#!/usr/bin/env python3
"""geno-ws — workspace initialisation for the geno ecosystem.

Usage:
  geno-ws init <track.domain.workspace> [options]

The dot-notation spec is the single spine:
  track.domain.workspace  →  ~/code/<track>/<domain>/<workspace>/

Steps performed by `init`:
  1. mkdir the workspace dir (via `tt new-project` if available, else directly)
  2. Clone each --repo into the workspace dir (or via SSH if --host given)
  3. Write <workspace>.code-workspace with all repos as folders
  4. Register the workspace node in ~/.geno/workspace.json
  5. Print the VS Code remote open command
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

_BOLD  = "\033[1m"
_DIM   = "\033[2m"
_GREEN = "\033[32m"
_RESET = "\033[0m"

# Track → title-bar color (matches geno-tt track tinting)
_TRACK_COLORS = {
    "crit":    {"bg": "#3a1a1a", "fg": "#e0a0a0", "bar": "#2e1414"},
    "explore": {"bg": "#1a2a3a", "fg": "#a0c0e0", "bar": "#14202e"},
    "chore":   {"bg": "#2a2a1a", "fg": "#d0d080", "bar": "#222214"},
    "side":    {"bg": "#1a1a3a", "fg": "#a0a0e0", "bar": "#141428"},
}
_DEFAULT_COLOR = {"bg": "#1a1a2a", "fg": "#a0a0c0", "bar": "#14141e"}


def _run(cmd: list[str], host: str | None = None, cwd: str | None = None) -> tuple[int, str]:
    if host:
        cwd_prefix = f"cd {cwd} && " if cwd else ""
        cmd = ["ssh", host, cwd_prefix + " ".join(cmd)]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd if not host else None)
    return r.returncode, (r.stdout + r.stderr).strip()


def _workspace_dir(spec: str, host: str | None = None) -> str:
    """Resolve the workspace directory path from a dot-notation spec."""
    parts = spec.split(".")
    if len(parts) < 3:
        raise SystemExit(f"Spec must be at least track.domain.workspace, got: {spec!r}")
    track, domain = parts[0], parts[1]
    workspace = ".".join(parts[2:])
    return f"{Path.home() if not host else '/home/' + os.environ.get('USER', 'user')}/code/{track}/{domain}/{workspace}/"


def _write_code_workspace(ws_dir: Path, spec: str, repos: list[str]) -> Path:
    track = spec.split(".")[0]
    colors = _TRACK_COLORS.get(track, _DEFAULT_COLOR)
    ws_name = spec.split(".", 2)[-1] if spec.count(".") >= 2 else spec
    folders = [{"name": Path(r).name, "path": Path(r).name} for r in repos]
    data = {
        "folders": folders,
        "settings": {
            "window.title": f"{spec} — ${{rootName}}",
            "workbench.colorCustomizations": {
                "titleBar.activeBackground": colors["bg"],
                "titleBar.activeForeground": colors["fg"],
                "activityBar.background":   colors["bar"],
                "statusBar.background":     colors["bg"],
                "statusBar.foreground":     colors["fg"],
            },
            "github.copilot.enable": {"*": False},
        },
    }
    out = ws_dir / f"{ws_name}.code-workspace"
    out.write_text(json.dumps(data, indent=2) + "\n")
    return out


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:]) if argv is None else list(argv)

    parser = argparse.ArgumentParser(prog="geno-ws")
    parser.add_argument("--version", action="version", version="geno-ws 0.2.0")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="initialise a workspace")
    p_init.add_argument("spec", help="dot-notation spec: track.domain.workspace (e.g. crit.rfhil.duc.2026.q2)")
    p_init.add_argument("--repo", action="append", default=[], metavar="URL",
                        help="git repo to clone into the workspace (repeatable)")
    p_init.add_argument("--host", default=None, help="SSH host to create workspace on")
    p_init.add_argument("--ticket", default=None, help="Jira ticket for context (e.g. NGAVPR-8494)")
    p_init.add_argument("--no-register", action="store_true",
                        help="skip registering in ~/.geno/workspace.json")

    args = parser.parse_args(argv)

    if args.cmd == "init":
        spec  = args.spec
        host  = args.host
        repos = args.repo

        parts = spec.split(".")
        if len(parts) < 3:
            raise SystemExit(f"Spec needs at least 3 parts (track.domain.workspace), got: {spec!r}")

        track, domain = parts[0], parts[1]
        workspace = ".".join(parts[2:])
        ws_path = Path.home() / "code" / track / domain / workspace

        # 1. mkdir (prefer tt new-project if available)
        if shutil.which("tt"):
            rc, out = _run(["tt", "new-project", spec] if not host
                           else ["ssh", host, f"tt new-project {spec}"])
            if rc != 0:
                print(f"{_DIM}tt new-project: {out} — falling back to mkdir{_RESET}")
        if host:
            _run(["mkdir", "-p", str(ws_path)], host=host)
        else:
            ws_path.mkdir(parents=True, exist_ok=True)
        print(f"{_GREEN}✓{_RESET} workspace dir: {ws_path}")

        # 2. Clone repos
        cloned = []
        for repo_url in repos:
            repo_name = repo_url.rstrip("/").split("/")[-1].removesuffix(".git")
            print(f"  cloning {repo_name}…", end="", flush=True)
            if host:
                rc, out = _run(["git", "clone", repo_url, repo_name], host=host,
                               cwd=str(ws_path))
            else:
                rc, out = _run(["git", "clone", repo_url, str(ws_path / repo_name)])
            if rc == 0:
                print(f" {_GREEN}ok{_RESET}")
                cloned.append(repo_name)
            else:
                print(f" {_DIM}failed: {out[:80]}{_RESET}")

        # 3. Write .code-workspace
        if not host:
            ws_file = _write_code_workspace(ws_path, spec, cloned or repos)
            print(f"{_GREEN}✓{_RESET} workspace file: {ws_file.name}")
            open_cmd = f"code {ws_file}"
            if host:
                open_cmd = f"code --remote ssh-remote+{host} {ws_file}"
            print(f"\n{_BOLD}open:{_RESET} {open_cmd}")
        else:
            print(f"{_DIM}(run geno-ws init without --host to write .code-workspace locally){_RESET}")

        # 4. Register in ~/.geno/workspace.json
        if not args.no_register and shutil.which("tt"):
            subprocess.run(["tt", "iterm", "reg", "pull"], capture_output=True)

        # 5. Ticket context hint
        if args.ticket:
            print(f"\n{_DIM}Tip: geno-tasks add {'.'.join(parts[:2]+[parts[2]])} --title {args.ticket}{_RESET}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
