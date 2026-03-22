## ALWAYS RUN

- study the README.md

## Add and update documentation

Always add and update documentation as appropriate. Update at least the following:

- any relevant files in the `docs/` directory.
- any updated designs and considerations in the `specs/` directory.

## Issue Management

File issues liberally to help keep context minimal and focus on your current
task.

- Issues are managed via the `bd` commmand line.
- Issues are created via `bd create`
  - Priority should be set to the following (P2 otherwise):
    - P0: Any required project fundamentals or initialization

## Committing code

- **unless** the prompt contains "don't commit", commit the code.
- **unless** the prompt contains "don't push", push the code.

- Use the conventional commit format for commit messages.
- The commit description must explain the problem first.
- The commit description must a summary of each area modified.

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
