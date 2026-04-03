# Agentic Best Practices

These are best practices that I've discovered, largely empirically.

Where possible, I will try to link to specific experiments I've run in the `experiments` directory.

**NOTE**: this guidance is designed to maximize success, even with relatively
low-functioning agents. Higher-functioning agents may still do very well without
any of this guidance. But following these practices ensures success with low-performing agents which are likely more cost-effective.

## Short checklist:

- always include "study AGENTS.md" in the prompt: this ensures that AGENTS.md will serve as a good point of reference.
- include a step-by-step workflow in AGENTS.md:

```
1. study the README.md
2. grep `specs/` for any relevant keywords to the task you are implementing.
3. study the relevant specs.
4. grep `design/` for any relevant keywords to the task you are implementing.
5. study the relevant documents.
6. implement the change requested in the prompt.
7. run linting and formatting before committing.
8. Identify any remaining issues or features that need to be implemented
   1. file them as bd issues (see [Issue Management](#issue-management)).
   2. include them in GAPS.md
9. commit and push the change.
```

- include links to AGENTS.md to other relevant files.
  - If most of your documentation is in a separate file, such as `README.md`, include "study README.md" as the first step.

- all lists should be numbered (avoids an agent not focusing on one of the items).
