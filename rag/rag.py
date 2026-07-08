from pathlib import Path
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from pypdf import PdfReader
import docx2txt

load_dotenv()

Path("uploads").mkdir(exist_ok=True)
Path("chroma_db").mkdir(exist_ok=True)

embedding = GoogleGenerativeAIEmbeddings(model="gemini-embedding-2")

vector_store = Chroma(
    collection_name="NexusGPT_DOCS",
    embedding_function=embedding,
    persist_directory="chroma_db"
)

def file_read(file_path:str):

    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        reader = PdfReader(file_path)
        text = ""

        for page in reader.pages:
            text += page.extract_text() or ""
            text += "\n"

        return text
    
    if suffix == ".docx":
        return docx2txt.process(file_path)
    
    if suffix in [".txt",".md",".py",".csv"]:
        return path.read_text(encoding="utf-8",errors="ignore")
    

    raise ValueError("Unsupported file type. Upload PDF, DOCX, TXT, MD, PY or CSV")


def add_document_to_rag(file_path:str,thread_id:str):
    text = file_read(file_path)

    if not text.strip():
        raise ValueError("No text could be extracted from this file")
    
    splitter = RecursiveCharacterTextSplitter(chunk_size=900,chunk_overlap=150)
    chunks = splitter.split_text(text)

    docs = [
        Document(page_content=chunk,metadata={"thread_id":thread_id,"source":Path(file_path).name}) for chunk in chunks
    ]

    vector_store.add_documents(docs)

    return {
        "filename":Path(file_path).name,
        "chunks":len(docs)
    }

def retrieve_from_rag(query:str,thread_id:str,k:int=4):

    docs = vector_store.similarity_search(query,k=k,filter={"thread_id":thread_id})

    if not docs:
        return "No relevant document content found"
    
    results = []

    for i, doc in enumerate(docs,start=1):
        source = doc.metadata.get("source","Uploaded Document")
        results.append(
            f"[Source {i}: {source}]\n{doc.page_content}"
        )

    return "\n\n".join(results)