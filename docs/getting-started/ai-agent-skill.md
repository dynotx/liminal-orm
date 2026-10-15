# AI Agent Skill

Liminal provides an SKILL.md file that instructs AI agents how to safely manage Benchling schemas and run Benchling migrations with the Liminal CLI. The skill gives AI agents a safe workflow for managing Benchling schemas with Liminal. It guides agents to identify and propagate schema changes throughout the codebase, inspect differences with `liminal diff`, and generate a revision file for review. The skill requires explicit human approval before every change to a Benchling tenant.


## Download

Download [SKILL.md](https://raw.githubusercontent.com/dynotx/liminal-orm/main/skills/liminal/SKILL.md), then copy it into your repository at the following locations:

## Codex

Copy the downloaded file into your repository at:

```text
.agents/skills/liminal/SKILL.md
```

## Cursor

Copy the downloaded file into your repository at:

```text
.cursor/skills/liminal/SKILL.md
```

## Claude Code

Copy the downloaded file into your repository at:

```text
.claude/skills/liminal/SKILL.md
```

## Review

Review the downloaded `SKILL.md` before using it, especially if you customize the approval process for your organization.
