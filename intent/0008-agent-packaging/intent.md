# Intent: agent packaging

Author: Srinivas. Status: draft. Part of [0000 mutaspec](../0000-mutaspec/intent.md).

## Problem
The most useful parts (realistic bugs and test suggestions) need a coding agent, and teams use different agents. Without exact instructions, an agent guesses commands, writes tests the user did not ask for, or skips the clean-code check.

## Proposed outcome
Users install mutaspec's skills in their agent and say "check how good my tests are". The agent sets up the config, gets the clean run green, plants realistic bugs, runs the round, and writes suggestions, without editing tests. Claude Code users get it as one plugin; other agents use the same skills.

## Affected users and systems
- Users of Claude Code, Codex, Copilot, Cursor and similar agents.
- `skills/`, `.claude-plugin/`, optional subagents; a snippet for the user's own AGENTS.md / CLAUDE.md.

## Constraints
- No logic in skills; all logic in the CLI.
- Skills never edit test files.
- Paid agent runs only for skill behaviour changes.

## Open questions
- Ship an MCP server too? Proposed: not now.
