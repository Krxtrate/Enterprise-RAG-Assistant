import os
import json
import re

placeholders = set()

for filename in os.listdir("smalltalk"):
    if not filename.endswith(".json"):
        continue

    path = os.path.join("smalltalk", filename)

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        text = json.dumps(data)

        matches = re.findall(r"%[A-Za-z_][A-Za-z0-9_]*", text)

        placeholders.update(matches)

    except Exception as e:
        print(f"Error in {filename}: {e}")

print("\nPLACEHOLDERS FOUND:")
for p in sorted(placeholders):
    print(p)