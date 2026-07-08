from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import declarative_base, sessionmaker, Mapped, mapped_column
from sqlalchemy import create_engine, Integer, String, Text, DateTime

Path("./data").mkdir(exist_ok=True)

DATABASE_URL = "sqlite:///data/chatbot_memory.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread":False}
)

sessionLocal = sessionmaker(bind=engine,autoflush=False,autocommit=False)
Base = declarative_base()

class Conversation(Base):

    __tablename__  = "conversations"

    id: Mapped[int] = mapped_column(Integer,primary_key=True,index=True)
    thread_id: Mapped[str] = mapped_column(String(100),unique=True,index=True)
    title: Mapped[str] = mapped_column(String(100), default="New Chat")
    created_at: Mapped[datetime] = mapped_column(DateTime,default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime,default=datetime.utcnow)


class ChatMessage(Base):

    __tablename__  = "chat_messages"

    id: Mapped[int] = mapped_column(Integer,primary_key=True,index=True)
    thread_id: Mapped[str] = mapped_column(index=True)
    role: Mapped[str] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime,default=datetime.utcnow)


class LongTermMemory(Base):

    __tablename__  = "long_term_memory"

    id: Mapped[int] = mapped_column(Integer,primary_key=True,index=True)
    thread_id: Mapped[str] = mapped_column(String(100),index=True)
    memory: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime,default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def create_or_update_conversation(thread_id:str,first_message:str|None = None):
    db = sessionLocal()

    try:
        conversation = db.query(Conversation).filter(Conversation.thread_id == thread_id).first()

        if not conversation:
            title = "New Chat"

            if first_message:
                title = first_message.strip()[:40]

                if len(first_message.strip()) > 40:
                    title += "..."

            conversation = Conversation(
                thread_id=thread_id,
                title = title
            )

            db.add(conversation)

        else:

            conversation.updated_at = datetime.utcnow()

        db.commit()

    finally:
        db.close()

def list_conversation():

    db = sessionLocal()

    try:
        return db.query(Conversation).order_by(Conversation.updated_at.desc()).all()
    
    finally:
        db.close()

def save_chat_message(thread_id:str,role:str,content:str):

    db = sessionLocal()

    try:

        msg = ChatMessage(
            thread_id=thread_id,
            role=role,
            content=content
        )

        db.add(msg)

        conversation = db.query(Conversation).filter(Conversation.thread_id == thread_id).first()

        if conversation:
            conversation.updated_at = datetime.utcnow()

        db.commit()

    finally:
        db.close()


def get_chat_history(thread_id:str):
    db = sessionLocal()

    try:
        return db.query(ChatMessage).filter(ChatMessage.thread_id == thread_id).order_by(ChatMessage.created_at.asc()).all()

    finally:
        db.close()

def save_memory(thread_id:str,memory:str):

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


def search_memory(thread_id:str,query:str):

    db = sessionLocal()

    try:
        memories = db.query(LongTermMemory).filter(LongTermMemory.thread_id == thread_id).order_by(LongTermMemory.created_at.desc()).limit(20).all()

        if not memories:
            return "No saved nenory found"
        
        return "\n".join([f"- {m.memory}" for m in memories])
    
    finally:
        db.close()
