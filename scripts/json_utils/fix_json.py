import os
import re

SMALLTALK_DIR = "smalltalk"

replacements = {
    '''
    '''
}

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

    original_content = content

    for wrong, correct in replacements.items():

        if wrong in content:

            print(f"Replacing {wrong} -> {correct}")

            content = content.replace(
                wrong,
                correct
            )

    if content != original_content:

        with open(
            filepath,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(content)

        print(
            f"Fixed: {filename}"
        )

print("\nDone.")