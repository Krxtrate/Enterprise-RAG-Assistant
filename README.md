# 🤖 AdCounty AI Assistant

> An enterprise-grade AI Assistant powered by Retrieval-Augmented Generation (RAG), designed to deliver fast, accurate, and context-aware responses from company knowledge. Runs on either a hosted LLM via the Hugging Face Inference API (no GPU or download required) a fully local model via Ollama.

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
- 🤖 LLM Inference via Hugging Face Inference API (default) or local Ollama (Llama 3.1)
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
- Hugging Face Inference API / Ollama
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
   Hugging Face Inference API  (or local Ollama)
                   │
                   ▼
             AI Response
```

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
│   ├── services/
│   │   ├── chroma.py
│   │   ├── hf.py          # Hugging Face Inference API client (Integrated currently)
│   │   ├── ollama.py       # Optional local inference client
│   │   └── mcp_server.py
│   ├── prompts/
│   └── database/
│
├── frontend/
│
├── data/
│   ├── knowledge/
│   └── smalltalk/
│
├── scripts/
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

# Choose ONE inference backend:

# Option A — Hugging Face Inference API (recommended, no GPU/download needed)
HF_API_TOKEN=your_huggingface_token_here
HF_MODEL=meta-llama/Llama-3.1-8B-Instruct

# Option B — Local Ollama (requires Ollama installed + model downloaded)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

> **Getting a Hugging Face token:** create a free account at [huggingface.co](https://huggingface.co), generate a token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens), and request access to the Llama 3.1 model page (approval is usually instant).

### 5. Build the knowledge base

```bash
python -m scripts.scrape      # scrape source content into PostgreSQL
python -m scripts.ingest      # chunk content into the chunks table
python -m scripts.embedder    # embed chunks into ChromaDB
```

### 6A. Run with Hugging Face Inference API (default, no extra setup)

```bash
uvicorn chatbot.app:app --reload
```

### 6B. Run with local Ollama instead

```bash
ollama serve
ollama pull llama3.1:8b
```

Then update `chatbot/services/__init__.py` to import from `ollama.py` instead of `hf.py`, and run:

```bash
uvicorn chatbot.app:app --reload
```

### 7. Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 🎯 Key Highlights

- ✅ Enterprise-ready RAG architecture
- ✅ Runs with zero local GPU requirement via Hugging Face Inference API
- ✅ Optional fully local inference via Ollama for offline/private use
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