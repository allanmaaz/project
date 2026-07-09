"use client";

import React, { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface AnalysisSection {
  id: string;
  title: string;
  type: "info" | "warning" | "danger" | "success" | "neutral";
  content: string | null;
  items: string[];
  icon?: string;
}

interface AnalysisSectionProps {
  section: AnalysisSection;
  defaultExpanded?: boolean;
}

export default function AnalysisSectionComponent({
  section,
  defaultExpanded = true,
}: AnalysisSectionProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  const getBorderColor = () => {
    switch (section.type) {
      case "danger":
        return "border-l-danger-500";
      case "warning":
        return "border-l-warning-500";
      case "success":
        return "border-l-success-500";
      case "info":
        return "border-l-brand-500";
      default:
        return "border-l-border";
    }
  };

  const getBgColor = () => {
    switch (section.type) {
      case "danger":
        return "bg-danger-50/10 hover:bg-danger-50/20";
      case "warning":
        return "bg-warning-50/10 hover:bg-warning-50/20";
      case "success":
        return "bg-success-50/10 hover:bg-success-50/20";
      case "info":
        return "bg-brand-50/10 hover:bg-brand-50/20";
      default:
        return "bg-bg-elevated hover:bg-bg-base";
    }
  };

  return (
    <div
      className={`border border-border rounded-2xl border-l-4 overflow-hidden transition-all shadow-xs ${getBorderColor()} ${getBgColor()}`}
    >
      {/* Header bar */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-5 text-left focus:outline-none"
      >
        <div className="flex items-center gap-3">
          <span className="text-lg font-bold text-foreground">
            {section.title}
          </span>
        </div>
        <div className="p-1 rounded-lg hover:bg-bg-base transition-all text-muted-foreground">
          {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {/* Expanded items list */}
      <AnimatePresence initial={false}>
        {isExpanded && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: "auto" }}
            exit={{ height: 0 }}
            transition={{ duration: 0.25, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div className="px-5 pb-5 pt-0 border-t border-border/40 space-y-4">
              {section.content && (
                <p className="text-sm font-semibold leading-relaxed text-foreground/80 pt-4">
                  {section.content}
                </p>
              )}
              {section.items && section.items.length > 0 && (
                <ul className="space-y-2.5">
                  {section.items.map((item, idx) => (
                    <li key={idx} className="flex items-start gap-2.5 text-sm font-semibold">
                      <span className="w-1.5 h-1.5 rounded-full bg-brand-500 flex-shrink-0 mt-2" />
                      <span className="text-foreground/90">{item}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
