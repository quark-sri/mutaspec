# Intent: project config and CLI

Author: Srinivas. Status: draft. Part of [0000 mutaspec](../0000-mutaspec/intent.md).

## Problem
Every project keeps source code in different places and runs unit, integration, API and UI tests in different ways, often with services to start first. Today there is no single place to tell a mutation tool "change these files, run these suites", so each tool needs its own setup per language, and agents have to guess commands.

## Proposed outcome
One short, readable config file per project says what to change and how to run each test suite. A first command writes a working draft of it. Every other command reads it, checks it and explains errors plainly. People and agents call the same commands and can get machine-readable output.

## Affected users and systems
- Developers and agents setting up mutaspec on a project.
- The user's repository: one new config file and a `.mutaspec/` folder.
- A small example project in this repo, used as the reference for every later feature.

## Constraints
- Do not change anything else in the user's repository.
- Source and test paths must never overlap: test files are never changed.
- Requires git.

## Open questions
- Config also allowed inside `pyproject.toml`? Proposed: no, one file.
