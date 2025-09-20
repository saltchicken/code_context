import argparse
import pyperclip
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
        "--functions",
        action="store_true",
        help="Extract and show Python functions from .py files."
    )
    
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy the generated context to the clipboard instead of printing."
    )

    args = parser.parse_args()
    
    # Ensure extensions start with a dot
    args.extensions = [f".{ext.lstrip('.')}" for ext in args.extensions]

    # This initialization is fast because no I/O is performed yet.
    context = CodeContext(start_path=".", extensions=args.extensions)
    
    output_parts = []
    
    # Determine if the user has requested specific parts of the context.
    has_specific_requests = any([args.tree, args.files, args.functions])

    if has_specific_requests:
        # Build the output from the requested parts.
        # Each property/method call will lazily load data only if needed.
        if args.tree:
            output_parts.append(context.get_directory_tree_string())
        
        if args.files:
            output_parts.append(context.get_file_contents_string())
            
        if args.functions:
            # To make this work, you would add a `get_formatted_functions` method
            # to your CodeContext class to nicely format the function data.
            # Assuming such a method exists:
            # output_parts.append(context.get_formatted_functions())
            
            # For now, let's just print the raw data:
            if context.functions:
                output_parts.append("--- Parsed Functions ---")
                for func in context.functions:
                    func_str = (
                        f"\n----- Function: {func['name']} -----\n"
                        f"Docstring: {func['docstring']}\n"
                        f"Code:\n{func['code']}"
                    )
                    output_parts.append(func_str)

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

if __name__ == "__main__":
    main()
