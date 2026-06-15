# CodeTruth Agent V3

**Engineering Intelligence Operating System** — an independent AI research
project. GPLv3.

V3 is built as a series of independent, frozen modules, each adding a
layer of deterministic, AI-model-free understanding of a software
repository. No network access, no modification of scanned repositories,
and every "I don't know" is logged explicitly rather than guessed.

## Modules

### [Module 1 — Repository Cognition Engine](module1/README.md)
Answers: **"What kind of repository is this?"**
Application type, primary framework, technology stack, entry points, and a
governance gate (APPROVED/BLOCKED) — validated across 69 real repositories,
100% discovery score, 0 crashes.

Source: `repository_cognition/` · Docs: [`docs/module1/`](docs/module1/)

### [Module 2 — Repository Graph Engine](module2/README.md)
Answers: **"How is the code inside it wired together?"**
Six structural graphs — functions, classes, modules, imports, dependencies,
and resolved call relationships — plus an honest unresolved-call log.
Validated across the same 69 repositories: 1,005,321 resolved calls,
0 crashes, 31/31 unit tests pass. Includes an early multi-language
extension scaffold (Java, JavaScript/TypeScript, C/C++).

Source: `repository_graph/` · Docs: [`docs/module2/`](docs/module2/)

## Project-Level Documentation

- [`docs/PROJECT_RECORD_v3.0.0-module2.md`](docs/PROJECT_RECORD_v3.0.0-module2.md) —
  full consolidated record: both modules' architecture, decisions,
  validation numbers, capability comparison, and documentation index.

## Status

| Module | Status |
|---|---|
| Module 1 — Repository Cognition | Complete, frozen (`v3.0.0-module1`) |
| Module 2 — Repository Graph (Python core) | Complete, frozen (`v3.0.0-module2`) |
| Module 2 — Multi-language scaffold | Validated baseline, not frozen |
| Module 3 | Planned next |

## License

GPLv3 — see repository root `LICENSE`.

## Author

Zeeshan Saud — Independent AI Researcher, UAE
github.com/Zeeshan78699/CodeTruthAgent
