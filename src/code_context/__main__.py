import os
import pathspec

# Load the .gitignore file and create a pathspec object
def load_gitignore():
    with open('.gitignore', 'r') as f:
        return pathspec.PathSpec.from_lines('gitignore', f.readlines())

# Check if a file is ignored based on the .gitignore rules
def is_ignored(path, gitignore_spec):
    return gitignore_spec.match_file(path)

# Print the tree and file contents for specific extensions
def print_tree_and_contents(startpath, gitignore_spec, extensions=None):
    if extensions is None:
        extensions = []  # Default to an empty list if no extensions are specified

    # Store all file paths for content printing later
    file_paths = []

    # Traverse the directory tree
    for root, dirs, files in os.walk(startpath):
        # Skip directories that are ignored
        dirs[:] = [d for d in dirs if d != '.git' and not is_ignored(os.path.join(root, d), gitignore_spec)]
        
        # Skip files that are ignored
        files = [f for f in files if not is_ignored(os.path.join(root, f), gitignore_spec)]
        
        # Calculate the depth of the directory structure
        depth = root.count(os.sep) - startpath.count(os.sep)
        indent = '│   ' * depth + '├── '
        print(f"{indent}{os.path.basename(root)}/")
        
        # Collect the files for later content printing (based on extensions)
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_paths.append(os.path.join(root, file))
        
        # Print the files in the directory
        subindent = '│   ' * (depth + 1) + '├── '
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                print(f"{subindent}{file}")

    # After printing the tree, print the contents of each file
    print("\n----- File Contents -----")
    for file_path in file_paths:
        print(f"\n----- {file_path} -----")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                print(f.read())
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

# Example usage:
def main():
    gitignore_spec = load_gitignore()
    extensions_to_print = ['.py', '.txt']  # Specify the extensions you want to print
    print_tree_and_contents('.', gitignore_spec, extensions=extensions_to_print)

