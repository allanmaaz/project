"use client";

import React from "react";
import { MessageCircle } from "lucide-react";

interface SuggestedQuestionsProps {
  suggestions: string[];
  onSelect: (question: string) => void;
}

export default function SuggestedQuestions({ suggestions, onSelect }: SuggestedQuestionsProps) {
  if (!suggestions || suggestions.length === 0) return null;

  return (
    <div className="space-y-2.5">
      <span className="text-[10px] uppercase font-bold tracking-widest text-muted-foreground">
        Suggested Questions
      </span>
      <div className="flex flex-col gap-2">
        {suggestions.map((question, index) => (
          <button
            key={index}
            onClick={() => onSelect(question)}
            className="flex items-center gap-2.5 text-left w-full p-3 border border-border rounded-xl bg-bg-elevated hover:bg-bg-base text-xs font-semibold text-foreground/90 transition-all hover:translate-x-0.5 active:scale-[0.99] group shadow-xs"
          >
            <MessageCircle className="w-3.5 h-3.5 text-brand-500 group-hover:scale-105 transition-all flex-shrink-0" />
            <span className="truncate">{question}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
