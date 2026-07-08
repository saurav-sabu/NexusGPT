"""
NexusGPT FastAPI Backend Application.

This module acts as the primary web server interface for NexusGPT.
It exposes REST endpoints for conversation listing, message history retrieval,
multi-turn interactive chat (using LangGraph execution), and document upload (for local RAG processing).
"""

import json
import uuid
import shutil
from pathlib import Path
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from agents.agent import get_agent
from database.database import *
from rag.rag import add_document_to_rag
from tools.tools import set_current_thread_id

# Instantiate FastAPI application
app = FastAPI(title="NexusGPT API")

# Ensure necessary application workspace directories exist
Path("uploads").mkdir(exist_ok=True)
Path("./data").mkdir(exist_ok=True)

# Initialize schema tables in the SQLite database
init_db()

# Enable Cross-Origin Resource Sharing (CORS) for external frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    """
    Pydantic request validation model for chat interaction.
    """
    message: str
    thread_id: str | None = None
    model_name: str | None = None


@app.get("/")
def read_root():
    """
    Root diagnostics endpoint to check API server status.
    """
    return {"status": "ok", "app": "NexusGPT API"}


@app.get("/api/conversations")
def get_conversations():
    """
    Retrieve a list of all active or saved conversation threads.

    Returns:
        A list of conversations with IDs, thread details, and timestamps.
    """
    try:
        convs = list_conversation()
        return [
            {
                "id": c.id,
                "thread_id": c.thread_id,
                "title": c.title,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None
            } for c in convs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/conversations/{thread_id}/history")
def get_history(thread_id: str):
    """
    Fetch the complete chronological chat log for a given thread.

    Args:
        thread_id: Unique string identifier for the target conversation.

    Returns:
        List of chat message logs with sender roles, content, and creation timestamps.
    """
    try:
        history = get_chat_history(thread_id)
        return [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat() if msg.created_at else None
            } for msg in history
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def extract_text_content(content) -> str:
    """
    Normalize and convert LangChain message contents into a clean text string.

    Supports simple strings, lists of message blocks, and dictionaries.

    Args:
        content: Raw output from the LangChain agent's AI message.

    Returns:
        A unified string containing the extracted text content.
    """
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict) and "text" in part:
                text_parts.append(part["text"])
        return "".join(text_parts)
    return str(content)


@app.post("/api/chat")
def chat(payload: ChatRequest):
    """
    Execute a turn of the conversation with NexusGPT agent.

    This endpoint maps incoming chat requests, registers the thread ID in tools context,
    records messages to the database history, invokes the LangGraph state machine,
    saves the agent's response, and returns it.

    Args:
        payload: Pydantic ChatRequest payload containing message and thread configurations.

    Returns:
        A dictionary containing the agent response and the conversation thread ID.
    """
    try:
        thread_id = payload.thread_id or str(uuid.uuid4())
        message = payload.message
        model_name = payload.model_name
        
        # Configure thread context globally for state-reliant tools (like memory/RAG)
        set_current_thread_id(thread_id)
        
        # Insert conversation metadata and log the user's message
        create_or_update_conversation(thread_id, first_message=message)
        save_chat_message(thread_id, "user", message)
        
        # Retrieve the requested model variant of the agent
        agent = get_agent(model_name)
        
        # Set thread configurations for LangGraph checkpointers
        config = {"configurable": {"thread_id": thread_id}}
        input_messages = {"messages": [HumanMessage(content=message)]}
        
        # Execute the agent graph loop (including potential tool usage cycles)
        response = agent.invoke(input_messages, config=config)
        
        # Extract the final textual response returned by the chatbot
        ai_message = response["messages"][-1]
        response_text = extract_text_content(ai_message.content)
        
        # Persist the chatbot's message in the database logs
        save_chat_message(thread_id, "assistant", response_text)
        
        return {
            "response": response_text,
            "thread_id": thread_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload")
def upload_file(file: UploadFile = File(...), thread_id: str = Form(...)):
    """
    Upload a document and index its contents into the RAG database for the thread.

    Receives the uploaded file via multipart/form-data request, writes it locally,
    parses it, splits it, and embeds it into Chroma vector database.

    Args:
        file: The uploaded document file object.
        thread_id: The specific thread context to bind the document scope to.

    Returns:
        A dictionary showing filename, chunk size metrics, and thread ID details.
    """
    try:
        # Establish global thread identifier context for tools
        set_current_thread_id(thread_id)
        
        # Re-ensure local upload directory exists
        uploads_dir = Path("uploads")
        uploads_dir.mkdir(exist_ok=True)
        
        # Save file to disk
        file_path = uploads_dir / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Parse and load document chunks into the Chroma DB Vector Store
        rag_result = add_document_to_rag(str(file_path), thread_id)
        
        return {
            "status": "success",
            "filename": rag_result.get("filename"),
            "chunks": rag_result.get("chunks"),
            "thread_id": thread_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))