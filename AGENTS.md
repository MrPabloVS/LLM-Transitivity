# Agent instructions

Read [CONSTITUTION.md](CONSTITUTION.md) before you change this project.
It defines the project conventions.

## Skills

- For domain terms, domain models, glossaries, or architecture decision records,
  read and use [domain-modeling](.agents/skills/domain-modeling/SKILL.md).
- Before you design a component or interface, refactor code, or review its design,
  read and use [design-principles](.agents/skills/design-principles/SKILL.md).

## Context

- Before you change module boundaries or dependencies, read
  [the architecture guide](docs/architecture.md).
- Before you change domain terms or their interpretation, read
  [GLOSSARY.md](GLOSSARY.md).
- Before you change pilot execution, input verification, or result archives, read
  [the pilot guide](docs/pilot.md).

## Tools and checks

Use `uv` to manage dependencies and run Python commands.
Read `pyproject.toml` and `.python-version` for the project requirements.
Use `uv sync --locked` to install the locked dependencies.

For code changes, run the checks that apply to the change:

```sh
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest
```

Review the diff and run `git diff --check` before you finish.
Report the checks you ran and their results. Distinguish failed checks, checks
you did not run, and checks that found no tests. Report existing failures as such.
