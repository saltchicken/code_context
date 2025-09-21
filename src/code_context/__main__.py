import argparse
import pyperclip
import tempfile
import shutil
from pathlib import Path
from git import Repo, GitCommandError
from .parse import CodeContext

def main():
    """
    Main function for the command-line interface.
    
    Parses arguments to determine what context to gather and how to output it.
    """
    parser = argparse.ArgumentParser(
        description="""Gather and display a codebase context, useful for LLMs.
        By default, it shows the directory tree and all file contents."""
    )
    
    parser.add_argument(
        "extensions", 
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

    args = parser.parse_args()
    
    # Ensure extensions start with a dot
    args.extensions = [f".{ext.lstrip('.')}" for ext in args.extensions]

    start_path = "."
    temp_dir = None

    if args.repo:
        try:
            print(f"🔄 Cloning repository from {args.repo}...")
            temp_dir = Path(tempfile.mkdtemp())
            Repo.clone_from(args.repo, temp_dir, multi_options=['--depth=1'])
            start_path = str(temp_dir)
            print("✅ Clone successful.")
        except GitCommandError as e:
            print(f"❌ Error cloning repository: {e}")
            if temp_dir:
                shutil.rmtree(temp_dir)
            return

    try:
        # This initialization is fast because no I/O is performed yet.
        context = CodeContext(start_path=start_path, extensions=args.extensions)
        
        output_parts = []
        
        # Determine if the user has requested specific parts of the context.
        has_specific_requests = any([args.tree, args.files])

        if has_specific_requests:
            # Build the output from the requested parts.
            # Each property/method call will lazily load data only if needed.
            if args.tree:
                output_parts.append(context.get_directory_tree_string())
            
            if args.files:
                output_parts.append(context.get_file_contents_string())
                
        else:
            # Default behavior: show the full context (tree + files).
            output_parts.append(context.get_full_context())

        final_output = "\n\n".join(output_parts).strip()

        if args.copy:
            pyperclip.copy(final_output)
            print("✅ Context copied to clipboard.")
        else:
            if final_output:
                print(final_output)
            else:
                print("No content found for the specified extensions.")
                
    finally:
        # Clean up the temporary directory if it was created
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir)
            print(f"🧹 Cleaned up temporary directory: {temp_dir}")

if __name__ == "__main__":
    main()
