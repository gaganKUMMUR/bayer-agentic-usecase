from langgraph.prebuilt import create_react_agent
from langchain_community.tools import tool
from .llms import load_llm
from dotenv import load_dotenv
import whisper
import os
import ssl
import urllib.request

ssl._create_default_https_context = ssl._create_unverified_context

load_dotenv()
llm = load_llm()

# @tool
def summarize_audio(file_path: str) -> str:
    """summarize the audio file or return hello"""
    model = whisper.load_model("models/base.en.pt")
    result = model.transcribe(file_path)
    print(result["text"])
    return result["text"]

audio_summarizer_agent = create_react_agent(
    model=llm,
    tools=[summarize_audio],
    prompt=(
        "You are an audio summarizer agent. Use summarize_audio tool for summarization. "
        "Return only the summary."
    ),
    name="audio_summarizer_agent",
)


if __name__ == "__main__":
    summarize_audio("df")