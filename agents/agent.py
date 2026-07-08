import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_google_genai import ChatGoogleGenerativeAI

from tools.tools import tools

load_dotenv()

Path("./data").mkdir(exist_ok=True)

DEFAULT_MODEL = os.getenv("GOOGLE_MODEL","gemini-2.5-flash")

ALLOWED_MODELS = {
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.5-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
}

SYSTEM_PROMPT = """
You are a helpful Agentic AI assistant named NexusGPT similar to ChatGPT.

You can:
1. Answer normal questions.
2. Use tools when needed.
3. Search uploaded documents using the RAG tool.
4. Search the web for latest/current information using Tavily Search.
5. Remember important user information using the memory tool.
6. Recall memory when useful.
7. Use calculator for math.

Rules:
- If the user asks about latest news, current events, recent updates, today's information, current prices, use web search.
- If the user asks about an uploaded document, use search_uploaded_document.
- If the user asks you to remember something, use remember_this.
- If the user asks about previous preferences or saved facts, use recall_memory.
- Use calculator for math questions.
- When using web search, summarize clearly and mention that the answer is based on web search results.
- Be clear, helpful, and concise.
"""

def normalize_model_name(model_name:str | None):

    if not model_name:
        return DEFAULT_MODEL
    
    model_name = model_name.strip()

    if model_name not in ALLOWED_MODELS:
        return DEFAULT_MODEL
    
    return model_name

def build_agent(model_name:str):

    selected_model = normalize_model_name(model_name)

    llm = ChatGoogleGenerativeAI(
        model=selected_model,
        temperature = 0.3,
        streaming=True
    )

    llm_with_tools = llm.bind_tools(tools)

    def chatbot_node(state:MessagesState):

        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]

        response = llm_with_tools.invoke(messages)


        return {
            "messages":[response]
        }
    
    tool_node = ToolNode(tools)

    workflow = StateGraph(MessagesState)

    workflow.add_node("chatbot",chatbot_node)
    workflow.add_node("tools",tool_node)

    workflow.add_edge(START,"chatbot")
    workflow.add_conditional_edges("chatbot",tools_condition)
    workflow.add_edge("tools","chatbot")

    conn = sqlite3.connect(
        "./data/langgraph_checkpoints.sqlite",
        check_same_thread=False
    )

    checkpointer = SqliteSaver(conn)

    checkpointer = SqliteSaver(conn)

    return workflow.compile(checkpointer=checkpointer)


__AGENT_CACHE =  {}

def get_agent(model_name:str|None=None):

    selected_model = normalize_model_name(model_name)

    if selected_model not in __AGENT_CACHE:
        __AGENT_CACHE[selected_model] = build_agent(selected_model)

    return __AGENT_CACHE[selected_model]

