"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { Search, FileText, UploadCloud, History, BarChart2, X, Settings } from "lucide-react";

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const [query, setQuery] = useState("");
  const router = useRouter();

  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      document.body.style.overflow = "hidden";
      window.addEventListener("keydown", handleEsc);
    }
    return () => {
      document.body.style.overflow = "unset";
      window.removeEventListener("keydown", handleEsc);
    };
  }, [isOpen, onClose]);

  const items = [
    { label: "Upload Document", desc: "Scan new prescriptions, contracts, bills", icon: UploadCloud, action: () => router.push("/upload") },
    { label: "View History", desc: "Search and filter past uploads", icon: History, action: () => router.push("/history") },
    { label: "Stats & Analytics", desc: "View spending, risk factors, counts", icon: BarChart2, action: () => router.push("/stats") },
    { label: "Account Settings", desc: "Update profile, theme, and language", icon: Settings, action: () => router.push("/settings") },
  ];

  const filteredItems = items.filter(
    (item) =>
      item.label.toLowerCase().includes(query.toLowerCase()) ||
      item.desc.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[100] flex items-start justify-center pt-[15dvh] px-4">
          {/* Backdrop blur overlay */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-neutral-950/40 backdrop-blur-sm"
          />

          {/* Palette container */}
          <motion.div
            initial={{ opacity: 0, scale: 0.96, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: -10 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="w-full max-w-lg rounded-2xl border border-border bg-bg-elevated shadow-2xl overflow-hidden z-10 flex flex-col max-h-[400px]"
          >
            {/* Search Input bar */}
            <div className="flex items-center px-4 border-b border-border py-3">
              <Search className="w-5 h-5 text-muted-foreground mr-3 flex-shrink-0" />
              <input
                type="text"
                autoFocus
                placeholder="Search commands or actions..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="w-full bg-transparent border-none text-foreground text-sm placeholder-muted-foreground focus:outline-none"
              />
              <button
                onClick={onClose}
                className="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-bg-base transition-all"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Results listing */}
            <div className="flex-1 overflow-y-auto p-2 space-y-1">
              {filteredItems.length > 0 ? (
                filteredItems.map((item, index) => {
                  const Icon = item.icon;
                  return (
                    <button
                      key={index}
                      onClick={() => {
                        item.action();
                        onClose();
                      }}
                      className="w-full flex items-center text-left gap-3 px-3 py-2.5 rounded-xl hover:bg-bg-base transition-all group"
                    >
                      <div className="p-2 rounded-lg bg-bg-sunken border border-border group-hover:bg-bg-elevated transition-all flex-shrink-0 text-muted-foreground group-hover:text-brand-500">
                        <Icon className="w-4 h-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-semibold text-foreground truncate">{item.label}</p>
                        <p className="text-xs text-muted-foreground truncate">{item.desc}</p>
                      </div>
                    </button>
                  );
                })
              ) : (
                <div className="text-center py-8 text-sm text-muted-foreground font-semibold">
                  No commands matching your query.
                </div>
              )}
            </div>

            {/* Footer tips */}
            <div className="px-4 py-2 border-t border-border bg-bg-sunken/30 flex justify-between items-center text-[10px] text-muted-foreground font-semibold">
              <span>Use arrows to navigate, Enter to select</span>
              <span>ESC to close</span>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
