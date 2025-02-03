import argparse
import pyperclip
from .parse import get_functions, print_functions, CodeContext


def main():
    parser = argparse.ArgumentParser(description="Get codebase context for LLM input")
    parser.add_argument(
        "extensions", nargs="+", help="List of extensions to print", type=str
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Send context to clipboard instead of printing",
    )

    parser.add_argument(
        "--functions",
        action="store_true",
        help="Get functions",
    )

    args = parser.parse_args()
    args.extensions = [f".{s}" for s in args.extensions]

    context = CodeContext(start_path=".", extensions=args.extensions)

    if args.copy:
        pyperclip.copy(context.context)
    elif args.functions:
        functions = get_functions(context.file_paths)
        print_functions(functions)
    else:
        print(context.context)
        print(context.file_paths)
