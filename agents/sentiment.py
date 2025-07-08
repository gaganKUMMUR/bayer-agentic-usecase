import os
from dotenv import load_dotenv
from .llms import load_llm
from .rating_store import store_rating, get_average_rating
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent

load_dotenv()
llm = load_llm()

def respond_positive() -> str:
    """Ask user for rating. Actual rating will be captured in the next message."""
    return "Thank you for your feedback! Please rate us from 1 to 5 stars ⭐"

def respond_negative() -> str:
    """Respond to negative sentiment."""
    return "We're sorry to hear that. Please fill out this feedback form: https://docs.google.com/forms/d/e/1FAIpQLSf41iiwVb6On_pYQVvChkq8ovl6TD7IQTp6Vuj9HCU9cCRyBA/viewform?usp=sharing&ouid=115447155914510213441"

sentiment_agent = create_react_agent(
    model=llm,
    tools=[respond_positive, respond_negative],
    prompt=(
        "You are a sentiment response agent.\n\n"
        "INSTRUCTIONS:\n"
        "- Read the user's message.\n"
        "- If sentiment is POSITIVE, use the 'respond_positive' tool.\n"
        "- If sentiment is NEGATIVE, use the 'respond_negative' tool.\n"
        "- You MUST use only one tool based on sentiment.\n"
        "- Respond ONLY using the result of the tool call. No extra text."
    ),
    name="sentiment_agent",
)

def get_response_from_review_agent(message_history):
    return sentiment_agent.invoke({"messages": message_history})