# Code Context

## Installation
```bash
pip install git+https://github.com/saltchicken/code_context
```
## Usage

Code Context

code_context is a command-line utility designed to capture and format a project's structure and file contents into a single, clean output. It's particularly useful for pasting a project's context into Large Language Models (LLMs) to provide them with a comprehensive understanding of the codebase.

The tool intelligently finds the project root, respects .gitignore rules, and allows for powerful, reusable filtering configurations through presets.

Features

    Automatic Project Root Detection: Finds your project's root by looking for a .git directory or a pyproject.toml file.

    Flexible Filtering: Uses .gitignore-style glob patterns to precisely include or exclude files and directories.

    .gitignore Aware: Automatically respects the exclusion rules defined in your project's .gitignore file.

    Project-Specific Presets: Define reusable configurations for your projects in a central presets.toml file for zero-argument execution.

    Clean, LLM-Ready Output: Generates a formatted output with a directory tree and file contents, ready to be used in prompts.

## Installation
```bash
pip install git+https://github.com/saltchicken/code_context
```

Usage

The tool can be run from anywhere inside a project directory.

Basic Usage with Presets

If you have a preset configured for your project (see Configuration below), you can simply run:
Bash

code_context

This will automatically use the preset matching your project's root folder name.

Command-Line Arguments

You can customize the output using command-line arguments. These arguments are combined with any active preset.

    --include: (Required if no preset is active) Patterns for files whose content you want to include.

    --exclude: Patterns for files or directories to completely exclude from both the tree and content.

    --include-in-tree: Patterns for files to show in the directory tree but without their content.

    --tree: Display only the directory tree structure, omitting all file contents.

    --preset: Manually specify which preset to use from your configuration file.

Examples

1. Include all Python files in src and the main pyproject.toml:
Bash

code_context --include "src/**/*.py" "pyproject.toml"

2. Include all Python files but exclude test files:
Bash

code_context --include "src/**/*.py" --exclude "**/test_*.py"

3. Show all Python files in the tree, but only include the content for files in the parse module:
Bash

code_context --include "src/code_context/parse.py" --include-in-tree "src/**/*.py"

4. Show just the directory tree for all non-test Python files:
Bash

code_context --include "src/**/*.py" --exclude "**/test_*.py" --tree

Configuration with Presets

Presets allow you to save and automatically apply configurations for your projects, making the tool much more convenient.

    Create a configuration file at: ~/.config/code_context/presets.toml

    Define your project configurations within this file using the project's root directory name as the key.

For example, if your project is located at /path/to/my-cool-project, the preset key would be [my-cool-project].

Example presets.toml:
Ini, TOML

# ~/.config/code_context/presets.toml

[my-cool-project]
# Patterns for files to include with their content
include = [
    "src/**/*.py",
    "README.md",
    "pyproject.toml"
]

# Patterns for files/directories to exclude entirely
exclude = [
    "dist/*",
    "*.log",
    ".venv/"
]

# Patterns for files to show in the tree but without content
include_in_tree = [
    "__init__.py"
]

[another-project]
include = [
    "app/**/*.js",
    "package.json"
]
exclude = [
    "node_modules/"
]

With this configuration, navigating into the my-cool-project directory and running code_context will automatically apply the specified rules without needing any command-line arguments.
