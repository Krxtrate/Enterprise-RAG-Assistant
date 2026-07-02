import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import "./App.css";

function TypingIndicator() {
  return (
    <div className="message assistant typing-msg">
      <span className="typing-dot" />
      <span className="typing-dot" />
      <span className="typing-dot" />
    </div>
  );
}

function Message({ msg }) {
  return (
    <div className={`message ${msg.role}${msg.isError ? " error-msg" : ""}`}>
      <div className="msg-avatar">
        {msg.role === "assistant" ? "🤖" : "👤"}
      </div>
      <div className="msg-body">
        <div className="msg-content">{msg.content}</div>
      </div>
    </div>
  );
}

function BackendNotice({ text }) {
  return (
    <div className="backend-notice">
      <span className="backend-notice-dot" />
      {text}
    </div>
  );
}

function App() {

  const [backendOnline, setBackendOnline] = useState(false);
  const [backendNotice, setBackendNotice] = useState(null);

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const response = await fetch("http://localhost:8000/");

        if (response.ok) {
          setBackendOnline(true);
        } else {
          setBackendOnline(false);
        }
      } catch {
        setBackendOnline(false);
      }
    };

    checkBackend();

    const interval = setInterval(checkBackend, 3000);

    return () => clearInterval(interval);
  }, []);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hello! I'm the AI assistant for AdCounty Media. Ask me about our products, team, services, or anything else! 🚀",
    },
  ]);

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const newChat = () => {
    setMessages([
      {
        role: "assistant",
        content:
          "Hello! I'm the AI assistant for AdCounty Media. Ask me about our products, team, services, or anything else! 🚀",
      },
    ]);
    setInput("");
    textareaRef.current?.focus();
  };

  const generate = async () => {
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    const userMessage = { role: "user", content: trimmed };
    const updatedMessages = [...messages, userMessage];

    setMessages(updatedMessages);
    setInput("");

    setLoading(true);
    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/generate",
        {
          messages: updatedMessages,
          company: "general",
        },
        { timeout: 180000 }
      );

      const output = response?.data?.output;
      const notice = response?.data?.notice;

      // Show (or clear) the fallback notice based on this response.
      // Once shown, it persists until a response comes back without one
      // (i.e. HF Inference API recovers).
      setBackendNotice(notice || null);

      if (!output) {
        // Backend returned 200 but no output field — show a user-visible error
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: "⚠️ I received an empty response. Please try again.",
            isError: true,
          },
        ]);
        return;
      }

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: output },
      ]);
    } catch (error) {
      console.error("Request failed:", error);

      let errorMsg = "❌ Failed to connect to the backend. Make sure the server is running.";
      if (error.code === "ECONNABORTED") {
        errorMsg = "⏱️ Request timed out. The model is taking too long — please try again.";
      } else if (error.response) {
        errorMsg = `❌ Server error (${error.response.status}). Please try again.`;
      }

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: errorMsg, isError: true },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      generate();
    }
  };

  const suggestedQuestions = [
    "Tell me about AdCounty Media",
    "What products do you offer?",
    "Who is on the leadership team?",
  ];

  const showSuggestions = messages.length === 1 && !loading;

  return (
    <div className="app">
      {/* SIDEBAR */}
      <aside className="sidebar">
        <div className="sidebar-logo">
            <img
                src="/adcountylogo.png"
                alt="AdCounty AI"
                className="logo-image"
            />
        </div>

        <button className="new-chat-btn" onClick={newChat}>
          <span className="new-chat-icon">＋</span>
          New Chat
        </button>

        <div className="sidebar-divider" />

        <div className="sidebar-section-label">Products</div>
        {["BidCounty", "GenWin", "GAM360", "iSearchAds", "SeeTV", "OpSIS Pro"].map(
          (product) => (
            <button
              key={product}
              className="sidebar-product-btn"
              onClick={() => {
                setInput(`Tell me about ${product}`);
                textareaRef.current?.focus();
              }}
            >
              <span className="product-dot" />
              {product}
            </button>
          )
        )}

        <div className="sidebar-footer">
          <span className="sidebar-footer-text">AdCounty Media © 2026</span>
        </div>
      </aside>

      {/* MAIN */}
      <main className="main">
        {/* HEADER */}
        <header className="header">
          <div className="header-left">
            <div className="header-avatar">
              <img src="/adcountychatlogo.png" alt="AdCounty" />
            </div>
            <div>
              <h1 className="header-title">AdCounty Media AI </h1>
              <p className="header-subtitle">Enterprise Knowledge Assistant</p>
            </div>
          </div>
          <div className={`status-badge ${backendOnline ? "online" : "offline"}`}>
            <span className="status-dot"></span>
            {backendOnline ? "Online" : "Offline"}
          </div>
        </header>

        {backendNotice && <BackendNotice text={backendNotice} />}

        {/* CHAT */}
        <div className="chat-container">
          {messages.map((msg, index) => (
            <Message key={index} msg={msg} />
          ))}

          {loading && <TypingIndicator />}

          {showSuggestions && (
            <div className="suggestions">
              <p className="suggestions-label">Suggested questions</p>
              <div className="suggestions-grid">
                {suggestedQuestions.map((q) => (
                  <button
                    key={q}
                    className="suggestion-chip"
                    onClick={() => {
                      setInput(q);
                      textareaRef.current?.focus();
                    }}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* INPUT */}
        <div className="input-area">
          <div className="input-wrapper">
            <textarea
              ref={textareaRef}
              placeholder="Ask me about AdCounty Media, our products, team..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
              disabled={loading}
            />
            <button
              className="send-btn"
              onClick={generate}
              disabled={loading || !input.trim()}
              aria-label="Send message"
            >
              {loading ? (
                <span className="send-spinner" />
              ) : (
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M22 2L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              )}
            </button>
          </div>
          <p className="input-hint">Press Enter to send · Shift+Enter for new line</p>
        </div>
      </main>
    </div>
  );
}

export default App;