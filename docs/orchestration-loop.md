# Orchestration Loop

The general idea of the loop is a do-while that picks off tasks of limited
context and delivers those.

This is more of less achieved with something like:

```bash
while [ `bd read --json` -ne "[]" ]; do
 bd ready --json -n 1 | jq ".[0].description" | gemini --yolo
end
```

And this generally works fine.

## Using the best practice tools

I use [beads]() and [lelouch]() in concert to handle the issue management queue
and orchestration, respectively.
