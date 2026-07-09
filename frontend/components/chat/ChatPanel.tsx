"use client";

import React, { useState, useRef, useEffect } from "react";
import { useChat } from "../../hooks/useChat";
import ChatMessage from "./ChatMessage";
import SuggestedQuestions from "./SuggestedQuestions";
import { ArrowUp, Loader2, MessageSquareDashed } from "lucide-react";

interface ChatPanelProps {
  uploadId: string;
}

export default function ChatPanel({ uploadId }: ChatPanelProps) {
  const { messages, suggestions, isLoading, isStreaming, error, sendMessage } = useChat(uploadId);
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement | null>(null);

  // Auto-scroll to bottom of conversation thread on message update
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isStreaming]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;
    sendMessage(input);
    setInput("");
  };

  const selectSuggestion = (question: string) => {
    sendMessage(question);
  };

  return (
    <div className="flex flex-col h-full bg-bg-elevated border border-border rounded-3xl overflow-hidden shadow-sm">
      {/* Header */}
      <div className="p-4 border-b border-border bg-bg-sunken/10 flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-brand-500 animate-pulse" />
        <span className="text-xs font-bold text-foreground">Ask Document Questions</span>
      </div>

      {/* Messages Thread */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-[300px]">
        {isLoading ? (
          <div className="h-full flex items-center justify-center">
            <Loader2 className="w-6 h-6 text-brand-500 animate-spin" />
          </div>
        ) : messages.length > 0 ? (
          <div className="space-y-4">
            {messages.map((msg) => (
              <ChatMessage key={msg.id} message={msg} />
            ))}
            {isStreaming && (
              <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground ml-10">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-brand-500" />
                <span>AI is typing...</span>
              </div>
            )}
            <div ref={scrollRef} />
          </div>
        ) : (
          <div className="h-full flex flex-col justify-between py-6">
            <div className="flex flex-col items-center justify-center text-center p-8 my-auto text-muted-foreground">
              <MessageSquareDashed className="w-10 h-10 mb-3 text-muted-foreground/60" />
              <p className="text-sm font-bold">Start a Conversation</p>
              <p className="text-xs mt-1 leading-normal max-w-xs">
                Ask about key dates, contract risks, total fees, or dose volumes.
              </p>
            </div>
            {/* Suggested prompts placement */}
            <div className="px-2">
              <SuggestedQuestions suggestions={suggestions} onSelect={selectSuggestion} />
            </div>
          </div>
        )}

        {error && (
          <div className="p-3 rounded-xl bg-danger-50 text-danger-500 text-xs font-semibold text-center">
            {error}
          </div>
        )}
      </div>

      {/* Form Input Area */}
      <form onSubmit={handleSend} className="p-4 border-t border-border bg-bg-base/30 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question..."
          disabled={isStreaming || isLoading}
          className="flex-1 py-2.5 px-4 border border-border rounded-2xl bg-bg-elevated text-sm placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!input.trim() || isStreaming || isLoading}
          className="p-2.5 bg-black dark:bg-white text-white dark:text-black hover:opacity-90 rounded-2xl transition-all disabled:opacity-30 disabled:scale-100 active:scale-95 flex items-center justify-center flex-shrink-0"
        >
          <ArrowUp className="w-4.5 h-4.5" />
        </button>
      </form>
    </div>
  );
}
