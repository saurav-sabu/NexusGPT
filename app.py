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

app = FastAPI(title="NexusGPT API")

# Ensure required directories exist
Path("uploads").mkdir(exist_ok=True)
Path("./data").mkdir(exist_ok=True)

# Initialize Database
init_db()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None
    model_name: str | None = None

@app.get("/")
def read_root():
    return {"status": "ok", "app": "NexusGPT API"}

@app.get("/api/conversations")
def get_conversations():
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
    try:
        thread_id = payload.thread_id or str(uuid.uuid4())
        message = payload.message
        model_name = payload.model_name
        
        # Set thread_id globally for tools
        set_current_thread_id(thread_id)
        
        # Create/Update conversation and save human message
        create_or_update_conversation(thread_id, first_message=message)
        save_chat_message(thread_id, "user", message)
        
        # Retrieve agent
        agent = get_agent(model_name)
        
        # Run agent
        config = {"configurable": {"thread_id": thread_id}}
        input_messages = {"messages": [HumanMessage(content=message)]}
        
        # Run agent graph
        response = agent.invoke(input_messages, config=config)
        
        # Retrieve agent's output response
        ai_message = response["messages"][-1]
        response_text = extract_text_content(ai_message.content)
        
        # Save assistant's message to db
        save_chat_message(thread_id, "assistant", response_text)
        
        return {
            "response": response_text,
            "thread_id": thread_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
def upload_file(file: UploadFile = File(...), thread_id: str = Form(...)):
    try:
        # Set thread_id globally for tools
        set_current_thread_id(thread_id)
        
        # Ensure uploads directory exists
        uploads_dir = Path("uploads")
        uploads_dir.mkdir(exist_ok=True)
        
        # Save the uploaded file
        file_path = uploads_dir / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Add document to RAG
        rag_result = add_document_to_rag(str(file_path), thread_id)
        
        return {
            "status": "success",
            "filename": rag_result.get("filename"),
            "chunks": rag_result.get("chunks"),
            "thread_id": thread_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))