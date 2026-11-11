# Research notes (2026-11-09)

## Existing tools

| Tool | Languages | How bugs are made | Test command | Fit for mutaspec |
|---|---|---|---|---|
| Stryker (JS/TS, C#, Scala) | 3 | AST operators, in memory | Own runners; JS has a command runner | Report schema to reuse; unit only |
| PIT | Java/JVM | Bytecode | JUnit/TestNG | Unit only |
| mutmut | Python | AST | pytest | Unit only |
| cargo-mutants | Rust | AST | cargo test | Unit only |
| Mull | C/C++ | LLVM IR | Compiled tests; git-diff mode | Diff-scoping idea |
| [universalmutator](https://github.com/agroce/universalmutator) | Many (regex rules, optional comby) | Text rewrite of lines; TCE dedup | Any shell command | Possible Rule Mutant source for languages we do not support yet (v0.3+). Licence: LICENSE file is Apache-2.0, `setup.py` says MIT; owner accepted it as Apache-2.0 on 2026-11-10 |
| [Mutahunter](https://scribe.disroot.org/post/493360) | Any (tree-sitter + LLM) | LLM | Any command | Agent Mutant idea; no Levels, no Rounds |
| [LLMorpheus](https://github.com/githubnext/llmorpheus) | JS/TS | LLM fills placeholders | npm test | Archived; moved to neu-se |
| [MAEWU](https://people.ece.ubc.ca/amesbah/resources/papers/icsme21.pdf) | Web UI | DOM changes in browser | E2E tests | UI-level idea; research prototype |
| Agent skills ([agentic-qe](https://skillselion.com/skills/proffesor-for-testing/agentic-qe/mutation-testing), [lisa](https://agent-skills.md/skills/codyswanngt/lisa/mutation-testing), [mutation-tester](https://www.claudepluginhub.com/plugins/rohitg00-mutation-tester-plugins-mutation-tester)) | Varies | Mostly wrap Stryker/mutmut | Unit | Not verified; most write tests for the user |

**Gap:** no open tool runs the same bugs against unit, integration, API and UI Suites with a trusted Baseline, scores per Level, and keeps a frozen Mutant Set across Rounds.

## Literature that shapes the design

- **DeMillo, Lipton, Sayward (1978)** — competent programmer hypothesis and coupling effect: small bugs stand in for real ones.
- **Offutt et al. (1996)** — selective mutation: a few operators (ABS, AOR, LCR, ROR, UOI) give almost the same result as all. → Start with a small operator set.
- **Jia & Harman (2011)**, **Papadakis et al. (2019)** — surveys: equivalent Mutants, cost reduction (sampling, schemata, selective), subsumption.
- **Just et al. (FSE 2014)** — Mutation Score correlates with real-fault detection, beyond coverage. → The score is worth having.
- **Trivial Compiler Equivalence (Papadakis et al. 2015)** — compile and compare binaries to drop equivalent/duplicate Mutants cheaply.
- **Google: State of Mutation Testing (ICSE-SEIP 2018), [Practical Mutation Testing at Scale (TSE 2021)](https://arxiv.org/abs/2102.11378)** — diff-scoped, covered lines only, arid-node filter, one Mutant per line, show few Survived Mutants in code review. → Intent 0005.
- **[Meta ACH (FSE 2025)](https://arxiv.org/abs/2501.12862)** — LLM writes few, realistic, concern-specific Mutants; LLM equivalence agent (precision 0.95 / recall 0.96 after preprocessing); 73% of generated tests accepted. → Agent Mutants and equivalence flagging.
- **[Tian et al. (ISSTA 2024)](https://arxiv.org/abs/2408.01760)**, **Wang et al. (TOSEM 2025, [arXiv 2406.09843](https://arxiv.org/abs/2406.09843))** — LLMs detect equivalent Mutants and write more realistic Mutants than rules, but more are invalid. → Validate every Agent Mutant.
- **[Stryker incremental mode](https://stryker-mutator.io/docs/stryker-js/incremental/)** and the [mutation-testing-elements schema](https://socket.dev/npm/package/mutation-testing-report-schema/overview/3.5.1) — shared JSON format and HTML viewer. → Our JSON report.
