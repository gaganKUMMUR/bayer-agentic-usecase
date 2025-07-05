from typing import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import PyPDFLoader
from dotenv import load_dotenv
import os
from llms import load_llm

load_dotenv()

llm = load_llm()

@tool
def summarize_pdf(file_path: str) -> str:
    """Use PyPDFLoader to load and summarize a PDF."""
    try:
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        content = "\n".join([page.page_content for page in pages])
        response = llm.invoke(f"Summarize the following PDF:\n\n{content[:3000]}")
        return response.content
    except Exception as e:
        return f"Failed to summarize PDF: {str(e)}"

pdf_summarizer_agent = create_react_agent(
    model=llm,
    tools=[summarize_pdf],
    prompt=(
        "You are a PDF summarizer agent. Use the summarize_pdf tool to process the file path provided. "
        "Return only the summary."
    ),
    name="pdf_summarizer_agent",
)
