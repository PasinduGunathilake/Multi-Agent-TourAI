from setuptools import find_packages, setup

setup(
    name = "Multi_Agent_TourAI",
    version= "1.0.0",
    author = "Pasindu Gunathilake",
    author_email= "pasindugunathilake144@gmail.com",
    description= "A Muti agent tour ai for effective tour planning using MCP, Guardrails, Long-term / Short_term  Persisistance Memory and Human In the Loop",
    packages=find_packages(),
    install_requires=[
        "langgraph==1.2.2",
        "langchain==1.3.2",
        "langchain-groq==1.1.3",
        "langchain-community==0.4.2",
        "langchain-tavily==0.2.18",
        "psycopg[binary]==3.3.4",
        "psycopg_pool==3.3.1",
        "python-dotenv==1.2.2",
        "tavily-python==0.7.24",
        "requests==2.34.2",
        "langgraph-checkpoint-postgres==3.1.0",
        "airportsdata==20260803",
        "pycountry==26.2.16",
        "fastapi==0.136.3",
        "uvicorn==0.48.0",
        "jinja2==3.1.6",
        "pyyaml==6.0.3",
        "langchain-mcp-adapters==0.3.0",
        "nest_asyncio==1.6.0",
        "mcp==1.28.1",
        "uv",
    ]
)

# pip install -e .