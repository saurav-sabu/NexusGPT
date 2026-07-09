# NexusGPT - Agentic Workspace

NexusGPT is a modern, responsive, and full-featured AI chat assistant featuring a dark-themed ReactJS frontend modeled after ChatGPT and a LangGraph-powered FastAPI backend. It supports advanced features such as multi-turn conversations, system memory, Tavily Web Search, and local document indexing (RAG) using Chroma DB.

---

## Project Structure

The codebase is organized into two primary workspaces:

```
NexusGPT/
├── backend/                # Python FastAPI Backend
│   ├── app.py              # FastAPI server and endpoint routing
│   ├── main.py             # LangGraph diagnostic CLI entry
│   ├── requirements.txt    # Python dependencies list
│   ├── pyproject.toml      # Project configurations
│   ├── .env                # Environment keys (Google Gemini, Tavily API keys)
│   ├── agents/             # LangGraph workflow state machine definitions
│   ├── database/           # SQLite memory and session logs persistence layer
│   ├── rag/                # Chroma DB vector database ingestion & retrieval
│   └── tools/              # Agent tools (Tavily search, calculator, memory)
├── frontend/               # Vite + ReactJS Frontend Client
│   ├── package.json        # Node.js dependencies
│   ├── vite.config.js      # Vite dev and build settings
│   ├── index.html          # Web application template
│   └── src/                # React source code (components, styles, API utils)
└── .venv/                  # Root Python virtual environment
```

---

## Key Features

1. **ChatGPT UI Experience**: Responsive dark theme built using Vanilla CSS. Includes a collapsible sidebar for managing conversation history and a sleek model picker.
2. **Model Selection**: Switch dynamically between different Google Gemini models (`gemini-2.5-flash`, `gemini-2.5-pro`, etc.) in the header.
3. **Retrieval-Augmented Generation (RAG)**: Attachment button (paperclip) to upload files (`.txt`, `.pdf`, `.docx`). Uploaded documents are parsed, chunked, and embedded into Chroma DB to answer questions scoped to that conversation.
4. **Agentic Core Tools**:
   - **Tavily Web Search**: Automatically queries the live web for current events and recent updates.
   - **Long-term Memory**: Remembers personal user facts and preferences upon request across conversation sessions.
   - **Calculator**: Evaluates mathematical expressions using `numexpr`.

---

## Getting Started

Follow these steps to launch both services on your local machine:

### Prerequisites
- **Node.js** (v18 or higher recommended)
- **Python** (v3.12 recommended)
- **Google Gemini API Key** and **Tavily API Key** added to `backend/.env`

---

### Setup Instructions

#### 1. Start the Backend Server
1. Open a terminal in the root workspace folder.
2. Activate the virtual environment:
   ```bash
   .venv\Scripts\activate
   ```
3. Navigate to the `backend/` folder and run Uvicorn:
   ```bash
   cd backend
   python -m uvicorn app:app --reload
   ```
   *The API will start running on [http://localhost:8000](http://localhost:8000).*

#### 2. Start the Frontend client
1. Open a separate terminal in the root workspace folder.
2. Navigate to the `frontend/` folder:
   ```bash
   cd frontend
   ```
3. Install dependencies (if not already done):
   ```bash
   npm install
   ```
4. Run the development server:
   ```bash
   npm run dev
   ```
   *The UI web page will launch on [http://localhost:5173/](http://localhost:5173/).*
