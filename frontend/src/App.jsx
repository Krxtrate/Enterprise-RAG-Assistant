import { useState, useRef, useEffect } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hello! I am the AI assistant for ABC. Ask me anything 🚀",
    },
  ]);

  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages]);


  const newChat = () => {
    setMessages([
      {
        role: "assistant",
        content:
          "Hello! I am the AI assistant for ABC. Ask me anything 🚀",
      },
    ]);

    setInput("");
  };

  const generate = async () => {
    if (!input.trim()) return;

    const currentInput = input.trim();

    const userMessage = {
      role: "user",
      content: currentInput,
    };

    const updatedMessages = [...messages, userMessage];

    const imageKeywords = [
      "generate image",
      "generate an image",
      "create image",
      "draw a",
      "make an image",
      "create a picture",
      "generate a picture",
      "create artwork",
      "make a drawing",
      "image of",
      "picture of",
      "generate a photo",
      "create a photo",
    ];

    const isImageRequest = imageKeywords.some((keyword) =>
      currentInput.toLowerCase().includes(keyword)
    );

    setMessages(updatedMessages);
    setInput("");

    try {
      setLoading(true);

      let response;

      if (isImageRequest) {
        response = await axios.post(
          "http://127.0.0.1:8000/generate-image",
          {
            prompt: currentInput,
          }
        );

        if (response.data.error) {
          throw new Error(response.data.error);
        }

        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: "[Generated Image]",
            image: response.data.image,
          },
        ]);
      } else {
        response = await axios.post(
          "http://127.0.0.1:8000/generate",
          {
            messages: updatedMessages,
          }
        );

        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content:
              response.data.output ||
              "No response received.",
          },
        ]);
      }
    } catch (error) {
      console.error(error);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            error?.message ||
            "❌ Failed to connect to backend.",
        },
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

  return (
    <div className="app">
      <div className="sidebar">
        <h2>🤖 Your AI Assistant</h2>
        <button
          className="new-chat"
          onClick={newChat}
        >
          + New Chat
        </button>
      </div>

      <div className="main">
        <div className="header">
          <h1>🚀 ABC AI</h1>
          <p>Enterprise Knowledge Assistant</p>
        </div>

        <div className="chat-container">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`message ${msg.role}`}
            >
              {msg.content && (
                <div>{msg.content}</div>
              )}

              {msg.image && (
                <img
                  src={`data:image/png;base64,${msg.image}`}
                  alt="Generated"
                  className="generated-image"
                />
              )}
            </div>
          ))}

          {loading && (
            <div className="message assistant">
              🤖 Thinking...
            </div>
          )}

          <div ref={messagesEndRef}></div>
        </div>

        <div className="input-area">
          <textarea
            placeholder="Ask something..."
            value={input}
            onChange={(e) =>
              setInput(e.target.value)
            }
            onKeyDown={handleKeyDown}
          />

          <button
            className="send-btn"
            onClick={generate}
            disabled={loading}
          >
            ➤
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;