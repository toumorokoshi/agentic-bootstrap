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

If the prompt contains `please commit and push`, then commit and push the code.

- Use the conventional commit format for commit messages.

## Linting

- Always run linting and formatting before committing.
- Formatting and lint fixing tools are available via `just fix`.
- Linting tools are available via `just lint`.

## CI

To verify CI status, use the GitHub MCP server.
