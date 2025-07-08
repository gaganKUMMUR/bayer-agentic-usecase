from langgraph.prebuilt import create_react_agent
from langchain_tavily import TavilySearch
from dotenv import load_dotenv
from .llms import load_llm
load_dotenv()
web_search = TavilySearch()

llm = load_llm()

news_search_agent = create_react_agent(
    model = llm,
    tools = [web_search],
 
    prompt = (
        "You are a news research agent.\n\n"
        "INSTRUCTIONS:\n"
        "- Assist ONLY with news related tasks.\n"
        "- Use the web_search tool to find relevant news as instructed.\n"
        "- After you're done with your tasks, respond to the supervisor directly\n"
        "- Respond ONLY with the results of your work, do NOT include ANY other text."
    ),
    name = "news_agent"
)