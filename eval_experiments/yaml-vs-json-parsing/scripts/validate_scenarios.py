"""
This script will check whether the scenarios are valid or not. For a given directory, this script checks the following:

1. Whether all yaml or json files are valid (they parse correctly).
"""
import os
import json
import yaml
import logging
import argparse

# Constants
SUPPORTED_YAML_EXTENSIONS = ('.yaml', '.yml')
SUPPORTED_JSON_EXTENSIONS = ('.json',)
CONTEXT_LINES = 5

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def format_error_snippet(content: str, lineno: int, context_lines: int = CONTEXT_LINES) -> str:
    """Formats a snippet of code around a given line number."""
    lines = content.splitlines()
    start = max(0, lineno - context_lines - 1)
    end = min(len(lines), lineno + context_lines)

    snippet = ["", "--- Potential Error Section ---"]
    for i in range(start, end):
        prefix = ">> " if i == lineno - 1 else "   "
        # Ensure we don't exceed line count
        if i < len(lines):
            snippet.append(f"{i + 1:4} | {prefix}{lines[i]}")
    snippet.append("--- End Section ---")
    return "\n".join(snippet)

def is_valid_json_content(content: str) -> tuple[bool, str | None]:
    """Validates if a content is a valid JSON."""
    try:
        json.loads(content)
        return True, None
    except json.JSONDecodeError as e:
        snippet = format_error_snippet(content, e.lineno)
        return False, f"{str(e)}\n{snippet}"

def is_valid_yaml_content(content: str) -> tuple[bool, str | None]:
    """Validates if a content is a valid YAML."""
    try:
        yaml.safe_load(content)
        return True, None
    except yaml.YAMLError as e:
        error_msg = str(e)
        if hasattr(e, 'problem_mark'):
            snippet = format_error_snippet(content, e.problem_mark.line + 1)
            error_msg = f"{error_msg}\n{snippet}"
        return False, error_msg

def is_valid_json(file_path: str) -> tuple[bool, str | None]:
    """Validates if a file is a valid JSON."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return is_valid_json_content(content)
    except OSError as e:
        return False, str(e)

def is_valid_yaml(file_path: str) -> tuple[bool, str | None]:
    """Validates if a file is a valid YAML."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return is_valid_yaml_content(content)
    except OSError as e:
        return False, str(e)

def validate_file(file_path: str) -> tuple[bool, str | None]:
    """Validates a single file based on its extension."""
    if file_path.endswith(SUPPORTED_JSON_EXTENSIONS):
        return is_valid_json(file_path)
    if file_path.endswith(SUPPORTED_YAML_EXTENSIONS):
        return is_valid_yaml(file_path)
    return True, None

def get_target_files(directory: str) -> list[str]:
    """Retrieves all target files (JSON/YAML) in a directory."""
    target_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(SUPPORTED_JSON_EXTENSIONS + SUPPORTED_YAML_EXTENSIONS):
                target_files.append(os.path.join(root, file))
    return target_files

def run_validation(directory: str) -> list[tuple[str, bool, str | None]]:
    """Runs validation on all relevant files in a directory."""
    files = get_target_files(directory)
    results = []
    for file_path in files:
        is_valid, error = validate_file(file_path)
        results.append((file_path, is_valid, error))
        if not is_valid:
            logger.error(f"Invalid file: {file_path} - {error}")
    return results

def main():
    parser = argparse.ArgumentParser(description="Validate structured data files in scenarios.")
    parser.add_argument("directory", help="Path to the scenario directory to validate.")
    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        logger.error(f"Error: Directory '{args.directory}' does not exist.")
        exit(1)

    logger.info(f"Validating scenarios in: {args.directory}")
    results = run_validation(args.directory)
    
    invalid_count = sum(1 for _, valid, _ in results if not valid)
    if invalid_count > 0:
        logger.error(f"Finished with {invalid_count} errors.")
        exit(1)
    
    logger.info("All scenarios are valid.")

if __name__ == "__main__":
    main()