from typing import Annotated
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.prebuilt import InjectedState, create_react_agent
from langgraph.graph import StateGraph, START, MessagesState, END
from langgraph.types import Command
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import PyPDFLoader
from dotenv import load_dotenv
import os
from news_agent import pretty_print_messages
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    api_key=os.getenv("GOOGLE_API_KEY")
)


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


@tool
def emailer_tool(receiver_address: str, message_body: str, email_subject: str):
    """email the reciver with the given message"""
    try:
        email_host = os.getenv("EMAIL_HOST")
        email_port = int(os.getenv("EMAIL_PORT"))
        email_user = os.getenv("EMAIL_USER")
        email_pass = os.getenv("EMAIL_PASS")
        msg = MIMEMultipart()
        msg["From"] = email_user
        msg["To"] = receiver_address
        msg["Subject"] = email_subject
        msg.attach(MIMEText(message_body, "plain"))

        with smtplib.SMTP(email_host, email_port) as server:
            server.starttls()
            server.login(email_user, email_pass)
            server.send_message(msg)
        print(receiver_address)
        return f"Summary successfully sent to {receiver_address}"
    
    except Exception as e:
        print(str(e))
        return f"Failed to send email: {str(e)}"


email_agent = create_react_agent(
    model=llm,
    tools=[emailer_tool],
    prompt=(
        "You are an agent capable of mailing the reciver with message"
        "You need to call the tool and give it the reciver address, message body and the subject, generate subject accordingly"
    ),
    name="email_agent"
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
    .add_node("pdf_summarizer_agent", pdf_summarizer_agent, input_updates=lambda state: {
              **state,
              "summary": state["messages"][-1].content  # store last assistant message
          })
    .add_node("audio_summarizer_agent", audio_summarizer_agent)
    .add_node("email_agent", email_agent)
    .add_edge(START, "supervisor")
    .add_edge("pdf_summarizer_agent", "supervisor")
    .add_edge("audio_summarizer_agent", "supervisor")
    .add_edge("email_agent", "supervisor")
    .compile()
)
png_bytes = supervisor_graph.get_graph().draw_mermaid_png()
with open("graph.png","wb") as file:
    file.write(png_bytes)

def print_last_assistant_message(state):
    messages = state["messages"]
    for message in messages:
        print(message)
        print()

# --- Run Once ---
if __name__ == "__main__":
    input_messages = [{
        "role": "user",
        "content": "summarize the pdf at ./1-s2.0-S2352847821000666-main-2.pdf and email the summary to kummurgagan@gmail.com"
    }]

    final_state = supervisor_graph.invoke({"messages": input_messages})
    print_last_assistant_message(final_state)


    # emailer_tool("kummurgagan@gmail.com", "Hi there")