import os
from dotenv import load_dotenv

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

from rating_store import store_rating, get_average_rating
from langchain_core.messages import convert_to_messages

def pretty_print_message(message, indent=False):
    pretty_message = message.pretty_repr(html=True)
    if not indent:
        print(pretty_message)
        return

    indented = "\n".join("\t" + c for c in pretty_message.split("\n"))
    print(indented)


def pretty_print_messages(update, last_message=False):
    is_subgraph = False
    if isinstance(update, tuple):
        ns, update = update
        # skip parent graph updates in the printouts
        if len(ns) == 0:
            return

        graph_id = ns[-1].split(":")[0]
        print(f"Update from subgraph {graph_id}:")
        print("\n")
        is_subgraph = True

    for node_name, node_update in update.items():
        update_label = f"Update from node {node_name}:"
        if is_subgraph:
            update_label = "\t" + update_label

        print(update_label)
        print("\n")

        messages = convert_to_messages(node_update["messages"])
        if last_message:
            messages = messages[-1:]

        for m in messages:
            pretty_print_message(m, indent=is_subgraph)
        print("\n")

from langgraph.prebuilt import create_react_agent

def respond_positive() -> str:
    """Ask user for rating, then store and show average."""
    print("🤖: Thank you for your feedback! Please rate us from 1 to 5 stars ⭐")
    while True:
        try:
            user_input = input("👤 Your Rating (1–5): ")
            rating = int(user_input)
            if 1 <= rating <= 5:
                break
            else:
                print("⚠️ Please enter a number between 1 and 5.")
        except ValueError:
            print("⚠️ Invalid input. Please enter a number.")

    store_rating(rating)
    avg = get_average_rating()
    return f"Thanks! You rated us {rating} ⭐. Our current average rating is {avg} ⭐."

def respond_negative() -> str:
    """Respond to negative sentiment."""
    return "We're sorry to hear that. Please fill out this feedback form: https://feedback-form.com"

# Create sentiment agent
sentiment_agent = create_react_agent(
    model="openai:gpt-4o-mini",
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

# 🚀 Main loop
if __name__ == "__main__":
    while True:
        user_input = input("👤 Your review (type 'exit' to quit): ")
        if user_input.lower() == "exit":
            break

        for chunk in sentiment_agent.stream(
            {"messages": [{"role": "user", "content": user_input}]}
        ):
            pretty_print_messages(chunk)

# for chunk in sentiment_agent.stream(
#     {"messages": [{"role": "user", "content": "The customer service was slow and unhelpful"}]}
# ):
#     pretty_print_messages(chunk)
