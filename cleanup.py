import os
import glob

# Find all python files in the macro_topics folder
files = glob.glob("macro_topics/**/*.py", recursive=True)

for file in files:
    with open(file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    with open(file, "w", encoding="utf-8") as f:
        for line in lines:
            # Skip the while loop declaration
            if line.strip() == "while True:":
                continue
            # Remove exactly 4 spaces of indentation for everything else
            if line.startswith("    "):
                f.write(line[4:])
            else:
                f.write(line)

print("✅ All while loops removed and code un-indented!")