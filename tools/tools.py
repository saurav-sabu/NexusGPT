import math
from langchain_core.tools import tool
from langchain_tavily import TavilySearch
from dotenv import load_dotenv
import numexpr
from database.database import save_memory, search_memory
from rag.rag import retrieve_from_rag

load_dotenv()

CURRENT_THREAD_ID = "default"

def set_current_thread_id(thread_id:str):
    global CURRENT_THREAD_ID
    CURRENT_THREAD_ID = thread_id


web_search_tool = TavilySearch(
    max_results = 5,
    topic="general",
    search_depth="advanced",
    description="""
Search the web for current information.

Use this tool for:
- latest news
- current events
- today's information
- live information
- recent updates
- current prices
- anything after your knowledge cutoff
"""
)

from langchain_core.tools import tool
import numexpr


@tool
def calculator(expression: str) -> str:
    """
    Evaluate a mathematical expression and return the result.

    This tool supports basic arithmetic operations including:
    - Addition (+)
    - Subtraction (-)
    - Multiplication (*)
    - Division (/)
    - Exponentiation (**)
    - Modulus (%)
    - Parentheses for grouping

    Args:
        expression: A valid mathematical expression as a string.

    Returns:
        The evaluated result as a string.

    Examples:
        calculator("2 + 3 * 4") -> "14"
        calculator("(10 + 5) / 3") -> "5.0"
        calculator("2 ** 8") -> "256"
    """
    try:
        result = numexpr.evaluate(expression).item()
        return str(result)
    except Exception as e:
        return f"Calculation error: {e}"
    
@tool
def remember_this(memory: str) -> str:
    """
    Save an important piece of information about the user for future conversations.

    Use this tool only when the user explicitly asks you to remember something
    or shares information that should be stored for future reference.

    Args:
        memory: The information to save.

    Returns:
        A confirmation message indicating whether the memory was saved successfully.
    """
    return save_memory(
        thread_id=CURRENT_THREAD_ID,
        memory=memory
    )


@tool
def recall_memory(query: str) -> str:
    """
    Search previously saved memories to answer questions about the user.

    Use this tool when the user asks about something they previously shared,
    such as preferences, personal details, or facts that may have been saved.

    Args:
        query: A search query describing the memory to retrieve.

    Returns:
        Relevant saved memories matching the query.
    """
    return search_memory(
        thread_id=CURRENT_THREAD_ID,
        query=query
    )


@tool
def search_uploaded_document(query: str) -> str:
    """
    Search the uploaded documents using Retrieval-Augmented Generation (RAG).

    Use this tool whenever the user's question requires information from
    documents they have uploaded. Do not use it for general knowledge or
    current events.

    Args:
        query: The question or search query related to the uploaded documents.

    Returns:
        The most relevant information retrieved from the uploaded documents.
    """
    return retrieve_from_rag(
        query=query,
        thread_id=CURRENT_THREAD_ID
    )

tools = [
    calculator,
    remember_this,
    search_uploaded_document,
    recall_memory,
    web_search_tool
]