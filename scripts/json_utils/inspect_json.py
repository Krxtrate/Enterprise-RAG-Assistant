import os
import re

SMALLTALK_DIR = "smalltalk"

targets = [
    '''
    '''
]

for filename in os.listdir(SMALLTALK_DIR):

    if not filename.endswith(".json"):
        continue

    filepath = os.path.join(
        SMALLTALK_DIR,
        filename
    )

    with open(
        filepath,
        "r",
        encoding="utf-8"
    ) as f:
        content = f.read()

    for target in targets:

        if target in content:

            print("\n===================")
            print(filename)
            print(target)

            idx = content.find(target)

            start = max(0, idx - 50)
            end = min(len(content), idx + 100)

            print(content[start:end])