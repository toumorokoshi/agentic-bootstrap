# Orchestration Loop

The general idea of the loop is a do-while that picks off tasks of limited
context and delivers those.

This is more of less achieved with something like:

```
while there are open issues:
    pass the next ready issue's description to the agent
```

And this generally works fine.

## Using the best practice tools

I use [lelouch](https://github.com/toumorokoshi/lelouch) to handle orchestration.
