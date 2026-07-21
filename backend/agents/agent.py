"""
NexusGPT Agent Module.

This module defines and constructs the agent workflow graph using LangGraph.
It manages model selection, initializes the language model with bound tools,
builds the execution graph, and handles state persistence using an SQLite checkpoint saver.
"""

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

# Load environment variables from .env file
load_dotenv()

# Ensure the local data directory exists for SQLite database checkpoint storage
Path("./data").mkdir(exist_ok=True)

# Define fallback/default model and the whitelist of supported Gemini models
DEFAULT_MODEL = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")

ALLOWED_MODELS = {
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.5-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
}

# The system prompt instructs NexusGPT on capabilities, rules, and tool usage guidelines.
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
8. Shorten long URLs using the URL shortening tool.
9. Generate UUIDs (Universally Unique Identifiers) using the UUID generation tool.
10. Fetch the latest stock price for publicly traded companies.
11. Retrieve the current weather for any city.

Rules:
- If the user asks about latest news, current events, recent updates, today's information, current prices, use web search.
- If the user asks about an uploaded document, use search_uploaded_document.
- If the user asks you to remember something, use remember_this.
- If the user asks about previous preferences or saved facts, use recall_memory.
- Use calculator for math questions.
- If the user asks to shorten a URL or generate a short link, use shorten_url.
- If the user asks to generate a UUID, unique identifier, UUID v4, random UUID, or GUID, use the generate_uuid tool.
- If the user asks for the current stock price, latest share price, stock quote, or market price of a company or stock symbol (e.g., AAPL, TSLA, MSFT, NVDA, GOOGL), use the get_stock_price tool.
- If the user asks about the current weather, temperature, humidity, wind speed, or weather conditions for a city or location, use the get_weather tool.
- When using web search, summarize clearly and mention that the answer is based on web search results.
- Be clear, helpful, and concise.
"""


def normalize_model_name(model_name: str | None) -> str:
    """
    Validate and normalize the requested model name.

    If the provided model name is empty, invalid, or unsupported,
    it falls back to the configured DEFAULT_MODEL.

    Args:
        model_name: The name of the model requested by the client.

    Returns:
        A validated model name string.
    """
    if not model_name:
        return DEFAULT_MODEL
    
    model_name = model_name.strip()

    if model_name not in ALLOWED_MODELS:
        return DEFAULT_MODEL
    
    return model_name


def build_agent(model_name: str):
    """
    Construct, configure, and compile the LangGraph workflow agent.

    This function sets up the Gemini Chat Model, binds the registered tools,
    defines the message handler node, sets up the state transitions, and
    attaches an SQLite checkpoint saver for persistent multi-turn chat history.

    Args:
        model_name: The normalized name of the Gemini model to use.

    Returns:
        CompiledStateGraph: A compiled LangGraph workflow state machine ready to run.
    """
    selected_model = normalize_model_name(model_name)

    # Initialize the Gemini Chat model with streaming enabled and temperature control
    llm = ChatGoogleGenerativeAI(
        model=selected_model,
        temperature=0.3,
        streaming=True
    )

    # Bind the external tools (RAG, search, memory, calculator) to the LLM
    llm_with_tools = llm.bind_tools(tools)

    def chatbot_node(state: MessagesState):
        """
        State graph node that handles the conversation turn.

        Prepends the SYSTEM_PROMPT instructions to the chat history,
        invokes the LLM with tools, and returns the response message.
        """
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        response = llm_with_tools.invoke(messages)

        return {
            "messages": [response]
        }
    
    # Prebuilt node that executes tools requested by the LLM
    tool_node = ToolNode(tools)

    # Initialize state graph with the predefined MessagesState structure
    workflow = StateGraph(MessagesState)

    # Add the processing and execution nodes
    workflow.add_node("chatbot", chatbot_node)
    workflow.add_node("tools", tool_node)

    # Configure graph edges and conditional routing rules
    workflow.add_edge(START, "chatbot")
    # Route to 'tools' node or END depending on if the LLM output contains tool calls
    workflow.add_conditional_edges("chatbot", tools_condition)
    # Loop back to the chatbot after executing tools to process tool outputs
    workflow.add_edge("tools", "chatbot")

    # Set up SQLite checkpointer to persist conversation thread states
    conn = sqlite3.connect(
        "./data/langgraph_checkpoints.sqlite",
        check_same_thread=False
    )
    checkpointer = SqliteSaver(conn)

    # Compile the workflow with state persistence checkpointer
    return workflow.compile(checkpointer=checkpointer)


# Global in-memory cache to store compiled agents for each model variant
__AGENT_CACHE = {}


def get_agent(model_name: str | None = None):
    """
    Retrieve or create the compiled agent instance for the specified model.

    Implements a lazy loading caching pattern to reuse already built and compiled agents,
    minimizing compilation overhead on successive requests.

    Args:
        model_name: The requested model name, or None to use default.

    Returns:
        CompiledStateGraph: The compiled state graph agent instance.
    """
    selected_model = normalize_model_name(model_name)

    if selected_model not in __AGENT_CACHE:
        __AGENT_CACHE[selected_model] = build_agent(selected_model)

    return __AGENT_CACHE[selected_model]


