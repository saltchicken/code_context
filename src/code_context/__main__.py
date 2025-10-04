import argparse
import pyperclip
import tempfile
import shutil
import importlib.resources
from pathlib import Path
from git import Repo, GitCommandError
from code_context.parse import CodeContext

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

def load_presets() -> dict:
    """
    Loads the built-in presets from the packaged `default_presets.toml` file.
    """
    try:
        files = importlib.resources.files('code_context')
        presets_text = files.joinpath('default_presets.toml').read_text(encoding='utf-8')
        return tomllib.loads(presets_text)
    except (FileNotFoundError, ModuleNotFoundError):
        # Return an empty dict if the file is missing for any reason
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
        By default, it shows the directory tree and all file contents."""
    )
    
    parser.add_argument(
        "--preset", 
        choices=preset_names, 
        help="Use a predefined set of options from pyproject.toml."
    )
    
    parser.add_argument(
        "--extensions", 
        nargs="+", 
        help="List of file extensions to include (e.g., py js html).", 
        type=str
    )

    parser.add_argument(
        "--repo", 
        help="URL of a Git repository to clone and analyze.", 
        type=str
    )

    parser.add_argument(
        "--tree", 
        action="store_true", 
        help="Show only the directory tree structure."
    )

    parser.add_argument(
        "--files", 
        action="store_true", 
        help="Show only the contents of the files."
    )
    
    parser.add_argument(
        "--copy", 
        action="store_true", 
        help="Copy the generated context to the clipboard instead of printing."
    )
    
    parser.add_argument(
        "--include-file-in-tree", 
        nargs="+", 
        default=[], 
        help="Specify file names to include in the directory tree but not their contents (e.g., pyproject.toml README.md).", 
        type=str
    )
    
    parser.add_argument(
        "--only-files", 
        nargs="+", 
        default=[], 
        help="Supersede extensions and only include the content of specified files. The tree still shows all files matching extensions.", 
        type=str
    )

    parser.add_argument(
        "--exclude", 
        nargs="+", 
        default=[], 
        help="List of gitignore-style patterns to exclude (e.g., 'src/tests/*' '*.log').", 
        type=str
    )

    # First pass to find the preset
    args, _ = parser.parse_known_args()

    # If a preset is chosen, set its values as defaults for the next parse
    if args.preset:
        preset_values = presets.get(args.preset, {})
        parser.set_defaults(**preset_values)

    # Final parse to get the combined arguments
    args = parser.parse_args()
    
    # Check for required arguments after defaults are set
    if not args.extensions:
        parser.error("The --extensions argument is required, either directly or via a preset.")
    
    # Ensure extensions start with a dot
    args.extensions = [f".{ext.lstrip('.')}" for ext in args.extensions]

    start_path = "."
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

    try:
        context = CodeContext(
            start_path=start_path, 
            extensions=args.extensions,
            include_in_tree_only=args.include_file_in_tree,
            only_files=args.only_files,
            exclude_patterns=args.exclude
        )
        
        output_parts = []
        
        has_specific_requests = any([args.tree, args.files])

        if has_specific_requests:
            if args.tree:
                output_parts.append(context.get_directory_tree_string())
            
            if args.files:
                output_parts.append(context.get_file_contents_string())
                
        else:
            output_parts.append(context.get_full_context())

        final_output = "\n\n".join(output_parts).strip()

        if args.copy:
            pyperclip.copy(final_output)
            print("✅ Context copied to clipboard.")
        else:
            if final_output:
                print(final_output)
            else:
                print("No content found for the specified extensions or files.")
                
    finally:
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir)
            print(f"🧹 Cleaned up temporary directory: {temp_dir}")

if __name__ == "__main__":
    main()
