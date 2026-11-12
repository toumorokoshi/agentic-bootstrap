## ALWAYS RUN

run the following, in order:

- study the README.md
- grep `specs/`, `design/`, and `human_specs/` for any relevant keywords to the task you are implementing.
- study the relevant files found.
- implement the change requested in the prompt.
- run linting and formatting before committing.
- Identify any remaining issues or features that need to be implemented. include them in tasks/
- summarize any major decisions or changes into DESIGN-DECISION-LOG.md. Include the date.
- commit and push the change. If the work was done in a work tree, merge without a merge commit, and delete the worktree unless the user says otherwise.

## Branch cleanup

When starting work, the branch should be clean, and you should try pull the
latest changes from the primary upstream branch before continuing.

## Add and update documentation

Always add and update documentation as appropriate. Update at least the following:

- any relevant files in the `docs/` directory.
- any updated designs and considerations in the `specs/` directory.
- do not update `human_specs/` unless told to explicitly - those are for humans.

## Issue Management

- Issues are tracked in individual files in tasks/, in markdown files with an issue description, and optionally a suggested fix where.

## Committing code

- **unless** the prompt contains "don't commit", commit the code.
- **unless** the prompt contains "don't push", push the code.

- Use the conventional commit format for commit messages.
- The commit description must explain the problem first.
- The commit description must a summary of each area modified.

## Commit and PR descriptions

- When writing commit or PR descriptions, use the `/yft-pr-commit-description`
  skill if available.

## Linting

- Always run linting and formatting before committing.
- Formatting and lint fixing tools are available via `just fix`.
- Linting tools are available via `just lint`.

## Testing

- linting, formatting, and testing **must** pass before a commit.
- add unit tests for every change if possible.

## CI

CI **must** pass after every commit.

To verify CI status, use the GitHub MCP server.

## Code Design

The following code tenants are followed:

- functional programming as much as possible.
- separate state from functional programming.
- re-use code as much as possible.
- leverage best-practice third party libraries.

## Examples

- example data is in the `examples/` directory.
