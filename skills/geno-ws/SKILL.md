---
name: geno-ws
description: >-
  DEPRECATED — superseded by geno-tt (the `tt` CLI). Legacy color-folder
  workspace management. Use `tt new-project` / `tt ecosystem-clone` /
  `tt overlay` / `tt migrate` instead. Retained only for migration.
  Use when user says /geno-ws or /geno-ws-init.
license: MIT
metadata:
  author: 42euge
  version: "0.2.0"
  deprecated: true
  superseded_by: geno-tt
---

# geno-ws

> **⚠️ DEPRECATED — superseded by [geno-tt](https://github.com/42euge/geno-tt).**
> Workspace management now lives in the `tt` CLI under the code-org scheme
> (`~/code/<track>/<domain>/<workspace>.<born>/<repo>`). Use
> `tt new-project`, `tt ecosystem-clone`, `tt overlay`, and `tt migrate`
> (skills `geno-tt-workspaces-*`). `geno-ws` is retained only for migration.

Workspace management for the geno ecosystem.

| Skill | Slash command | Purpose |
|-------|---------------|---------|
| geno-ws-init | /geno-ws-init | *(deprecated)* Create color-folder workspaces — use `tt new-project` |
