from langgraph.prebuilt import create_react_agent
from langchain_community.tools import tool
from llms import load_llm
from dotenv import load_dotenv
import os

load_dotenv()
llm = load_llm()

@tool
def summarize_audio(file_path: str) -> str:
    """summarize the audio file or return hello"""
    return f"Simulated audio summary for {file_path}"

audio_summarizer_agent = create_react_agent(
    model=llm,
    tools=[summarize_audio],
    prompt=(
        "You are an audio summarizer agent. Use summarize_audio tool for summarization. "
        "Return only the summary."
    ),
    name="audio_summarizer_agent",
)
