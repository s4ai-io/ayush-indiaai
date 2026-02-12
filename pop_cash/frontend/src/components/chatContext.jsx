// import { createContext, useContext, useState } from "react";

// const ChatContext = createContext();

// const ChatProvider = ({ children }) => {
//   const [messages, setMessages] = useState([]);
//   const [isLoading, setIsLoading] = useState(false);
//   const [toast, setToast] = useState(null);
//   const [isStreaming, setIsStreaming] = useState(false); // ✅ NEW STATE

//   const addMessage = (content, type = "user") => {
//     setMessages((msgs) => [
//       ...msgs,
//       {
//         id: Date.now().toString(),
//         content,
//         type,
//         timestamp: new Date(),
//       },
//     ]);
//   };

//   const sendMessage = async (msg) => {
//     addMessage(msg, "user");
//     setIsLoading(true);
//     setIsStreaming(false);

//     try {
//       const res = await fetch("/api/chat", {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({ message: msg }),
//       });

//       if (!res.ok) throw new Error("Network response was not ok");

//       const reader = res.body.getReader();
//       const decoder = new TextDecoder();
//       let fullText = "";

//       // Create empty assistant message
//       const id = Date.now().toString();
//       setMessages((msgs) => [
//         ...msgs,
//         { id, content: "", type: "assistant", timestamp: new Date() },
//       ]);

//       // Stream chunks directly without normalization
//       while (true) {
//         const { done, value } = await reader.read();
//         if (done) break;
//         const chunk = decoder.decode(value, { stream: true });
//         // ✅ Mark streaming as started once the first chunk arrives
//         if (!isStreaming) setIsStreaming(true);
//         fullText += chunk;

//         // Update assistant message progressively
//         setMessages((msgs) =>
//           msgs.map((m) => (m.id === id ? { ...m, content: fullText } : m))
//         );
//       }
//     } catch (err) {
//       console.error("Streaming error:", err);
//       addMessage("Error: Unable to stream response from AI.", "assistant");
//       setToast({
//         type: "error",
//         message: "Streaming error. Please try again.",
//       });
//     }

//     setIsLoading(false);
//     setIsStreaming(false);
//   };

//   return (
//     <ChatContext.Provider
//       value={{ messages, isLoading, toast, isStreaming, sendMessage }}
//     >
//       {children}
//     </ChatContext.Provider>
//   );
// };

// export function useChat() {
//   return useContext(ChatContext);
// }

// export default ChatProvider;

import { createContext, useContext, useState } from "react";

const ChatContext = createContext();

const ChatProvider = ({ children }) => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [isStreaming, setIsStreaming] = useState(false);

  const addMessage = (content, type = "user") => {
    setMessages((msgs) => [
      ...msgs,
      {
        id: Date.now().toString(),
        content,
        type,
        timestamp: new Date(),
      },
    ]);
  };

  const sendMessage = async (msg) => {
    addMessage(msg, "user");
    setIsLoading(true);
    setIsStreaming(false);

    try {
      // ✅ Connect directly to your AutoRAG backend
      const backendUrl = "http://127.0.0.1:8000/ask";

      const res = await fetch(backendUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: msg }), // Changed from 'message' to 'query' to match your backend
      });

      if (!res.ok) {
        throw new Error(`Backend returned ${res.status}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let fullText = "";

      // Create empty assistant message
      const id = Date.now().toString();
      setMessages((msgs) => [
        ...msgs,
        { id, content: "", type: "assistant", timestamp: new Date() },
      ]);

      // Stream chunks directly
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });

        // Mark streaming as started once the first chunk arrives
        if (!isStreaming) setIsStreaming(true);

        fullText += chunk;

        // Update assistant message progressively
        setMessages((msgs) =>
          msgs.map((m) => (m.id === id ? { ...m, content: fullText } : m))
        );
      }

      // Clear any previous error toast on success
      setToast(null);
    } catch (err) {
      console.error("❌ Streaming error:", err);
      addMessage(
        "Error: Unable to connect to the AI backend. Please check if the server is running.",
        "assistant"
      );
      setToast({
        type: "error",
        message: "Failed to reach AI backend. Please try again.",
      });
    }

    setIsLoading(false);
    setIsStreaming(false);
  };

  return (
    <ChatContext.Provider
      value={{ messages, isLoading, toast, setToast, isStreaming, sendMessage }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export function useChat() {
  return useContext(ChatContext);
}

export default ChatProvider;
