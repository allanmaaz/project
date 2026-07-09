"use client";

import React from "react";
import { Sparkles } from "lucide-react";
import { motion } from "framer-motion";

interface SummaryCardProps {
  summary: string;
}

export default function SummaryCard({ summary }: SummaryCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-6 rounded-3xl border-l-4 border-l-brand-500 border border-y-border border-r-border bg-brand-50/20 dark:bg-brand-900/5 relative overflow-hidden"
    >
      {/* Background ambient light */}
      <div className="absolute top-[-10px] right-[-10px] w-24 h-24 bg-brand-350/10 rounded-full blur-xl" />
      
      <div className="flex gap-4">
        <div className="p-2 bg-brand-500/10 text-brand-500 rounded-xl h-fit">
          <Sparkles className="w-5 h-5" />
        </div>
        <div className="space-y-2">
          <span className="text-[10px] uppercase font-bold tracking-widest text-brand-500">
            Executive Summary
          </span>
          <p className="text-sm font-semibold text-foreground/90 leading-relaxed">
            {summary || "AI is composing summary..."}
          </p>
        </div>
      </div>
    </motion.div>
  );
}
