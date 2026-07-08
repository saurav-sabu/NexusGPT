"""
NexusGPT Database Module.

This module configures the database engine, sessions, and schema models using SQLAlchemy.
It provides functions for persistent storage and retrieval of conversation metadata,
chat histories, and agent long-term memory records.
"""

from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import declarative_base, sessionmaker, Mapped, mapped_column
from sqlalchemy import create_engine, Integer, String, Text, DateTime

# Ensure the SQLite data directory exists
Path("./data").mkdir(exist_ok=True)

# Database connection URL for the local SQLite database
DATABASE_URL = "sqlite:///data/chatbot_memory.db"

# Create the SQLAlchemy engine with multi-threading compatibility settings for SQLite
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Create a thread-local session factory for database transactions
sessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Declarative base class for SQLAlchemy models
Base = declarative_base()


class Conversation(Base):
    """
    SQLAlchemy model representing a conversation thread session.

    Stores unique thread identifiers, auto-generated or custom titles,
    and tracking timestamps.
    """

    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    thread_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(100), default="New Chat")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    """
    SQLAlchemy model representing an individual chat message in a thread.

    Stores the sender role (e.g., 'user', 'assistant'), text content,
    and a relation link through thread_id.
    """

    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    thread_id: Mapped[str] = mapped_column(index=True)
    role: Mapped[str] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class LongTermMemory(Base):
    """
    SQLAlchemy model representing long-term memory snippets saved by the agent.

    Allows the agent to persist user preferences or key facts across multiple
    different threads or sessions.
    """

    __tablename__ = "long_term_memory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    thread_id: Mapped[str] = mapped_column(String(100), index=True)
    memory: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


def init_db():
    """
    Initialize the database by creating all tables defined in the schema.
    """
    Base.metadata.create_all(bind=engine)


def create_or_update_conversation(thread_id: str, first_message: str | None = None):
    """
    Create a new conversation session record or update the timestamp of an existing one.

    If creating a new conversation, the title is automatically generated from
    the first few characters of the user's initial message.

    Args:
        thread_id: The unique identifier for the conversation thread.
        first_message: The initial message of the thread used to generate the title.
    """
    db = sessionLocal()

    try:
        conversation = db.query(Conversation).filter(Conversation.thread_id == thread_id).first()

        if not conversation:
            title = "New Chat"

            if first_message:
                # Truncate title to first 40 characters
                title = first_message.strip()[:40]

                if len(first_message.strip()) > 40:
                    title += "..."

            conversation = Conversation(
                thread_id=thread_id,
                title=title
            )

            db.add(conversation)

        else:
            # Update the last activity timestamp
            conversation.updated_at = datetime.utcnow()

        db.commit()

    finally:
        db.close()


def list_conversation():
    """
    Fetch all conversations ordered by last update time descending.

    Returns:
        list[Conversation]: A list of Conversation model instances.
    """
    db = sessionLocal()

    try:
        return db.query(Conversation).order_by(Conversation.updated_at.desc()).all()
    
    finally:
        db.close()


def save_chat_message(thread_id: str, role: str, content: str):
    """
    Persist a chat message to database and update conversation's updated_at timestamp.

    Args:
        thread_id: The unique thread ID identifier.
        role: The role of the sender (e.g., 'user', 'model', 'assistant').
        content: The body text of the chat message.
    """
    db = sessionLocal()

    try:
        msg = ChatMessage(
            thread_id=thread_id,
            role=role,
            content=content
        )

        db.add(msg)

        # Update parent conversation session update timestamp
        conversation = db.query(Conversation).filter(Conversation.thread_id == thread_id).first()

        if conversation:
            conversation.updated_at = datetime.utcnow()

        db.commit()

    finally:
        db.close()


def get_chat_history(thread_id: str):
    """
    Retrieve all persisted chat messages for a specific conversation thread.

    Args:
        thread_id: The unique identifier for the conversation thread.

    Returns:
        list[ChatMessage]: Messages ordered chronologically by creation timestamp.
    """
    db = sessionLocal()

    try:
        return db.query(ChatMessage).filter(ChatMessage.thread_id == thread_id).order_by(ChatMessage.created_at.asc()).all()

    finally:
        db.close()


def save_memory(thread_id: str, memory: str):
    """
    Persist a long-term memory snippet to the database for subsequent retrieval.

    Args:
        thread_id: The active thread ID context.
        memory: The structured knowledge or facts to store.

    Returns:
        str: Success feedback message.
    """
    db = sessionLocal()

    try:
        item = LongTermMemory(
            thread_id=thread_id,
            memory=memory
        )

        db.add(item)
        db.commit()
        return "Memory Saved Sucessfully"
    
    finally:
        db.close()


def search_memory(thread_id: str, query: str):
    """
    Search and retrieve the list of most recent memories recorded under a thread.

    Args:
        thread_id: The thread ID context to retrieve memories for.
        query: Unused parameter kept for future query-based search expansion.

    Returns:
        str: A concatenated list of memories or a fallback message if empty.
    """
    db = sessionLocal()

    try:
        memories = db.query(LongTermMemory).filter(LongTermMemory.thread_id == thread_id).order_by(LongTermMemory.created_at.desc()).limit(20).all()

        if not memories:
            return "No saved nenory found"
        
        return "\n".join([f"- {m.memory}" for m in memories])
    
    finally:
        db.close()

