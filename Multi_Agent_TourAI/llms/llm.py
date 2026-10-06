import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing. Please add it to your environmental variable file.")

# LLM Confuguration
llm = ChatGroq(
    model = "llama-3.3-70b-versatile",
    api_key = GROQ_API_KEY
)