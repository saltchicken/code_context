import os
import pathspec


def load_gitignore():
    with open(".gitignore", "r") as f:
        return pathspec.PathSpec.from_lines("gitignore", f.readlines())


def is_ignored(path, gitignore_spec):
    return gitignore_spec.match_file(path)


def print_tree_and_contents(startpath, gitignore_spec, extensions=None):
    if extensions is None:
        extensions = []  # Default to an empty list if no extensions are specified

    output_lines = []  # List to collect all output lines
    file_paths = []

    for root, dirs, files in os.walk(startpath):
        # Skip directories that are ignored
        dirs[:] = [
            d
            for d in dirs
            if d != ".git"
            and not is_ignored(os.path.join(root, d + "/"), gitignore_spec)
            and not is_ignored(os.path.join(root, d), gitignore_spec)
        ]
        print(gitignore_spec)

        # Skip files that are ignored
        files = [
            f for f in files if not is_ignored(os.path.join(root, f), gitignore_spec)
        ]

        # Calculate the depth of the directory structure
        depth = root.count(os.sep) - startpath.count(os.sep)
        indent = "│   " * depth + "├── "
        output_lines.append(f"{indent}{os.path.basename(root)}/")

        # Collect the files for later content printing (based on extensions)
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_paths.append(os.path.join(root, file))

        # Collect the files in the directory
        subindent = "│   " * (depth + 1) + "├── "
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                output_lines.append(f"{subindent}{file}")

    # After collecting the tree, add the contents of each file
    output_lines.append("\n----- File Contents -----")
    for file_path in file_paths:
        output_lines.append(f"\n----- {file_path} -----")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                output_lines.append(f.read())
        except Exception as e:
            output_lines.append(f"Error reading {file_path}: {e}")

    # Join all lines into a single string for printing or clipboard copying
    final_output = "\n".join(output_lines)

    return final_output
