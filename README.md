# agentic-bootstrap

A set of files, curated by myself, to bootstrap and agentic workflow.

## Workflow Overview

1. Create empty version control (git or jujutsu) repository
2. `run ./scripts/install.sh <target_dir>` to bootstrap agentic development.
3. Flesh out the `README.md` and add whatever specs you want.
4. Run the [initial-issue-seed](prompts/initial-issue-seed.md) to enqueue issues
   and start the loop.

## How to use

generally, I'd like to get to the point where I can just either:

1. Copy the required files over with some simple script
2. Have some default prompt where I point my agent here with an empty repo to pull all the right files in to get started.
