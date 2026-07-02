# 🤖 AdCounty AI Assistant

An enterprise-grade AI Assistant powered by Retrieval-Augmented Generation (RAG), designed to deliver fast, accurate, and context-aware responses from company knowledge. Tries the Hugging Face Inference API first for fast, GPU-free responses, and automatically falls back to a local Ollama model if the free tier is rate-limited — with zero manual intervention.

Built during my Software Development Internship at **AdCounty Media**.

---

## 🚀 Overview

AdCounty AI Assistant is an intelligent enterprise chatbot that enables employees and stakeholders to interact with company knowledge naturally.

Instead of relying solely on a Large Language Model's built-in knowledge, the assistant retrieves relevant information from an indexed knowledge base before generating responses, ensuring accurate, up-to-date, and context-aware answers.

The assistant supports product information, leadership queries, comparisons, company information, technical documentation, conversational follow-ups, and much more.

---

## ✨ Features

- 🧠 Retrieval-Augmented Generation (RAG)
- 🔍 Semantic Search with ChromaDB
- 🤖 Dual-backend LLM inference — Hugging Face Inference API (primary, ~3-5s responses) with automatic failover to local Ollama (Llama 3.1) if the free tier is rate-limited
- 🔄 Self-healing — automatically retries the Hugging Face API every 24 hours to recover from fallback
- 🟡 Frontend notice banner when running on the local fallback, so users know to expect slower responses
- 🎯 Intelligent Intent Detection
- 💬 Multi-turn Conversation Support
- 🌐 Automated Website Scraping (accordion, tab, and dropdown-aware)
- ⚡ FastAPI Backend
- 🎨 Responsive React Frontend
- 📊 Product Comparison Engine
- 👥 Leadership & Company Information Retrieval
- 😊 Small Talk Detection
- 🧩 Modular & Scalable Architecture
- 🔌 MCP Server support for external tool integration

---

## 🛠 Tech Stack

### Backend
- Python
- FastAPI
- ChromaDB
- Hugging Face Inference API + local Ollama (automatic failover)
- Sentence Transformers
- Transformers
- Playwright
- BeautifulSoup
- PostgreSQL + SQLAlchemy

### Frontend
- React
- JavaScript
- CSS

### AI & Machine Learning
- Retrieval-Augmented Generation (RAG)
- Semantic Search
- Embeddings
- Intent Classification

---

## ⚙️ System Architecture

```text
                 User
                   │
                   ▼
          React Frontend
                   │
                   ▼
          FastAPI Backend
                   │
                   ▼
        Intent Detection Engine
                   │
                   ▼
      Conversation & Context Router
                   │
                   ▼
      ChromaDB Semantic Retrieval
                   │
                   ▼
          Prompt Construction
                   │
                   ▼
       ┌───────────────────────┐
       │   LLM Failover Router │
       └───────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
  Hugging Face API      Local Ollama
  (tried first)      (automatic fallback
                       if HF fails/rate-limited)
                   │
                   ▼
             AI Response
        (+ notice if on fallback)
```

---

## 🔁 How the Failover Works

1. Every request tries the **Hugging Face Inference API** first — fast (~3-5s) and requires no GPU.
2. If HF fails (rate limit, timeout, server error), the request automatically retries against **local Ollama** running on the server.
3. The response includes a `notice` field when served by the fallback, which the frontend surfaces as a banner: *"Running on local inference — the free Hugging Face tier limit was reached, so responses may be slower than usual."*
4. The backend automatically retries HF every 24 hours in case the rate limit window has reset — no restart or manual switch needed.
5. `GET /health` reports which backend is currently active (`huggingface` or `ollama`) at any time.

This means the assistant stays available and fast under normal conditions, and gracefully degrades to local inference during high traffic — without anyone needing to intervene.

---

## 🧠 Supported Capabilities

- 📦 Product Information
- ⚖️ Product Comparisons
- 🏢 Company Overview
- 👥 Leadership Information
- 💡 Technical Documentation
- 📚 Knowledge Base Search
- 🔄 Follow-up Questions
- 🌐 General Information
- 😊 Natural Conversation

---

## 📁 Project Structure

```text
Enterprise-RAG-Assistant
│
├── chatbot/
│   ├── app.py
│   ├── config.py
│   ├── models.py
│   ├── core/
│   ├── prompts/
│   ├── tools/                # Future MCP tools 
│   ├── database/
│   └── services/
│        ├── chroma.py
│        ├── llm.py           # Failover router — app.py imports ONLY from here
│        ├── hf.py            # Hugging Face Inference API client
│        ├── ollama.py        # Local Ollama client (fallback)
│        └── mcp_server.py
│
├── frontend/
│
├── data/
│   ├── knowledge/
│   └── smalltalk/
│
├── scripts/
│   ├── scrape.py
│   ├── ingest.py
│   └── embedder.py
│
├── tests/
│
├── .env.example
├── requirements.txt
└── README.md
```

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Krxtrate/AdCounty-AI-Assistant
cd AdCounty-AI-Assistant
```

### 2. Set up the backend environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
playwright install
```

### 3. Set up PostgreSQL

Create a local PostgreSQL database and update the connection string in your `.env` file (see below).

### 4. Configure environment variables

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

```env
# .env
DATABASE_URL=postgresql://user:password@localhost:5432/adcounty_chatbot

# Hugging Face Inference API — tried first on every request.
# No GPU or model download required.
# Get a token at https://huggingface.co/settings/tokens
# Request access to the model at https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct
HF_API_TOKEN=your_huggingface_token_here
HF_MODEL=meta-llama/Llama-3.1-8B-Instruct

# Local Ollama — automatic fallback if HF fails or hits rate limits.
# Must be installed and running for the fallback to actually work.
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

> **Note:** Both backends are configured simultaneously — there's no toggle to set. The app tries HF first on every request and only falls back to Ollama automatically if HF is unavailable. If you don't have Ollama installed, the app still runs fine as long as HF is reachable; the fallback simply won't have anywhere to go if HF ever fails.

### 5. (Optional but recommended) Install and start Ollama for fallback coverage

```bash
ollama serve
ollama pull llama3.1:8b
```

### 6. Build the knowledge base

```bash
python -m scripts.scrape      # scrape source content into PostgreSQL
python -m scripts.ingest      # chunk content into the chunks table
python -m scripts.embedder    # embed chunks into ChromaDB
```

### 7. Run the backend

```bash
uvicorn chatbot.app:app --reload
```

Check `GET http://localhost:8000/health` at any time to see which backend is currently serving requests.

### 8. Frontend (in a separate terminal)

```bash
cd frontend
npm install
npm run dev
```

---

## 🎯 Key Highlights

- ✅ Enterprise-ready RAG architecture
- ✅ Fast hosted inference via Hugging Face Inference API, with zero local GPU requirement
- ✅ Automatic, self-healing failover to local Ollama — no manual switching, no downtime
- ✅ Frontend transparency — users see a banner when running on the slower local fallback
- ✅ Fast semantic document retrieval
- ✅ Context-aware responses
- ✅ Conversation memory support
- ✅ Product recommendation & comparison
- ✅ Knowledge ingestion pipeline with accordion/tab-aware scraping
- ✅ Clean modular architecture

---

## 📈 Future Improvements

- 🔐 Authentication & User Roles
- 🧠 Hybrid Retrieval (BM25 + Vector Search)
- ☁️ Cloud Deployment
- 🔄 Streaming Responses
- 🗂️ Multi-document Collections
- 📝 Conversation History Persistence

---

## 👨‍💻 Developed By

**Kritarth Sharan**