import React, { useState, useRef, useEffect } from "react";
import { IoChatbubbleEllipses, IoClose } from "react-icons/io5";
import "../styles/ChatWidget.css";

const clamp = (v, a, b) => Math.max(a, Math.min(b, v));

const ChatWidget = () => {
  const [open, setOpen] = useState(false);
  // width in percentage of viewport (30 - 70)
  const [widthPct, setWidthPct] = useState(40);
  const [resizing, setResizing] = useState(false);
  const sidebarRef = useRef(null);

  useEffect(() => {
    const onMove = (e) => {
      if (!resizing) return;
      const clientX = e.clientX || (e.touches && e.touches[0].clientX);
      if (typeof clientX !== "number") return;
      const vw = window.innerWidth;
      // width from right edge
      const widthPx = vw - clientX;
      const pct = (widthPx / vw) * 100;
      setWidthPct((p) => clamp(Math.round(pct), 30, 70));
    };

    const onUp = () => setResizing(false);

    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    window.addEventListener("touchmove", onMove);
    window.addEventListener("touchend", onUp);

    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
      window.removeEventListener("touchmove", onMove);
      window.removeEventListener("touchend", onUp);
    };
  }, [resizing]);

  useEffect(() => {
    // prevent body scroll when open
    document.body.style.overflow = open ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  const startResize = (e) => {
    e.stopPropagation();
    setResizing(true);
  };

  return (
    <>
      {/* Floating button */}
      {!open && (
        <div className={`chat-widget-fab ${open ? "open" : ""}`}>
          <button
            aria-label={open ? "Close chat" : "Open chat"}
            className="chat-fab-button"
            onClick={() => setOpen((s) => !s)}
          >
            {/* {open ? <IoClose size={22} /> : <IoChatbubbleEllipses size={22} />} */}
            <IoChatbubbleEllipses size={22} />
          </button>
        </div>
      )}

      {/* Overlay */}
      {open && (
        <div className="chat-widget-overlay" onClick={() => setOpen(false)} />
      )}

      {/* Sidebar */}
      <aside
        ref={sidebarRef}
        className={`chat-widget-sidebar ${open ? "open" : ""}`}
        style={{ width: `${widthPct}vw`, minWidth: "30vw", maxWidth: "70vw" }}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-hidden={!open}
      >
        <div className="chat-sidebar-header">
          <h3>Assistant</h3>
          <div className="chat-header-actions">
            <button
              className="small-btn"
              onClick={() => setOpen(false)}
              aria-label="Close chat"
            >
              <IoClose size={18} />
            </button>
          </div>
        </div>

        <div className="chat-sidebar-body">
          <div className="chat-messages">
            <div className="chat-message bot">
              Hi! I'm your assistant. Ask me about brands.
            </div>
          </div>
        </div>

        <div className="chat-sidebar-footer">
          <input className="chat-input" placeholder="Type a message..." />
          <button className="chat-send">Send</button>
        </div>

        {/* Resizer handle on left edge */}
        <div
          className="chat-resizer"
          role="separator"
          aria-orientation="vertical"
          onMouseDown={startResize}
          onTouchStart={startResize}
        />
      </aside>
    </>
  );
};

export default ChatWidget;
