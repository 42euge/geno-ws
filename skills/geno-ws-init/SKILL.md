---
name: geno-ws-init
description: >-
  Create development workspaces from GitHub issues, JIRA tickets, repo names, or feature ideas.
  Clone repos into color-coded folders with metadata and agent rules.
  Use when user says /geno-ws-init.
argument-hint: "[config|list|<freeform text>]"
license: MIT
metadata:
  author: 42euge
  version: "0.1.0"
---

# Create Workspace

Create isolated development workspaces by cloning repos into the user's preferred code space. Accepts freeform input — the skill infers whether it's a GitHub issue, JIRA ticket, repo names, or a feature idea.

## Input

`$ARGUMENTS` is either a utility subcommand (`config`, `list`) or freeform text describing what to work on.

## Zero Footprint Policy

This skill never modifies a project's tracked files. All geno artifacts (`.geno/`, `CLAUDE.local.md`) live in the workspace directory, which is outside any repo's working tree.

## Config System

Workspace settings live at `~/.geno/config.yaml`. Auto-created on first use if missing.

```yaml
workspaces:
  mode: color                # code space method — determines folder strategy
  base_path: "~"
  color:                     # settings for mode: color
    default: code-purp
    folders:
      - code-red
      - code-blue
      - code-purp
      - code-indigo
```

The `mode` field selects the code space method. Currently supported: `color`. Future modes (e.g., `flat`, `project`, `date`) can be added by defining a new key under `workspaces` with their own settings.

## Naming Convention

Workspace directory names encode the source and context:

| Source | Format | Example |
|---|---|---|
| GitHub issue | `GH-{repo}-{number}-{slug}-ws` | `GH-geno-dev-42-fix-auth-token-ws` |
| JIRA ticket | `{PROJECT-NUMBER}-{slug}-ws` | `PROJ-1234-migrate-db-schema-ws` |
| Repos / Idea | `{slug}-ws` | `voice-coding-assist-ws` |

Slug rules: AI-generated, 5–15 characters, 3–4 hyphenated words. Must be filesystem-safe (lowercase, hyphens only).

## Workflow

### 1. Load config

- Read `~/.geno/config.yaml`.
- If the file does not exist, create it with the defaults shown above.
- Read `mode` to determine the folder strategy.
- For `color` mode: read `default` folder and `folders` list.

### 2. Parse input and infer intent

If `$ARGUMENTS` starts with `config` or `list`, route to that subcommand (see below) and stop.

If `$ARGUMENTS` is empty, use `AskUserQuestion` to ask "What are you working on?" with a freeform text option.

Otherwise, infer the mode from the freeform text:

1. **Contains a `github.com` URL** (e.g., `https://github.com/42euge/geno-dev/issues/42`)
   → **GitHub issue mode**. Extract owner, repo name, and issue number from the URL.

2. **Matches `[A-Z]+-\d+` pattern** (e.g., `PROJ-1234`, `TEAM-56`)
   → **JIRA ticket mode**. The matched string is the ticket ID.

3. **Looks like repo names** (words that match known geno-ecosystem repo names, or `owner/repo` patterns, or GitHub URLs without issue paths)
   → **Repos mode**. Each word/URL is a repo to clone.

4. **Anything else** (natural language description)
   → **Idea mode**. Treat the text as a feature description.

5. **Ambiguous** (could be repo names or a description)
   → Use `AskUserQuestion` to clarify: "Did you mean repos to clone, or a feature description?" with options for each.

### 3. Resolve repos

#### GitHub issue mode

1. Run `gh issue view <url> --json title,body,labels,assignees` to fetch issue details.
2. The repo from the URL is the primary repo — always included.
3. Scan the issue body for references to other repos (look for `github.com/42euge/geno-*` URLs or `geno-*` mentions).
4. If additional repos are found, suggest them via `AskUserQuestion` (multi-select: "Include these related repos?").
5. Generate the slug from the issue title (3–4 hyphenated words, 5–15 chars).
6. Workspace name: `GH-{repo}-{number}-{slug}-ws`

#### JIRA ticket mode

1. No API call — the ticket ID is used for naming only.
2. Since JIRA tickets don't imply a repo, prompt the user to select repos.
3. Scan the geno-ecosystem repos directory. For each repo, read its `.geno-agents` file to get role, description, and capabilities.
4. Present repos via `AskUserQuestion` with multi-select. Each option shows the repo name and its description from `.geno-agents`.
5. Ask for a short description (or use any additional text from `$ARGUMENTS` after the ticket ID) to generate the slug.
6. Workspace name: `{TICKET-ID}-{slug}-ws`

#### Repos mode

