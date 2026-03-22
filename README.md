# agentic-bootstrap

A set of files, curated by myself, to bootstrap and agentic workflow.

## Workflow Overview

1. Create empty version control (git or jujutsu) repository
2. initialize the repository for [beads](https://github.com/steveyegge/beads) and [lelouch](https://github.com/toumorokoshi/lelouch):
   1. `beads init --stealth`
   2. `lelouch init . --executor="gemini" --model="gemini-3-flash-preview"`
3. `run ./scripts/install.sh <target_dir>` to bootstrap agentic development.
4. Flesh out the `README.md` and add whatever specs you want.
5. Run the [initial-issue-seed](prompts/initial-issue-seed.md) to enqueue issues.
6. start the loop: `lelouch run -v`

## How to use

generally, I'd like to get to the point where I can just either:

1. Copy the required files over with some simple script
2. Have some default prompt where I point my agent here with an empty repo to pull all the right files in to get started.
