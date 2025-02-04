import ast
import json
import pprint

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