1. For each repo argument:
   - If it's a full URL → use as-is
   - If it's `owner/repo` → expand to `https://github.com/{owner}/{repo}`
   - If it's a bare name → expand to `https://github.com/42euge/{name}`
2. Validate each with `gh repo view <repo> --json name,url 2>/dev/null`. If validation fails, warn the user and ask to continue or fix.
3. Generate the slug from the repo names or ask the user for one.
4. Workspace name: `{slug}-ws`

#### Idea mode

1. Read `.geno-agents` from every repo directory under the geno-ecosystem path:
   `/Users/euge/Library/Mobile Documents/iCloud~md~obsidian/Documents/Everything/research/kaggle/gemma-4-good-hackathon/geno-ecosystem/repos/`
   For each, extract: role, description, capabilities.
2. Also run `gh repo list 42euge --limit 50 --json name,description` to discover repos not in the local ecosystem directory.
3. Analyze the idea description against repo descriptions and capabilities. Rank by relevance.
4. Present the top 3–5 suggested repos via `AskUserQuestion` with multi-select. Each option shows the repo name and why it's relevant.
5. Generate the slug from the idea description.
6. Workspace name: `{slug}-ws`

### 4. Confirm with user

Use `AskUserQuestion` to present the workspace plan:
- Workspace name (the generated directory name)
- Color folder (the default from config, e.g., `~/code-purp/`)
- Repos to clone (with URLs)

Options:
- "Create" — proceed
- "Change color" — show available color folders as options
- "Change name" — accept freeform text for a custom name

### 5. Create workspace

For `color` mode:

```bash
# Ensure color folder exists
mkdir -p ~/<color>/

# Create workspace structure
mkdir -p ~/<color>/<workspace-name>/.geno

# Clone each repo
git clone <url-1> ~/<color>/<workspace-name>/<repo-1>
git clone <url-2> ~/<color>/<workspace-name>/<repo-2>
```

Write `.geno/workspace.yaml`:

```yaml
ticket: GH-geno-dev-42     # or PROJ-1234, or null
slug: fix-auth-token
status: active
repos:
  - url: https://github.com/42euge/geno-dev
    path: geno-dev
  - url: https://github.com/42euge/geno-tools
    path: geno-tools
color: code-purp
created: 2026-04-25T12:00:00Z
source: issue               # issue | repos | idea
source_ref: https://github.com/42euge/geno-dev/issues/42
```

Write `CLAUDE.local.md` at the workspace root:

```markdown
# Workspace: <workspace-name>

<Ticket/description context>
Repos: <repo-1>, <repo-2>

## Agent Rules
- Do not commit `.geno/` or `CLAUDE.local.md` in any repo in this workspace.
- When staging files, always exclude `.geno/` and `CLAUDE.local.md`.
- Worktrees for repos in this workspace live at `../.geno/worktrees/<repo>/<branch>/`.
```

### 6. Report

Tell the user:
- Workspace created at `~/<color>/<workspace-name>/`
- Repos cloned: list each with its path
- Next steps: `cd ~/<color>/<workspace-name>/<repo>/` to start working
- Mention: `/geno-dev-worktrees-manage` is workspace-aware and will put worktrees in `.geno/worktrees/`

---

## Subcommand: config

Manage workspace configuration at `~/.geno/config.yaml`.

- `config` (no args) → display current mode and settings
- `config mode <mode>` → switch code space method
- For `color` mode:
  - `config default <color>` → set the default color folder
  - `config add <color>` → add a new color to the folders list
  - `config remove <color>` → remove a color (with `AskUserQuestion` confirmation)

Read the file, modify the relevant field, write it back. Use YAML formatting.

---

## Subcommand: list

List all workspaces across all configured color folders.

1. Read `~/.geno/config.yaml` to get the folders list (for `color` mode).
2. For each color folder, scan for directories ending in `-ws` or `-WS` (case-insensitive).
3. For each match:
   - If `.geno/workspace.yaml` exists → parse metadata (ticket, repos, status, date, source)
   - If directory ends in `-WS` (uppercase) and no `workspace.yaml` → tag as `[legacy]`
   - If directory ends in `-ws` (lowercase) and no `workspace.yaml` → tag as `[unmanaged]`
4. Display as a table:

| Workspace | Color | Ticket | Repos | Status | Created | Tags |
|---|---|---|---|---|---|---|
| `GH-geno-dev-42-fix-auth-ws` | code-purp | GH-geno-dev-42 | geno-dev, geno-tools | active | 2026-04-25 | |
| `geno-dev-WS` | code-purp | — | — | — | — | [legacy] |
| `lottie-creator-ws` | code-purp | — | — | — | — | [unmanaged] |

Sort: active workspaces first, then by creation date (newest first). Legacy and unmanaged at the end.
