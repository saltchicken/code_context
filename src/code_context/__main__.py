import argparse
import sys
import logging
from pathlib import Path
from code_context.parse import CodeContext

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


def find_project_root(path: Path) -> Path | None:
    """
    Traverses up from the starting path to find a directory containing
    a .git folder or a pyproject.toml file.
    """
    current_path = path.resolve()
    while True:
        if (current_path / ".git").is_dir() or (current_path / "pyproject.toml").is_file():
            return current_path
        if current_path.parent == current_path:  # Reached the filesystem root
            return None
        current_path = current_path.parent


def load_presets() -> dict:
    """
    Loads presets from the user's configuration file at ~/.config/code_context/presets.toml.
    """
    user_config_path = Path.home() / ".config" / "code_context" / "presets.toml"
    if user_config_path.is_file():
        try:
            presets_text = user_config_path.read_text(encoding='utf-8')
            return tomllib.loads(presets_text)
        except Exception as e:
            logging.warning(f"⚠️ Could not parse user presets at {user_config_path}: {e}")
    else:
        logging.warning(f"⚠️ User presets not found at {user_config_path}")
    return {}


def main() -> None:
    """
    Main function for the command-line interface.

    Parses arguments to determine what context to gather and how to output it.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",  # Keep the output clean, as messages have their own indicators
        stream=sys.stderr,
    )

    presets = load_presets()
    preset_names = list(presets.keys())
    parser = argparse.ArgumentParser(
        description="""Gather and display a codebase context, useful for LLMs.
        By default, it shows the directory tree and content of included files."""
    )

    # --- General Action Arguments ---
    parser.add_argument("--preset", choices=preset_names, help="Use a predefined set of options from presets.toml.")
    parser.add_argument("--tree", action="store_true", help="Show only the directory tree structure.")

    # --- Filtering Arguments ---
    filter_group = parser.add_argument_group('Filtering Options (gitignore-style patterns)')
    filter_group.add_argument("--include", nargs="+", default=[],
                              help="Patterns for files to include for content (e.g., 'src/**/*.py', '*.md').")
    filter_group.add_argument("--include-in-tree", nargs="+", default=[],
                              help="Patterns for files to show in the tree but without their content (e.g., '__init__.py').")
    filter_group.add_argument("--exclude", nargs="+", default=[],
                              help="Patterns for files or directories to exclude (e.g., 'dist/*', '*.log').")

    # --- Preset and Argument Merging ---
    args = parser.parse_args()
    project_root = find_project_root(Path.cwd())

    # Determine which preset to use (CLI > auto-detect)
    preset_key = args.preset
    if not preset_key and project_root and project_root.name in presets:
        preset_key = project_root.name

    preset_values = presets.get(preset_key, {}) if preset_key else {}
    # Combine preset and command-line arguments, then remove duplicates
    final_include = list(dict.fromkeys(preset_values.get('include', []) + args.include))
    final_exclude = list(dict.fromkeys(preset_values.get('exclude', []) + args.exclude))
    final_include_in_tree = list(dict.fromkeys(preset_values.get('include_in_tree', []) + args.include_in_tree))

    # --- Validation ---
    if not final_include:
        if project_root and project_root.name not in presets:
            tip = (
                f"\n💡 Tip: No automatic preset found for '{project_root.name}'.\n"
                f"  To run `code_context` without arguments here, create a preset named "
                f"'[{project_root.name}]' in:\n  {Path.home() / '.config' / 'code_context' / 'presets.toml'}"
            )
            logging.info(tip)
        parser.error("At least one --include value must be provided, either directly or via a preset.")
        sys.exit(1)

    if project_root is None:
        logging.error("❌ Error: Not inside a recognized project directory (.git or pyproject.toml not found).")
        sys.exit(1)

    start_path = str(project_root)
    context = CodeContext(
        start_path=start_path,
        include=final_include,
        exclude=final_exclude,
        include_in_tree=final_include_in_tree,
    )

    # --- Output Generation ---
    if args.tree:
        final_output = context.get_directory_tree_string()
    else:
        final_output = context.get_full_context()

    if final_output:
        print(final_output)  # This is the only print to stdout
    else:
        logging.warning("⚠️ No content found for the specified criteria.")
        sys.exit(1)


if __name__ == "__main__":
    main()
