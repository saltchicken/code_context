import argparse
import pyperclip
import tempfile
import shutil
import sys
import importlib.resources
from pathlib import Path
from git import Repo, GitCommandError
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
    Loads the built-in presets from the packaged `default_presets.toml` file.
    """
    try:
        files = importlib.resources.files('code_context')
        presets_text = files.joinpath('default_presets.toml').read_text(encoding='utf-8')
        return tomllib.loads(presets_text)
    except (FileNotFoundError, ModuleNotFoundError):
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
    parser.add_argument("--repo", help="URL of a Git repository to clone and analyze.", type=str)
    parser.add_argument("--preset", choices=preset_names, help="Use a predefined set of options.")
    parser.add_argument("--tree", action="store_true", help="Show only the directory tree structure.")
    parser.add_argument("--copy", action="store_true", help="Copy the output to the clipboard instead of printing.")

    # --- Inclusion Arguments ---
    inc_group = parser.add_argument_group('Inclusion Options')
    inc_group.add_argument("--include-extensions", nargs="+", default=[], help="File extensions to include for content (e.g., py js).")
    inc_group.add_argument("--include-files", nargs="+", default=[], help="Specific files to include for content.")
    inc_group.add_argument("--include-extensions-in-tree", nargs="+", default=[], help="Extensions to show in the tree but not their content.")
    inc_group.add_argument("--include-files-in-tree", nargs="+", default=[], help="Specific files to show in the tree but not their content.")
    
    # --- Exclusion Arguments ---
    exc_group = parser.add_argument_group('Exclusion Options')
    exc_group.add_argument("--exclude-extensions", nargs="+", default=[], help="File extensions to completely exclude.")
    exc_group.add_argument("--exclude-files", nargs="+", default=[], help="Specific files to completely exclude.")
    exc_group.add_argument("--exclude-patterns", nargs="+", default=[], help="List of gitignore-style patterns to exclude (e.g., 'dist/*' '*.log').")

    # First pass to find the preset and handle its values manually
    args, _ = parser.parse_known_args()

    preset_extensions = []
    if args.preset:
        preset_values = presets.get(args.preset, {}).copy()
        # Pop extensions to handle them separately for merging
        preset_extensions = preset_values.pop("include_extensions", [])
        parser.set_defaults(**preset_values)

    # Final parse to get the combined arguments
    args = parser.parse_args()
    
    # --- Merge preset and command-line extensions ---
    combined_extensions = preset_extensions + args.include_extensions
    # Remove duplicates while preserving order
    args.include_extensions = list(dict.fromkeys(combined_extensions))
    
    # Check for required arguments after merging
    if not args.include_extensions and not args.include_files:
        parser.error("Either --include-extensions or --include-files must be provided, either directly or via a preset.")
    
    # Normalize extensions to ensure they start with a dot
    args.include_extensions = [f".{ext.lstrip('.')}" for ext in args.include_extensions]
    args.exclude_extensions = [f".{ext.lstrip('.')}" for ext in args.exclude_extensions]
    args.include_extensions_in_tree = [f".{ext.lstrip('.')}" for ext in args.include_extensions_in_tree]

    start_path = ""
    temp_dir = None

    if args.repo:
        try:
            print(f"🔄 Cloning repository from {args.repo}...")
            temp_dir = Path(tempfile.mkdtemp())
            Repo.clone_from(args.repo, temp_dir, multi_options=['--depth=1', '--recursive'])
            start_path = str(temp_dir)
            print("✅ Clone successful.")
        except GitCommandError as e:
            print(f"❌ Error cloning repository: {e}")
            if temp_dir:
                shutil.rmtree(temp_dir)
            return
    else:
        # Find the project root by searching upwards from the current directory
        project_root = find_project_root(Path.cwd())
        if project_root is None:
            print("❌ Error: Not inside a recognized project directory (.git or pyproject.toml not found).")
            sys.exit(1)
        start_path = str(project_root)
        print(f"✅ Found project root at: {start_path}")

    try:
        context = CodeContext(
            start_path=start_path,
            include_extensions=args.include_extensions,
            exclude_extensions=args.exclude_extensions,
            include_files=args.include_files,
            exclude_files=args.exclude_files,
            include_files_in_tree=args.include_files_in_tree,
            include_extensions_in_tree=args.include_extensions_in_tree,
            exclude_patterns=args.exclude_patterns,
        )
        
        # Determine the output based on the arguments
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
                
    finally:
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir)
            print(f"🧹 Cleaned up temporary directory: {temp_dir}")

if __name__ == "__main__":
    main()
