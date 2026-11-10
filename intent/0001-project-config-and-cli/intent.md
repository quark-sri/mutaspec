# Intent: project config and CLI

Author: Srinivas. Status: approved. Part of [0000 mutaspec](../0000-mutaspec/intent.md).

## Problem
Every project keeps source code in different places and runs unit, integration, API and UI tests in different ways, often with services to start first. Today there is no single place to tell a mutation tool "change these files, run these suites", so each tool needs its own setup per language, and agents have to guess commands.

## Proposed outcome
One short, readable config file per project says what to change and how to run each test suite, including any services a suite needs started first and stopped after. A first command writes a working draft of it. Every other command reads it, checks it and explains errors plainly. People and agents call the same commands and can get machine-readable output.

## Affected users and systems
- Developers and agents setting up mutaspec on a project.
- The user's repository: one new config file and a `.mutaspec/` folder. Temporary files in that folder are never picked up by git; files meant to be shared (such as the Mutant Set) can be committed.
- A small example project in this repo, used as the reference for every later feature.

## Constraints
- Do not change anything else in the user's repository.
- No file is both source and test: test files are never changed, even when they sit next to the source.
- Requires git.
- One config file, `mutaspec.toml`, for every language; not inside other tools' files such as `pyproject.toml` or `package.json`.

## Open questions
- None.
