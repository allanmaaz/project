import { useState, useEffect, useRef } from "react";
import { api } from "../lib/api";
import { getAccessToken } from "../lib/supabase";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export const useChat = (uploadId: string) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const eventSourceRef = useRef<EventSource | null>(null);

  const cleanup = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  };

  useEffect(() => {
    loadChatHistory();
    loadSuggestions();
    return cleanup;
  }, [uploadId]);

  const loadChatHistory = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.chat.getHistory(uploadId);
      setMessages(res.messages);
    } catch (err: any) {
      setError(err.message || "Failed to load chat history.");
    } finally {
      setIsLoading(false);
    }
  };

  const loadSuggestions = async () => {
    try {
      const res = await api.chat.getSuggestions(uploadId);
      setSuggestions(res.suggestions);
    } catch {
      // Gracefully ignore suggestion load errors
    }
  };

  const sendMessage = async (text: string) => {
    if (!text.trim() || isStreaming) return;

    cleanup();
    setError(null);

    // 1. Optimistic User Message
    const tempUserMsg: Message = {
      id: Math.random().toString(),
      role: "user",
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    // 2. Set temporary empty AI response bubble
    const tempAiMsgId = Math.random().toString();
    const tempAiMsg: Message = {
      id: tempAiMsgId,
      role: "assistant",
      content: "",
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempAiMsg]);
    setIsStreaming(true);

    try {
      const token = await getAccessToken();
      if (!token) {
        throw new Error("You must be logged in to chat.");
      }

      // Build EventSource link with auth token in URL parameters
      const streamUrl = api.chat.getStreamUrl(uploadId, text, token);
      const eventSource = new EventSource(streamUrl);
      eventSourceRef.current = eventSource;

      let accumulatedContent = "";

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.token) {
            accumulatedContent += data.token;
            // Update the temporary AI message content
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === tempAiMsgId ? { ...msg, content: accumulatedContent } : msg
              )
            );
          } else if (data.event === "done") {
            cleanup();
            setIsStreaming(false);
            // Refresh with real database records to get exact IDs and timestamps
            loadChatHistory();
          } else if (data.event === "error") {
            cleanup();
            setIsStreaming(false);
            setError(data.message || "Error generating AI response.");
            // Remove the empty/incomplete AI bubble
            setMessages((prev) => prev.filter((msg) => msg.id !== tempAiMsgId));
          }
        } catch {
          // Ignore parse errors
        }
      };

      eventSource.onerror = (err) => {
        cleanup();
        setIsStreaming(false);
        setError("Connection lost. Please try again.");
        setMessages((prev) => prev.filter((msg) => msg.id !== tempAiMsgId));
      };

    } catch (err: any) {
      cleanup();
      setIsStreaming(false);
      setError(err.message || "Failed to initiate chat stream.");
      setMessages((prev) => prev.filter((msg) => msg.id !== tempAiMsgId));
    }
  };

  return {
    messages,
    suggestions,
    isLoading,
    isStreaming,
    error,
    sendMessage,
    reloadHistory: loadChatHistory,
  };
};
