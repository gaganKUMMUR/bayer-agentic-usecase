from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from .llms import load_llm
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

load_dotenv()

llm = load_llm()

# @tool
def emailer_tool(receiver_address: str, message_body: str, email_subject: str):
    """email the reciver with the given message"""
    try:
        email_host = os.getenv("EMAIL_HOST")
        email_port = int(os.getenv("EMAIL_PORT"))
        email_user = os.getenv("EMAIL_USER")
        email_pass = os.getenv("EMAIL_PASS")
        print(email_host, email_pass, email_port, email_user)
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
    prompt = (
    "You are an intelligent email assistant.\n"
    "\n"
    "Your task is to send professional, personalized, and clearly written emails based on the user's input.\n"
    "\n"
    "Use the tool `emailer_tool` to send the email.\n"
    "\n"
    "You must:\n"
    "1. Carefully understand the user's request and intention.\n"
    "2. Compose a clear, well-formatted email message based on the request. Write in complete sentences.\n"
    "3. Generate an appropriate subject line that summarizes the purpose of the email.\n"
    "4. Call the tool `emailer_tool` with:\n"
    "   - `receiver_address`: the intended recipient's email.\n"
    "   - `message_body`: the generated message.\n"
    "   - `email_subject`: the generated subject.\n"
    "\n"
    "🧠 Always think before generating — structure the email with greetings, body, and a closing if appropriate.\n"
    "Do **not** reply with the email content to the user — instead, call the `emailer_tool` directly with the appropriate arguments."
),
    name="email_agent"
)


if __name__ == "__main__":
    emailer_tool("kummurgagan@gmail.com", "hello", "hi there")