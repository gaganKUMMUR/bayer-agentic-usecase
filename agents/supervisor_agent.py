from langgraph.prebuilt import create_react_agent
from typing import Annotated
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import create_react_agent, InjectedState
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.types import Command
from .emailer_agent import email_agent
from .audio_summary_agent import audio_summarizer_agent
from .notes_agent import pdf_summarizer_agent
from .news_agent import news_search_agent
from .llms import load_llm
from .meeting_scheduler import meeting_scheduler_agent
from dotenv import load_dotenv
import os
 
load_dotenv()
 
llm = load_llm()

PROMPT="""
You are a supervisor managing five specialized agents:\n

\n

- PDF Summarizer: Accepts a PDF document uploaded by the user and returns a clear, concise summary of its contents. Used when no summary exists yet for the uploaded PDF.\n

\n

- Audio Summarizer: Processes uploaded audio files by first transcribing them and then summarizing the spoken content. Used when no summary exists yet for the uploaded audio.\n

\n

- News Fetcher: Gathers the latest relevant news articles based on the user's request or topic of interest, and generates a summarized version. Used when no current news summary is available.\n

\n

- Emailer: Sends any available summary (from PDF, audio, or news) to the user via email. Triggered when an email address is provided and a summary is ready to send.\n

\n

- Meet Scheduler: Interprets the user’s request to schedule a meeting, extracts and formats the desired date and time, checks the boss’s availability via the calendar, and either schedules the meeting or replies with the next available slot if the requested time is unavailable.\n

\n

Your job is to analyze the user's request and orchestrate the correct sequence of tool usage, using only one tool at a time.\n

\n

TO SEND EMAIL USE EMAILER AGENT and write message body (mostly the summary) and email subject accordingly


**Workflow Logic:**\n

\n

1. If the user uploads a PDF file and no summary exists yet, call the **PDF Summarizer**.\n

2. If the user uploads an audio file and no summary exists yet, call the **Audio Summarizer**.\n

3. If the user requests news content and it is not yet available, call the **News Fetcher**.\n

4. If a summary (from PDF, audio, or news) already exists **and** the user provides an email address, call the **Emailer** to send the summary.\n

5. If the user requests to email the news and the news summary is already available, call the **Emailer**.\n

6. If the user asks to schedule a meeting:\n

   - Use the **Meet Scheduler** to extract the requested date and time.\n

   - Check the boss's calendar for availability.\n

   - If the requested slot is free, schedule the meeting.\n

   - If the slot is busy, inform the user that the boss is unavailable and suggest the next available time.\n

\n

Always:\n

- Use only one tool per step.\n

- Re-evaluate the next action based on updated context after each tool finishes.\n

- Do not skip steps or make assumptions. Only act based on what's available in the current state.\n

\n

Wait for each tool’s output before proceeding to the next step.\n

"""

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
assign_to_news_agent = create_handoff_tool("news_agent")
assign_to_meeting_scheduler_agent = create_handoff_tool("meeting_scheduler_agent")
 
# --- Supervisor Agent ---
supervisor_agent = create_react_agent(
    model=llm,
    tools=[assign_to_pdf_agent, assign_to_audio_agent, assign_to_email_agent, assign_to_news_agent, assign_to_meeting_scheduler_agent],
    prompt=(
        PROMPT
    ),
    name="supervisor"
)
 
# --- LangGraph Wiring ---
supervisor_graph = (
    StateGraph(MessagesState)
    .add_node("supervisor", supervisor_agent, destinations=("pdf_summarizer_agent", "audio_summarizer_agent", "email_agent","news_agent", "meeting_scheduler_agent",END))
    .add_node("pdf_summarizer_agent", pdf_summarizer_agent, input_updates=lambda state: {**state,"summary": state["messages"][-1].content})
    .add_node("audio_summarizer_agent", audio_summarizer_agent, input_updates=lambda state:{**state, "summary": state["messages"][-1].content})
    .add_node("news_agent", news_search_agent, input_updates=lambda state:{**state, "news": sta["messages"][-1].content})
    .add_node("meeting_scheduler_agent", meeting_scheduler_agent, input_updates=lambda state:{**state, "meeting_status": state["messages"][-1].content})
    .add_node("email_agent", email_agent)
    .add_edge(START, "supervisor")
    .add_edge("pdf_summarizer_agent", "supervisor")
    .add_edge("audio_summarizer_agent", "supervisor")
    .add_edge("email_agent", "supervisor")
    .add_edge("news_agent", "supervisor")
    .add_edge("meeting_scheduler_agent", "supervisor")
    .compile()
)


png_bytes = supervisor_graph.get_graph().draw_mermaid_png()
with open("graph.png","wb") as file:
    file.write(png_bytes)


# --- Run Once ---
if __name__ == "__main__":
    input_messages = [{
        "role": "user",
        "content": "Schedule a meeting on 15th of july from from 9:30 AM for 1 hour"
    }]
 
    final_state = supervisor_graph.invoke({"messages": input_messages})
    print(final_state)