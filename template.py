import os 
from pathlib import Path

project_name = "Multi_Agent_TourAI"

list_of_dirnfiles = [
    f"{project_name}/tools/__init__.py",
    f"{project_name}/tools/flight_tool.py",
    f"{project_name}/tools/tavily_tool.py",
    f"{project_name}/tools/logger.py",


    # root level components
    ".env",
    ".dockerignore",
    "setup.py",
    "app.py",
    "backend.py",
    "test.py",
    "requirements.txt",
    "templates/index.html",
    ".gitignore",
    "static/script.js",
    "static/styles.css",

]

for filepath in list_of_dirnfiles:
    filepath = Path(filepath)
    filedir, filename = os.path.split(filepath)

    if filedir != "":
        os.makedirs(filedir, exist_ok=True)
        print(f"Creating dir: {filedir}")

    if (not os.path.exists(filepath)) or (os.path.getsize(filepath) == 0):
        with open(filepath, "w") as f:
            pass
            print(f"Creating file: {filepath}")
    else:
        print(f"File already exists: {filename}")