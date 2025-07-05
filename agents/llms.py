from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

def load_llm():
    # uses_llm = os.getenv("llm")
    # if uses_llm == "gemini":
    return ChatGoogleGenerativeAI(model="gemini-2.0-flash",api_key=os.getenv("GOOGLE_API_KEY"))
    # else:
    #     return ChatOpenAI(model="gpt4.0")