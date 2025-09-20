import argparse
import pyperclip
from .parse import CodeContext

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
    parser.add_argument(
        "--dir_tree",
        action="store_true",
        help="Get directory tree",
    )

    args = parser.parse_args()
    args.extensions = [f".{s}" for s in args.extensions]

    context = CodeContext(start_path=".", extensions=args.extensions)

    if args.copy:
        pyperclip.copy(context.context)
    elif args.functions:
        context.print_functions()
    elif args.dir_tree:
        print("\n".join(context.dir_tree))
    else:
        print(context.context)
