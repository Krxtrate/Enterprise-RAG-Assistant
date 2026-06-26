import os
import json

languages = set()

for filename in os.listdir("smalltalk"):

    if not filename.endswith(".json"):
        continue

    path = os.path.join("smalltalk", filename)

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        bot_says = data["body"]["bot_says"]

        for lang in bot_says.keys():
            languages.add(lang)

    except Exception as e:
        print(f"Error in {filename}: {e}")

print(f"\nTOTAL LANGUAGES: {len(languages)}\n")

for lang in sorted(languages):
    print(lang)