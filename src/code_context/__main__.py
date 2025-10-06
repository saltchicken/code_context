import argparse
import pyperclip
import sys
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
            print(f"⚠️ Warning: Could not parse user presets at {user_config_path}: {e}", file=sys.stderr)
    else:
        print(f"⚠️ Warning: User presets not found at {user_config_path}", file=sys.stderr)

    return {}

def main() -> None:
    """
    Main function for the command-line interface.
    
    Parses arguments to determine what context to gather and how to output it.
    """
    presets = load_presets()
    preset_names = list(presets.keys())

    parser = argparse.ArgumentParser(
        description="""Gather and display a codebase context, useful for LLMs.
        By default, it shows the directory tree and content of included files."""
    )
    
    # --- General Action Arguments ---
    parser.add_argument("--preset", choices=preset_names, help="Use a predefined set of options from presets.toml.")
    parser.add_argument("--tree", action="store_true", help="Show only the directory tree structure.")
    parser.add_argument("--copy", action="store_true", help="Copy the output to the clipboard instead of printing.")

    # --- Filtering Arguments ---
    filter_group = parser.add_argument_group('Filtering Options (gitignore-style patterns)')
    filter_group.add_argument("--include", nargs="+", default=[], dest="include",
                              help="Patterns for files to include for content (e.g., 'src/**/*.py', '*.md').")
    filter_group.add_argument("--include-in-tree", nargs="+", default=[], dest="include_in_tree",
                              help="Patterns for files to show in the tree but without their content (e.g., '__init__.py').")
    filter_group.add_argument("--exclude", nargs="+", default=[], dest="exclude",
                              help="Patterns for files or directories to exclude (e.g., 'dist/*', '*.log').")

    # --- Preset and Argument Merging ---
    # First pass to find the preset
    args, _ = parser.parse_known_args()
    project_root = find_project_root(Path.cwd())

    # Auto-select preset if project directory name matches a preset name
    if not args.preset and project_root and project_root.name in presets:
        print(f"✅ Found matching preset '{project_root.name}' for the project directory.")
        args.preset = project_root.name

    # Set preset defaults if one is selected
    if args.preset:
        preset_values = presets.get(args.preset, {})
        parser.set_defaults(**preset_values)

    # Final parse to get the combined arguments
    args = parser.parse_args()
    
    # Manually merge list-based arguments from preset and command-line
    final_args = {"include": [], "exclude": [], "include_in_tree": []}
    if args.preset:
        preset_values = presets.get(args.preset, {})
        for key in final_args:
            final_args[key].extend(preset_values.get(key, []))

    # Add command-line arguments, which take precedence if provided
    raw_args = sys.argv[1:]
    if "--include" in raw_args:
        final_args["include"] = args.include
    else:
        final_args["include"].extend(args.include)

    if "--exclude" in raw_args:
        final_args["exclude"] = args.exclude
    else:
        final_args["exclude"].extend(args.exclude)
        
    if "--include-in-tree" in raw_args:
        final_args["include_in_tree"] = args.include_in_tree
    else:
        final_args["include_in_tree"].extend(args.include_in_tree)

    # --- Validation ---
    if not final_args["include"]:
        if project_root and project_root.name not in presets:
            tip = (
                f"\n💡 Tip: No automatic preset found for '{project_root.name}'.\n"
                f"  To run `code_context` without arguments here, create a preset named "
                f"'[{project_root.name}]' in:\n  {Path.home() / '.config' / 'code_context' / 'presets.toml'}"
            )
            print(tip, file=sys.stderr)
        parser.error("At least one --include value must be provided, either directly or via a preset.")
    
    if project_root is None:
        print("❌ Error: Not inside a recognized project directory (.git or pyproject.toml not found).")
        sys.exit(1)
    
    start_path = str(project_root)

    context = CodeContext(
        start_path=start_path,
        include=list(dict.fromkeys(final_args["include"])),
        exclude=list(dict.fromkeys(final_args["exclude"])),
        include_in_tree=list(dict.fromkeys(final_args["include_in_tree"])),
    )
    
    # --- Output Generation ---
    if args.tree:
        final_output = context.get_directory_tree_string()
    else:
        final_output = context.get_full_context()

    if args.copy:
        pyperclip.copy(final_output)
        print("✅ Context copied to clipboard.")
    else:
        if final_output:
            print(final_output)
        else:
            print("No content found for the specified criteria.")

if __name__ == "__main__":
    main()
