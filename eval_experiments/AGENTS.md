# Agent instructions for running evals

1. Use the evaluation methodology outlined in the [skill-creator skill](.agents/skill/skill-creator/SKILL.md).
2. Always put results of the eval in `eval_results/{experiment_name}`.
3. Always copy the contents of the scenario into a new directory and run the
   agent there. This ensures the repository will not get polluted.
4. The evals.yaml format uses a modified version of the standard evals.yaml. Instead, the `expected_output` is a json array with multiple expected outputs to make assertions easier to read.
5. At the end of the evals, read the README.md of the experiment directory and
   update any results.

## Evals Format

The evals.json uses the following format:

```json
{
  "skill_name": "<skill_name>",
  "evals": [
    {
      "id": "1",
      "prompt": "{the prompt}",
      "expected_output": [
        "1. The output file exists in the scenario directory.",
        "2. The description of GET /users/{userId} is exactly: \"Retrieves a single user by their unique identifier.",
        "3. The `email` field in the User schema has format `email`.",
        "4. The `age` field in the User schema has type `number` (not `integer`).",
        "5. The `createdAt` field is present in the User schema with type `string` and format `date-time`.",
        "6. The `createdAt` field is listed as required in the User schema.",
        "7. The `limit` query parameter description on GET /users is exactly: \"Maximum number of users to return per page.\""
      ],
      "files": []
    },
}
```
