import { useState, useEffect, useRef, useCallback } from "react";
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
  
  const controllerRef = useRef<AbortController | null>(null);

  const cleanup = useCallback(() => {
    if (controllerRef.current) {
      controllerRef.current.abort();
      controllerRef.current = null;
    }
  }, []);

  useEffect(() => {
    loadChatHistory();
    loadSuggestions();
    return cleanup;
  }, [uploadId, cleanup]);

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

      // Use the API client's streamChat method
      controllerRef.current = new AbortController();
      const response = await api.chat.streamChat(uploadId, text, token);

      if (!response.ok) {
        const errData = await response.json().catch(() => ({ error: { message: "Stream failed" } }));
        throw new Error(errData.error?.message || "Failed to start chat stream");
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let accumulatedContent = "";

      if (!reader) throw new Error("No response body");

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.token) {
                accumulatedContent += data.token;
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === tempAiMsgId ? { ...msg, content: accumulatedContent } : msg
                  )
                );
              } else if (data.event === "done") {
                cleanup();
                setIsStreaming(false);
                loadChatHistory();
              } else if (data.event === "error") {
                cleanup();
                setIsStreaming(false);
                setError(data.message || "Error generating AI response.");
                setMessages((prev) => prev.filter((msg) => msg.id !== tempAiMsgId));
              }
            } catch {
              // Ignore parse errors
            }
          }
        }
      }

      // Stream ended normally
      cleanup();
      setIsStreaming(false);
      loadChatHistory();

    } catch (err: any) {
      cleanup();
      setIsStreaming(false);
      if (err.name === "AbortError") return;
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
