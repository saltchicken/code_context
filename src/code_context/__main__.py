import argparse
import pyperclip
from .parse import print_tree_and_contents, load_gitignore


def main():
    parser = argparse.ArgumentParser(description="Get codebase context for LLM input")
    parser.add_argument(
        "--clip",
        action="store_true",
        help="Send context to clipboard instead of printing",
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Send context to clipboard instead of printing",
    )

    args = parser.parse_args()

    gitignore_spec = load_gitignore()
    extensions_to_print = [".py", ".txt"]  # Specify the extensions you want to print
    context = print_tree_and_contents(
        ".", gitignore_spec, extensions=extensions_to_print
    )

    if args.clip or args.copy:
        pyperclip.copy(context)
    else:
        print(context)
