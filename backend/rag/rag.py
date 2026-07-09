"""
NexusGPT RAG (Retrieval-Augmented Generation) Module.

This module handles document parsing, text splitting, embedding generation,
and vector database interactions (using Chroma DB) to allow the agent to 
upload and query context documents dynamically.
"""

from pathlib import Path
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from pypdf import PdfReader
import docx2txt

# Load environment variables
load_dotenv()

# Create directories for document uploads and local Chroma database persistence
Path("uploads").mkdir(exist_ok=True)
Path("chroma_db").mkdir(exist_ok=True)

# Initialize Google's Gemini Embedding model
embedding = GoogleGenerativeAIEmbeddings(model="gemini-embedding-2")

# Configure the Chroma Vector Store collection
vector_store = Chroma(
    collection_name="NexusGPT_DOCS",
    embedding_function=embedding,
    persist_directory="chroma_db"
)


def file_read(file_path: str) -> str:
    """
    Read and extract the textual content of a file based on its extension.

    Supports PDF, DOCX, TXT, MD, PY, and CSV file formats.

    Args:
        file_path: The filesystem path to the target document.

    Returns:
        The extracted plain text content of the document.

    Raises:
        ValueError: If the file extension/type is not supported.
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    # Parse PDF files page by page
    if suffix == ".pdf":
        reader = PdfReader(file_path)
        text = ""

        for page in reader.pages:
            text += page.extract_text() or ""
            text += "\n"

        return text
    
    # Parse Microsoft Word files
    if suffix == ".docx":
        return docx2txt.process(file_path)
    
    # Read standard plain text, markdown, python, and spreadsheet CSV files
    if suffix in [".txt", ".md", ".py", ".csv"]:
        return path.read_text(encoding="utf-8", errors="ignore")
    
    raise ValueError("Unsupported file type. Upload PDF, DOCX, TXT, MD, PY or CSV")


def add_document_to_rag(file_path: str, thread_id: str) -> dict:
    """
    Ingest a document into the RAG system.

    Extracts text, splits it into semantic chunks with overlap, assigns
    metadata fields (specifically tracking the thread_id for conversation context scope),
    and indexes the chunks inside the Chroma database.

    Args:
        file_path: Path of the uploaded document file.
        thread_id: Thread ID to isolate document scope to a specific conversation.

    Returns:
        A dictionary containing the filename and number of created chunks.

    Raises:
        ValueError: If the document contains no extractable text content.
    """
    text = file_read(file_path)

    if not text.strip():
        raise ValueError("No text could be extracted from this file")
    
    # Configure text chunk size and overlap for context window fitting
    splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=150)
    chunks = splitter.split_text(text)

    # Convert chunks into LangChain Document objects with thread filters
    docs = [
        Document(
            page_content=chunk,
            metadata={"thread_id": thread_id, "source": Path(file_path).name}
        ) for chunk in chunks
    ]

    # Add embedded documents to Chroma DB
    vector_store.add_documents(docs)

    return {
        "filename": Path(file_path).name,
        "chunks": len(docs)
    }


def retrieve_from_rag(query: str, thread_id: str, k: int = 4) -> str:
    """
    Retrieve relevant document snippets using vector similarity search.

    Limits results to documents uploaded specifically under the active thread_id.

    Args:
        query: The user search query string.
        thread_id: The unique thread ID context for metadata filtering.
        k: The maximum number of relevant documents to retrieve.

    Returns:
        A concatenated string showing numbered sources and matching document snippets.
    """
    # Query vector store with thread metadata filter
    docs = vector_store.similarity_search(query, k=k, filter={"thread_id": thread_id})

    if not docs:
        return "No relevant document content found"
    
    results = []

    # Format the retrieved documents into structured text blocks
    for i, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source", "Uploaded Document")
        results.append(
            f"[Source {i}: {source}]\n{doc.page_content}"
        )

    return "\n\n".join(results)