# geno-ws — Workspace Management

`geno-ws` manages development workspaces for the geno ecosystem. Creates workspaces from GitHub issues, JIRA tickets, repo names, or feature ideas, cloning repos into color-coded folders with metadata and agent rules.

## Skills

| Skill | Slash command | Purpose |
|-------|---------------|---------|
| geno-ws | — | Umbrella |
| geno-ws-init | /geno-ws-init | Create a new workspace |

## Repo structure

```
geno-ws/
├── GENO.md
├── SKILL.md -> skills/geno-ws/SKILL.md
├── genotools.yaml
└── skills/
    ├── geno-ws/SKILL.md
    └── geno-ws-init/SKILL.md
```

Previously lived in `geno-dev` as `geno-dev-workspaces-init`. Extracted because workspace management is infrastructure used across all skillsets.
