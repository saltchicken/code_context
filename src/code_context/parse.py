import os
import pathspec
import ast
import json

class CodeContext:
    def __init__(self, start_path, extensions=None):
        self.start_path = start_path
        self.extensions = extensions
        if self.extensions is None:
            self.extensions = []  # Default to an empty list if no extensions are specified
        self.extensions = extensions
        self.gitignore_spec = self.load_gitignore()
        self.context = []
        self.file_paths = []
        self.dirs = []

        self.parse_contents()

    def load_gitignore(self):
        if ".gitignore" in os.listdir():
            with open(".gitignore", "r") as f:
                return pathspec.PathSpec.from_lines("gitignore", f.readlines())
        else:
            print(".gitignore file not found in the current directory.")
            return None

    def is_ignored(self, path):
        if self.gitignore_spec:
            return self.gitignore_spec.match_file(path)
        else:
            return False

    def get_filtered_dirs(self, root, dirs):
        """Filters out directories that are ignored based on the gitignore_spec."""
        return [
            d
            for d in dirs
            if d != ".git"
            and not self.is_ignored(os.path.join(root, d + "/"))
            and not self.is_ignored(os.path.join(root, d))
        ]

    def get_filtered_files(self, root, files):
        """Filters out files that are ignored based on the gitignore_spec."""
        return [
            f for f in files if not self.is_ignored(os.path.join(root, f))
        ]

    def calculate_depth(self, root, start_path):
        """Calculates the depth of the directory structure."""
        return root.count(os.sep) - start_path.count(os.sep)

    def get_indent(self, depth):
        """Returns the indentation string based on the depth of the directory."""
        return "│   " * depth + "├── "

    def collect_file_paths(self, root, files):
        """Collects files that match the specified extensions."""
        file_paths = [ os.path.join(root, file) for file in files if any(file.endswith(ext) for ext in self.extensions) ]
        return file_paths

    def collect_file_contents(self, file_paths):
        """Collects the contents of files and handles exceptions."""
        output_lines = []
        for file_path in file_paths:
            output_lines.append(f"\n----- {file_path} -----")
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    output_lines.append(f.read())
            except Exception as e:
                output_lines.append(f"Error reading {file_path}: {e}")
        return output_lines

    def parse_contents(self):
        for root, dirs, files in os.walk(self.start_path):
            # Filter directories and files based on gitignore
            dirs[:] = self.get_filtered_dirs(root, dirs)
            self.dirs.extend(dirs)
            files = self.get_filtered_files(root, files)

            # Calculate the depth of the directory structure
            depth = self.calculate_depth(root, self.start_path)
            indent = self.get_indent(depth)
            self.context.append(f"{indent}{os.path.basename(root)}/")

            # Collect files that match extensions
            self.file_paths.extend(self.collect_file_paths(root, files))

            # Collect the files in the directory
            subindent = self.get_indent(depth + 1)
            for file in files:
                if any(file.endswith(ext) for ext in self.extensions):
                    self.context.append(f"{subindent}{file}")

        # After collecting the tree, add the contents of each file
        self.context.append("\n----- File Contents -----")
        self.context.extend(self.collect_file_contents(self.file_paths))

        # Join all lines into a single string for printing or clipboard copying
        self.context = "\n".join(self.context)

def extract_functions_from_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            docstring = ast.get_docstring(node)
            
            # Remove docstring from the function body
            if docstring and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
                node.body.pop(0)  # Remove the first statement (which is the docstring)

            functions.append({
                "name": node.name,
                "docstring": docstring,
                "code": ast.unparse(node),
            })

    return functions

def get_functions(file_paths: list) -> list:
    functions = []
    for file_path in file_paths:
        functions.extend(extract_functions_from_file(file_path))
    return functions

def save_functions(function: list) -> None:
    with open("code_dataset.json", "w") as f:
        json.dump(function, f, indent=2)

def read_functions(json_file_path: str) -> None:
    with open(json_file_path, "r") as f:
        return json.load(f)

def print_functions(data) -> None:
    for func in data:
        print("Function:", func["name"])
        print("Docstring:", func["docstring"])
        print("Code:", func["code"])


