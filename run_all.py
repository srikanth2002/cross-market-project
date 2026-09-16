import os
import sys

# Run this file from the project root (the folder that contains
# app.py, market.db, requirements.txt, and the scripts/ subfolder)

scripts = [
    "scripts/create_db.py",
    "scripts/fetch_crypto.py",
    "scripts/fetch_oil.py",
    "scripts/fetch_stocks.py",
]

for script in scripts:
    print(f"Running {script} ...")
    exit_code = os.system(f"python {script}")
    if exit_code != 0:
        print(f"Failed: {script} (exit code {exit_code}). Stopping.")
        sys.exit(1)

print("All scripts completed successfully.")
