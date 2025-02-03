import json

with open("code_dataset.json") as f:
    data = json.load(f)

with open("fine_tune.jsonl", "w") as f:
    for item in data:
        json.dump({
            "instruction": f"What does the function '{item['name']}' do?",
            "input": item["code"],
            "output": item["docstring"] or "No docstring available."
        }, f)
        f.write("\n")
