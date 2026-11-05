# Project constitution

This document defines the shared conventions for this project.
Apply them to new work and to the parts of existing work that you change.
Project conventions take priority over guidance in installed skills.

## Language

Use ASD-STE100 Simplified Technical English for new documentation, code comments,
and commit messages. Write short, direct sentences. Use active voice and one
consistent term for each concept. Keep technical names and identifiers exact.
Define technical terms when the reader needs them.

Use Spanish in conversations with the user.
Preserve the original content of benchmark prompts, model responses, and
historical data. Language rules do not authorize changes to research evidence.
Keep installed third-party skills in their original form.

## Commits

Use Conventional Commits with a required scope:

```text
type(scope): description
```

Choose a scope that names the part of the project that changed.
For example: `docs(governance): define project conventions`.
For a breaking change, use `type(scope)!: description` and explain the change
in the commit body.

Make each commit atomic: one logical change that can be reviewed and reverted
on its own. Include the tests and documentation needed for that change.
Keep unrelated changes in separate commits. Keep behavior changes separate
from refactoring when they can stand on their own.
Review the staged diff and run the relevant checks before each commit.

## Design and domain terms

Use the installed domain-modeling skill to establish and maintain domain terms.
Use the installed design-principles skill to guide component and interface design.
Keep each project rule in one authoritative place. Reference that rule from other
documents instead of repeating it.
