#!/usr/bin/env bash
# install.sh - copies the template files to the current directory
set -e

ROOT_DIR="$(dirname "$(dirname "$(realpath "$0")")")"
TEMPLATE_DIR="${ROOT_DIR}/template"

rsync -avh --exclude=".gitignore" "${TEMPLATE_DIR}/" "./"