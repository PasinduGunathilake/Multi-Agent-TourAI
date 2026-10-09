import os 
from pathlib import Path

project_name = "Multi_Agent_TourAI"

list_of_dirnfiles = [
    f"{project_name}/__init__.py",

    # LLM module
    f"{project_name}/llms/__init__.py",
    f"{project_name}/llms/llm.py",
    
    # agents module
    f"{project_name}/agents/__init__.py",
    f"{project_name}/agents/itinerary_agent.py",
    f"{project_name}/agents/flight_agent.py",
    f"{project_name}/agents/hotel_agent.py",
    f"{project_name}/agents/final_agent.py",

    # graph module (state & workflow)
    f"{project_name}/graph/__init__.py",
    f"{project_name}/graph/state.py",
    f"{project_name}/graph/workflow.py",

    # tools module (API)
    f"{project_name}/tools/__init__.py",
    f"{project_name}/tools/flight_tool.py",
    f"{project_name}/tools/tavily_tool.py",

    # memory & database module (PostgresServer)
    f"{project_name}/memory/__init__.py",
    f"{project_name}/memory/checkpointer.py",

    # config & prompts module
    f"{project_name}/config/__init__.py",
    f"{project_name}/config/config.yaml",
    f"{project_name}/config/prompts.py",

    # utils & logger module
    f"{project_name}/utils/__init__.py",
    f"{project_name}/utils/flight_utils.py",
    f"{project_name}/utils/logger.py",

    # testing module
    "tests/__init__.py",
    "tests/test_flight_utils.py",
    "tests/test_flight_tool.py",
    "tests/test_tavily_tool.py",

    # root level components
    ".env",
    ".dockerignore",
    ".gitignore",
    "README.md",
    "setup.py",
    "app.py",
    "entrypoint.py",
    "backend.py",
    "requirements.txt", # for Rest api, if you need frontend make separate dir and go on.
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