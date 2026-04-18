# Shared skills

Skills in this directory are loaded into **every** agent via `extra_skill_dirs` (see `orchestrator/launch.py`). Put things here that any of the four agents might legitimately need — e.g. how to read the shared roadmap, cascade etiquette, how to address the founder.

Per-domain playbooks belong in `workspaces/<role>/skills/`, not here.

## Conventions

Each skill is one markdown file with YAML frontmatter:

```markdown
---
name: my-skill
description: One line. The model reads this to decide whether to load the skill.
---

# My Skill

## When to use
Short, concrete trigger.

## Workflow
1. Step one
2. Step two
```

## TODO (starter backlog)

- [ ] `cascade-etiquette.md` — how to end a turn so the router can fan out cleanly (what to put in the outcome summary).
- [ ] `roadmap-reading.md` — where the roadmap lives, what its columns mean, how to reference an item.
- [ ] `founder-voice.md` — tone defaults for founder-facing replies.
