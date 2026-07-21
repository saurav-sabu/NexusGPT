import math
from langchain_core.tools import tool
from langchain_tavily import TavilySearch
from dotenv import load_dotenv
import numexpr
from database.database import save_memory, search_memory
from rag.rag import retrieve_from_rag
import requests
import uuid
import os
import arxiv


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

@tool
def generate_uuid(version: int = 4) -> str:
    """
    Generate a Universally Unique Identifier (UUID).

    Use this tool whenever the user asks to:
    - generate a UUID
    - create a UUID
    - create a unique identifier
    - generate a UUID v1 or UUID v4

    Args:
        version: UUID version to generate.
            Supported values:
            - 1: Time-based UUID.
            - 4: Random UUID (default and recommended).

    Returns:
        A UUID string. Returns an error message if an unsupported version is requested.

    Examples:
        generate_uuid() -> "550e8400-e29b-41d4-a716-446655440000"
        generate_uuid(1) -> "f81d4fae-7dec-11d0-a765-00a0c91e6bf6"
    """
    try:
        if version == 1:
            return str(uuid.uuid1())
        elif version == 4:
            return str(uuid.uuid4())
        else:
            return "Error: Only UUID versions 1 and 4 are supported."
    except Exception as e:
        return f"Error generating UUID: {e}"

@tool
def shorten_url(url:str) -> str:
    """
    Create a shortened version of a long URL using the TinyURL service.

    Use this tool whenever the user asks to:
    - shorten a URL
    - create a short link
    - generate a TinyURL
    - make a long URL easier to share
    - convert a long web link into a shorter one

    Do not use this tool for:
    - validating URLs
    - expanding shortened URLs
    - searching the web

    Args:
        url: The original URL to be shortened. It should be a valid HTTP or HTTPS URL.

    Returns:
        The shortened TinyURL as a string. If the request fails, an error message is returned.
    """
     
    short_url = requests.get("https://tinyurl.com/api-create.php",params={"url":url}).text
    return short_url

@tool
def get_stock_price(symbol:str) -> str:
    '''
    Fetch the latest stock price for a given symbol (eg: AAPL, TSLA)
    Using Alpha vantage with API KEY in URL
    '''
    response = requests.get(f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={os.getenv("ALPHA_VANTAGE_API_KEY")}")
    result = response.json()
    return result

@tool
def get_weather(city:str) -> str:
    '''
    Get the current weather of the city
    '''
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={os.getenv("OPENWEATHER_AI_KEY")}&units=metric"
    response = requests.get(url)
    result = response.json()
    return result

@tool
def search_arxiv(query: str) -> str:
    """
    Search arXiv for research papers.

    Use this tool whenever the user asks for:
    - research papers
    - academic papers
    - arXiv papers
    - latest AI/ML papers
    - scientific publications
    - transformer, RAG, LLM, diffusion papers

    Args:
        query: Search query describing the topic.

    Returns:
        A formatted list of relevant arXiv papers.
    """

    try:
        search = arxiv.Search(
            query=query,
            max_results=5,
            sort_by=arxiv.SortCriterion.Relevance
        )

        results = []

        for paper in search.results():
            authors = ", ".join(a.name for a in paper.authors)

            results.append(
                f"""
Title: {paper.title}

Authors: {authors}

Published: {paper.published.date()}

Summary:
{paper.summary}

PDF:
{paper.pdf_url}
"""
            )

        if not results:
            return "No papers found."

        return "\n\n" + "=" * 80 + "\n\n".join(results)

    except Exception as e:
        return f"Error searching arXiv: {e}"

tools = [
    calculator,
    remember_this,
    search_uploaded_document,
    recall_memory,
    web_search_tool,
    shorten_url,
    generate_uuid,
    get_stock_price,
    get_weather
]