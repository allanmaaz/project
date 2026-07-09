"use client";

import React from "react";
import { Message } from "../../hooks/useChat";
import { User, Sparkles } from "lucide-react";

interface ChatMessageProps {
  message: Message;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  const renderContent = (content: string) => {
    // Simple formatter: replace *text* or **text** with bold tags
    const parts = content.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, index) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={index} className="font-extrabold text-foreground">{part.slice(2, -2)}</strong>;
      }
      return part;
    });
  };

  return (
    <div className={`flex gap-3.5 max-w-[85%] ${isUser ? "ml-auto flex-row-reverse" : "mr-auto"}`}>
      {/* Avatar icon */}
      <div
        className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 text-xs font-bold ${
          isUser
            ? "bg-brand-500/10 text-brand-500 border border-brand-500/20"
            : "bg-black/5 dark:bg-white/5 border border-border text-muted-foreground"
        }`}
      >
        {isUser ? <User className="w-3.5 h-3.5" /> : <Sparkles className="w-3.5 h-3.5 text-brand-500" />}
      </div>

      {/* Bubble text wrapper */}
      <div
        className={`p-3.5 rounded-2xl text-sm font-semibold leading-relaxed ${
          isUser
            ? "bg-black dark:bg-white text-white dark:text-black rounded-tr-xs shadow-xs"
            : "bg-bg-elevated border border-border text-foreground/90 rounded-tl-xs shadow-xs"
        }`}
      >
        <p className="whitespace-pre-line">{renderContent(message.content)}</p>
      </div>
    </div>
  );
}
