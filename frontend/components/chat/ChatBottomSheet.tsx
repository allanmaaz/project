"use client";

import React, { useState } from "react";
import { MessageSquare, X } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import ChatPanel from "./ChatPanel";

interface ChatBottomSheetProps {
  uploadId: string;
}

export default function ChatBottomSheet({ uploadId }: ChatBottomSheetProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {/* Floating Action Button - FAB (Mobile only) */}
      <button
        onClick={() => setIsOpen(true)}
        className="lg:hidden fixed bottom-20 right-4 w-12 h-12 rounded-full bg-brand-500 text-white flex items-center justify-center shadow-lg hover:scale-105 active:scale-95 transition-all z-40 border border-brand-600"
      >
        <MessageSquare className="w-5.5 h-5.5" />
      </button>

      {/* Animated Drawer panel */}
      <AnimatePresence>
        {isOpen && (
          <div className="lg:hidden fixed inset-0 z-50 flex flex-col justify-end">
            {/* Backdrop cover */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
              className="absolute inset-0 bg-neutral-950/40 backdrop-blur-xs"
            />

            {/* Bottom Drawer container */}
            <motion.div
              initial={{ y: "100%" }}
              animate={{ y: 0 }}
              exit={{ y: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 220 }}
              className="bg-bg-base w-full rounded-t-3xl border-t border-border shadow-2xl relative flex flex-col h-[70dvh] z-10"
            >
              {/* Top Handle / Drag indicator */}
              <div className="w-full flex justify-between items-center px-6 py-4 border-b border-border bg-bg-elevated rounded-t-3xl">
                <span className="text-sm font-bold">Document Q&A</span>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1 rounded-md text-muted-foreground hover:bg-bg-base transition-all"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Chat panel contents */}
              <div className="flex-1 min-h-0 p-4">
                <ChatPanel uploadId={uploadId} />
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}
