import ast
import json
import pprint

def extract_functions_from_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append({
                "name": node.name,
                "docstring": ast.get_docstring(node),
                "code": ast.unparse(node),
            })

    return functions

if __name__ == "__main__":
    dataset = []
    for file in ["parse.py"]:
        dataset.extend(extract_functions_from_file("parse.py"))

    print(dataset)
    with open("code_dataset.json", "w") as f:
        json.dump(dataset, f, indent=2)

    with open("code_dataset.json", "r") as f:
        data = json.load(f)

        print("--------------------------------------------")

        for func in data:
            print("Function:", func["name"])
            print("Docstring:", func["docstring"])
            print("Code:", func["code"])
