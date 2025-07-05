from typing import Annotated
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.prebuilt import InjectedState, create_react_agent
from langgraph.graph import StateGraph, START, MessagesState, END
from langgraph.types import Command
from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.document_loaders import PyPDFLoader
from dotenv import load_dotenv
import os
from news_agent import pretty_print_messages

# Load environment variables
load_dotenv()

# Setup Gemini
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    api_key=os.getenv("GOOGLE_API_KEY")
)

# Root directory for file system access
# file_root = "/Users/gagan/Documents/bayer-agentic-usecase"
# fs = FileSystem(root_dir=file_root)

# Create file management toolkit
# file_toolkit = FileManagementToolkit(root_dir=file_root)
# file_tools = file_toolkit.get_tools()

# Get ReadFileTool specifically
# read_file_tool = next(t for t in file_tools if t.name == "read_file")

# Tool wrapper that calls the ReadFileTool and summarizes

@tool
def summarize_pdf(file_path: str) -> str:
    """Use PyPDFLoader to load and summarize a PDF."""
    try:
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        content = "\n".join([page.page_content for page in pages])
        response = llm.invoke(f"Summarize the following PDF:\n\n{content[:3000]}")
        # print(response)
        return response.content
    except Exception as e:
        # print(str(e))
        return f"Failed to summarize PDF: {str(e)}"

# Dummy audio tool (unchanged)
@tool
def summarize_audio(file_path: str) -> str:
    """summarize the audio file or return hello"""
    return f"Simulated audio summary for {file_path}"

# --- PDF Agent ---
pdf_summarizer_agent = create_react_agent(
    model=llm,
    tools=[summarize_pdf],
    prompt=(
        "You are a PDF summarizer agent. Use the summarize_pdf tool to process the file path provided. "
        "Return only the summary."
    ),
    name="pdf_summarizer_agent",
)

# --- Audio Agent ---
audio_summarizer_agent = create_react_agent(
    model=llm,
    tools=[summarize_audio],
    prompt=(
        "You are an audio summarizer agent. Use summarize_audio tool for summarization. "
        "Return only the summary."
    ),
    name="audio_summarizer_agent",
)

# --- Handoff Tool Generator ---
def create_handoff_tool(agent_name: str, description: str | None = None):
    name = f"transfer_to_{agent_name}"
    description = description or f"Send the task to {agent_name}"

    @tool(name, description=description)
    def handoff_tool(
        state: Annotated[MessagesState, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> Command:
        tool_message = {
            "role": "tool",
            "content": f"Transferring to {agent_name}",
            "name": name,
            "tool_call_id": tool_call_id,
        }
        # print(state["messages"])
        return Command(
            goto=agent_name,
            update={**state, "messages": state["messages"] + [tool_message]},
            graph=Command.PARENT,
        )
    return handoff_tool

# Handoff tools
assign_to_pdf_agent = create_handoff_tool("pdf_summarizer_agent")
assign_to_audio_agent = create_handoff_tool("audio_summarizer_agent")

# --- Supervisor Agent ---
supervisor_agent = create_react_agent(
    model=llm,
    tools=[assign_to_pdf_agent, assign_to_audio_agent],
    prompt=(
        "You are a supervisor managing two agents:\n"
        "- One for summarizing PDF/text documents\n"
        "- One for summarizing audio files\n\n"
        "Identify the file type from user input and use the appropriate handoff tool."
    ),
    name="supervisor",
)

# --- LangGraph Wiring ---
supervisor_graph = (
    StateGraph(MessagesState)
    .add_node("supervisor", supervisor_agent, destinations=("pdf_summarizer_agent", "audio_summarizer_agent", END))
    .add_node("pdf_summarizer_agent", pdf_summarizer_agent)
    .add_node("audio_summarizer_agent", audio_summarizer_agent)
    .add_edge(START, "supervisor")
    .add_edge("pdf_summarizer_agent", "supervisor")
    .add_edge("audio_summarizer_agent", "supervisor")
    .compile()
)


def print_last_assistant_message(state):
    messages = state["messages"]
    print(messages)


# --- Run Once ---
if __name__ == "__main__":
    input_messages = [{
        "role": "user",
        "content": "Please summarize the audio at /Users/gagan/Documents/bayer-agentic-usecase/segment_2_29.72_49.71.mp3"
    }]

    final_state = supervisor_graph.invoke({"messages": input_messages})
    print_last_assistant_message(final_state)
