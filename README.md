# 🤖 AdCounty AI Assistant

> An enterprise-grade AI Assistant powered by Retrieval-Augmented Generation (RAG), designed to deliver fast, accurate, and context-aware responses from company knowledge using local Large Language Models.

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
- 🤖 Local LLM Inference using Ollama (Llama 3.1)
- 🎯 Intelligent Intent Detection
- 💬 Multi-turn Conversation Support
- 🌐 Automated Website Scraping
- ⚡ FastAPI Backend
- 🎨 Responsive React Frontend
- 📊 Product Comparison Engine
- 👥 Leadership & Company Information Retrieval
- 😊 Small Talk Detection
- 🧩 Modular & Scalable Architecture

---

## 🛠 Tech Stack

### Backend
- Python
- FastAPI
- ChromaDB
- Ollama
- Sentence Transformers
- Transformers
- Playwright
- BeautifulSoup

### Frontend
- React
- JavaScript
- CSS

### AI & Machine Learning
- Retrieval-Augmented Generation (RAG)
- Semantic Search
- Local LLMs
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
      Ollama (Llama 3.1 Local LLM)
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
│   └── database/
│
├── frontend/
│
├── data/
│   ├── knowledge/
│   └── smalltalk/
│
├── scripts/
├── chroma_db/
├── tests/
│
├── requirements.txt
└── README.md
```

---

## 🚀 Getting Started

### Clone the repository

```bash
git clone https://github.com/Krxtrate/AdCounty-AI-Assistant
```

### Backend

```bash
python -m venv venv

# Windows
venv\Scripts\activate

pip install -r requirements.txt

playwright install
```

### Start Ollama

```bash
ollama serve
```

Pull the required model if needed:

```bash
ollama pull llama3.1:8b
```

### Run the Backend

```bash
uvicorn chatbot.app:app --reload
```

### Frontend

```bash
cd frontend

npm install

npm run dev
```

---

## 🎯 Key Highlights

- ✅ Enterprise-ready RAG architecture
- ✅ Local AI inference (No external LLM API required)
- ✅ Fast semantic document retrieval
- ✅ Context-aware responses
- ✅ Conversation memory support
- ✅ Product recommendation & comparison
- ✅ Knowledge ingestion pipeline
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

**Kritarth**
