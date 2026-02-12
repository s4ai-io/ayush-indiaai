import { useState, useEffect, useRef } from "react";
import { FiSend, FiX } from "react-icons/fi";
import { useChat } from "./chatContext";
import { marked } from "marked";
import { sanitize } from "isomorphic-dompurify";
import "../styles/FloatingChatDrawer.css";
import aiLogo from "../assets/ailogo.png";

const FloatingChatDrawer = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [drawerWidth, setDrawerWidth] = useState("30vw");
  const [isResizing, setIsResizing] = useState(false);
  const startXRef = useRef(0);
  const startWidthRef = useRef(0);
  const messagesEndRef = useRef(null);
  const { messages, isLoading, toast, setToast, isStreaming, sendMessage } =
    useChat();

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    requestAnimationFrame(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: "auto" });
    });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  const handleSend = () => {
    if (message.trim() !== "") {
      sendMessage(message);
      setMessage("");
    }
  };

  // Handle mouse drag resize with 30%-80% limits
  const handleMouseDown = (e) => {
    setIsResizing(true);
    startXRef.current = e.clientX;
    startWidthRef.current = parseFloat(drawerWidth);
    e.preventDefault();
  };

  const handleMouseMove = (e) => {
    if (!isResizing) return;
    const deltaX = startXRef.current - e.clientX;
    const screenWidth = window.innerWidth;
    let newWidthPercent =
      ((screenWidth * parseFloat(drawerWidth)) / 100 + deltaX) / screenWidth;

    newWidthPercent = Math.max(0.3, Math.min(0.8, newWidthPercent));
    setDrawerWidth(`${newWidthPercent * 100}vw`);
  };

  const handleMouseUp = () => {
    setIsResizing(false);
  };

  useEffect(() => {
    if (isResizing) {
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
    } else {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    }
    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isResizing]);

  // Animated loading dots
  const LoadingDots = () => (
    <span className="loading-dots">
      <span className="loading-dot"></span>
      <span className="loading-dot"></span>
      <span className="loading-dot"></span>
    </span>
  );

  // Clean malformed HTML
  const cleanContent = (content) => {
    return content
      .replace(/<\s+/g, "<")
      .replace(/\s+>/g, ">")
      .replace(
        /<(\w+)\s+([^>]*?)\s*>/g,
        (match, tag, attrs) => `<${tag}${attrs ? " " + attrs.trim() : ""}>`
      );
  };

  // Custom code block renderer
  marked.setOptions({
    gfm: true,
    breaks: true,
    renderer: new marked.Renderer({
      code(code, infostring) {
        const lang = (infostring || "").match(/\S*/)[0];
        return `<pre><code class="language-${lang}">${code}</code></pre>`;
      },
    }),
  });

  return (
    <>
      {/* Floating Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="floating-chat-button"
          aria-label="Open chat"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            />
          </svg>
        </button>
      )}

      {/* Background overlay */}
      {isOpen && (
        <div
          className="chat-overlay"
          onClick={() => setIsOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Drawer */}
      {isOpen && (
        <aside className="chat-drawer" style={{ width: drawerWidth }}>
          {/* Resize Handle */}
          <div onMouseDown={handleMouseDown} className="resize-handle"></div>

          {/* Header */}
          <header className="chat-header">
            <div className="chat-header-content">
              <img src={aiLogo} alt="Logo" className="chat-logo" loading="lazy" />
              <h2 className="chat-title">ISHA</h2>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="chat-close-button"
              aria-label="Close chat"
            >
              <FiX />
            </button>
          </header>

          {/* Messages Container */}
          <div className="chat-messages">
            <div className="messages-list">
              {messages.length === 0 && (
                <div className="chat-empty-state">
                  <h3>👋 Hello!</h3>
                  <p>How can I assist you today?</p>
                </div>
              )}
              {messages.map((msg) => (
                <div key={msg.id} className={`message-wrapper ${msg.type}`}>
                  <div className={`message-bubble ${msg.type}`}>
                    {msg.type === "user" ? (
                      <div className="message-content">{msg.content}</div>
                    ) : (
                      <div
                        className="markdown-content"
                        dangerouslySetInnerHTML={{
                          __html: sanitize(
                            marked.parse(cleanContent(msg.content)),
                            {
                              USE_PROFILES: { html: true },
                            }
                          ),
                        }}
                      />
                    )}
                    <div className={`message-timestamp ${msg.type}`}>
                      {msg.timestamp &&
                        new Date(msg.timestamp).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                    </div>
                  </div>
                </div>
              ))}
              {isLoading && !isStreaming && (
                <div className="loading-message">
                  <div className="loading-bubble">
                    <span className="loading-text">
                      ISHA is typing <LoadingDots />
                    </span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Footer */}
          <footer className="chat-footer">
            <div className="chat-input-wrapper">
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Type your message..."
                className="chat-textarea"
                rows={1}
                style={{
                  height: "auto",
                  minHeight: "48px",
                }}
                onInput={(e) => {
                  e.target.style.height = "auto";
                  e.target.style.height =
                    Math.min(e.target.scrollHeight, 128) + "px";
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                disabled={isLoading}
              />
              <button
                onClick={handleSend}
                disabled={!message.trim() || isLoading}
                className="chat-send-button"
                aria-label="Send message"
              >
                <FiSend />
              </button>
            </div>
            {toast && (
              <div className={`chat-toast ${toast.type}`}>
                <span>{toast.message}</span>
                {toast.type === "error" && (
                  <button
                    onClick={() => {
                      setToast(null);
                      if (message) sendMessage(message);
                    }}
                    className="chat-toast-retry"
                  >
                    Retry
                  </button>
                )}
              </div>
            )}
          </footer>
        </aside>
      )}
    </>
  );
};

export default FloatingChatDrawer;
