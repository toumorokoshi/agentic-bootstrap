#!/usr/bin/env bash
# install.sh - copies the template files to the current directory
set -e
TARGET_DIR=${1}

if [ -z "${TARGET_DIR}" ]; then
  echo "Usage: $0 <target_directory>"
  exit 1
fi

ROOT_DIR="$(dirname "$(dirname "$(realpath "$0")")")"
TEMPLATE_DIR="${ROOT_DIR}/template"

rsync -avh --exclude=".gitignore" "${TEMPLATE_DIR}/" "${TARGET_DIR}/"