# Glossary

| Term | Meaning | _Avoid_ |
|---|---|---|
| **Baseline** | The clean code under test: a git ref (default `HEAD`) with no Mutant applied. | original, control |
| **Baseline result** | The outcome of running every Suite on the Baseline, `repeat` times: "ready" or "not ready", each Suite `ok` or `broken`, each test `pass`, `failing` or `flaky`, and durations. Stored in `.mutaspec/runs/baseline.json`. | baseline report, dry run |
| **Flaky test** | A test that both passes and fails on the same Baseline. Excluded from deciding Killed. | unstable test, random failure |
| **Mutant** | One injected bug: a small change to one line of a source file, never a test file. Shown as a diff. Has a stable id. | fault, defect, mutation (for the object) |
| **Mutant Set** | The Mutants that one run uses. In v0.1 it is picked again each run: the same Mutants for the same code and `--max`. | bug list |
| **Rule Mutant** | A Mutant made by a mutation operator (for example `<` to `<=`). | |
| **Agent Mutant** | A realistic Mutant written by a coding agent from the code and its spec. | LLM mutant, AI bug |
| **Operator** | A rule that turns code into a Rule Mutant. | mutator |
| **Suite** | One test command at one Level, with optional setup, start, ready, teardown. | test job |
| **Level** | The kind of Suite: `unit`, `integration`, `api`, `ui`, `other`. | layer, tier |
| **Round** | One run of all selected Mutants against the Suites, with a result per Mutant. | run (alone), iteration |
| **Killed** | At least one Suite failed with the Mutant where it passed on the Baseline. | detected |
| **Caught** | Killed or Timeout: what the Mutation Score counts. | |
| **Survived** | All Suites passed with the Mutant applied. | missed, lived |
| **Timeout** | A Suite took longer than its limit with the Mutant. Counts as Killed. | hang |
| **Invalid** | The Mutant does not apply, the build fails, or a Suite breaks for another reason (a service does not start). Not scored. | compile error |
| **Stale** | The Mutant no longer applies because the source changed. Not scored. | |
| **Equivalent** | A person decided the Mutant does not change behaviour. Not scored. | |
| **Mutation Score** | (Killed + Timeout) / (Killed + Timeout + Survived), overall or per Level. | coverage, kill rate |
| **Suggestion** | Advice from the agent for one Survived Mutant: what is not tested, which Level should test it, and a sketch of the check. | fix, patch |
| **Arid code** | Code where a Mutant is not useful (logging, metrics). Excluded. | |
