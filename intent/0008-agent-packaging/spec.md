# Spec: agent packaging (from intent.md)

Status: pre-draft. Intent: [intent.md](intent.md)

## User scenarios and acceptance

### S1 Right skill at the right time (P1)
- **AC1** Each skill's description triggers on its task and not on unrelated testing tasks (trigger eval: ≥ 10 positive and ≥ 10 negative prompts per skill).
- **AC4** In a fresh Claude Code project with the plugin, "check how good my tests are" leads to `mutaspec-setup` then `mutaspec-round`.

### S2 Skills match the CLI (P1)
- **AC2** Skills call only `mutaspec` commands with `--json` and documented flags; a test parses every command in skill text and checks it exists.

### S3 Safe tools (P1)
- **AC3** The `survivor-analyst` subagent has no write access outside `.mutaspec/runs/`.

### S4 Portable (P2)
- **AC5** The same skill text works in at least one other agent (Codex or Copilot CLI) unchanged.

## Edge cases
- `mutaspec` not installed: the skill says how to install it and stops.

## Functional requirements
- **FR1** Skills: `mutaspec-setup`, `mutaspec-inject` (write Agent Mutants with `category`, `why_realistic`, `spec_ref`), `mutaspec-round`, `mutaspec-suggest`.
- **FR2** Claude Code plugin: the skills, subagents `mutant-writer` and `survivor-analyst`, commands `/mutaspec-round`, `/mutaspec-suggest`.
- **FR3** `docs/agents-snippet.md` for users' AGENTS.md / CLAUDE.md.

## Key entities
Agent Mutant, Suggestion.

## Success criteria
- **SC1** End to end on `examples/shop` from a fresh agent session: setup → inject → round → suggest, with no human command typed.

## Out of scope
MCP server.

## Needs clarification
- none
