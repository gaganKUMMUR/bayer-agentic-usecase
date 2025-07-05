from langgraph.prebuilt import create_react_agent
from typing import Annotated
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import create_react_agent, InjectedState
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.types import Command
from emailer_agent import email_agent
from audio_summary_agent import audio_summarizer_agent
from notes_agent import pdf_summarizer_agent
from llms import load_llm
from dotenv import load_dotenv
import os

load_dotenv()

llm = load_llm()


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
assign_to_email_agent = create_handoff_tool("email_agent")

# --- Supervisor Agent ---
supervisor_agent = create_react_agent(
    model=llm,
    tools=[assign_to_pdf_agent, assign_to_audio_agent, assign_to_email_agent],
    prompt=(
        "You are a supervisor managing three agents:\n"
        "- PDF summarizer\n- Audio summarizer\n- Emailer\n\n"
        "Check the user's request.\n"
        "If the request includes a PDF and no summary is available yet, call PDF summarizer.\n"
        "If a summary is already available and an email address is provided, call the emailer agent."
        "\n\nUse tools one at a time."
    ),
    name="supervisor"
)

# --- LangGraph Wiring ---
supervisor_graph = (
    StateGraph(MessagesState)
    .add_node("supervisor", supervisor_agent, destinations=("pdf_summarizer_agent", "audio_summarizer_agent", "email_agent",END))
    .add_node("pdf_summarizer_agent", pdf_summarizer_agent, input_updates=lambda state: {**state,"summary": state["messages"][-1].content})
    .add_node("audio_summarizer_agent", audio_summarizer_agent, input_updates=lambda state:{**state, "summary": state["messages"][-1].content})
    .add_node("email_agent", email_agent)
    .add_edge(START, "supervisor")
    .add_edge("pdf_summarizer_agent", "supervisor")
    .add_edge("audio_summarizer_agent", "supervisor")
    .add_edge("email_agent", "supervisor")
    .compile()
)


# png_bytes = supervisor_graph.get_graph().draw_mermaid_png()
# with open("graph.png","wb") as file:
#     file.write(png_bytes)


# --- Run Once ---
if __name__ == "__main__":
    input_messages = [{
        "role": "user",
        "content": "summarize the pdf at ./1-s2.0-S2352847821000666-main-2.pdf and email the summary to kummurgagan@gmail.com"
    }]

    final_state = supervisor_graph.invoke({"messages": input_messages})
    # print_last_assistant_message(final_state)