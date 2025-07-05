import os
import json
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import date
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START
from dotenv import load_dotenv
load_dotenv()   # <-- this pulls in your .env variables

FROM_EMAIL = os.getenv("FROM_EMAIL")
FROM_PASS  = os.getenv("FROM_EMAIL_PASS")
TO_EMAIL   = os.getenv("TO_EMAIL")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ─── Define the shared state shape ────────────────────────────────────────────
class State(TypedDict, total=False):
    headlines: list[str]
    summary: str

# ─── Agent node implementations ────────────────────────────────────────────────
def fetch_agent(state: State) -> State:
    """Fetch today’s top tech headlines and store in state['headlines']."""
    resp = requests.get(
        "https://newsapi.org/v2/top-headlines",
        params={
            "category": "technology",
            "pageSize": 10,
            "apiKey": os.getenv("NEWS_API_KEY"),
            "language": "en",
        },
    )
    resp.raise_for_status()
    headlines = [a["title"] for a in resp.json().get("articles", [])]
    return {"headlines": headlines}

def summarizer_agent(state: State) -> State:
    """Summarize the fetched headlines into a 5-bullet summary."""
    headlines = state.get("headlines", [])
    prompt = (
        "Summarize these tech headlines into 5 concise bullet points:\n\n"
        + "\n".join(f"- {h}" for h in headlines)
    )

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": os.getenv("GEMINI_API_KEY"),
    }
    body = {"contents": [{"parts": [{"text": prompt}]}]}
    r = requests.post(url, json=body, headers=headers)
    r.raise_for_status()

    candidate = r.json()["candidates"][0]
    parts = candidate["content"]["parts"]
    summary = "".join(p["text"] for p in parts).strip()
    return {"summary": summary}

def email_agent(state: State) -> State:
    """Send the summary via Gmail SMTP using an App Password."""
    summary = state.get("summary", "")
    today   = date.today().strftime("%B %d, %Y")
    subject = f"Tech News Digest — {today}"

    # Build a clean bullet list
    lines = [
        "Hi there,",
        "",
        f"Here are today’s top tech headlines ({today}):",
        ""
    ]
    for ln in summary.splitlines():
        clean = ln.lstrip(" *").replace("**", "").strip()
        if clean:
            lines.append(f"• {clean}")
    lines += ["", "Have a great day!", "— Niharika"]
    body = "\n".join(lines)

    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"]    = os.getenv("FROM_EMAIL")
    msg["To"]      = os.getenv("TO_EMAIL")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(os.getenv("FROM_EMAIL"), os.getenv("FROM_EMAIL_PASS"))
        smtp.send_message(msg)

    return {}

# ─── Build and run the LangGraph StateGraph ─────────────────────────────────
if __name__ == "__main__":
    graph_builder = StateGraph(State)
    graph_builder.add_node(fetch_agent)
    graph_builder.add_node(summarizer_agent)
    graph_builder.add_node(email_agent)

    graph_builder.add_edge(START, "fetch_agent")
    graph_builder.add_edge("fetch_agent", "summarizer_agent")
    graph_builder.add_edge("summarizer_agent", "email_agent")

    graph = graph_builder.compile()
    graph.invoke({})  # starts with an empty state
    print("📬 Digest sent!")
