# Initial Issue Seed

## Description

This is used to seed the initial project issues that start the loop.

_note_: use a deep thinking agent here. This will ensure that the prompts are
more descriptive. A weaker agent can be used to implement the individual,
modular tasks.

## Content

1. study README.md
2. enqueue the following tasks with `bd create`, as a P0:
   - P0: implement basic build scaffolding.
   - P1: implement `just lint` and `just fix`.
   - P1: implement CI.
3. study each specification in the specs/ directory.
4. look at code that's already implemented.
5. generate a list of tasks to perform, and create work items for them via `bd`. Include the following in the issue:
   - the prefix "study README.md"
   - any relevant parts of the spec to follow.
   - the suffix "Check the production deployment to see where the gaps are. Create any additional issues as needed."
   - these issues should be blocked on the creation of the CI, scaffolding and just lint issues.
