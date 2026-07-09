"use client";

import React from "react";
import { motion } from "framer-motion";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen grid grid-cols-1 lg:grid-cols-12 bg-bg-base overflow-hidden">
      {/* Left side (Desktop only) - Apple/Vercel inspired showcase panel */}
      <div className="hidden lg:flex lg:col-span-7 xl:col-span-8 bg-black relative flex-col justify-between p-12 overflow-hidden">
        {/* Ambient background glows */}
        <div className="absolute top-[-10%] left-[-10%] w-[60%] h-[60%] rounded-full bg-brand-900/30 blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[60%] h-[60%] rounded-full bg-indigo-950/20 blur-[120px]" />

        {/* Wordmark logo */}
        <div className="z-10 flex items-center gap-2 text-white font-bold text-lg">
          <span className="text-brand-500 text-xl">◈</span> Clarify AI
        </div>

        {/* Dynamic floating cards panel */}
        <div className="flex-1 flex flex-col justify-center items-center z-10 relative">
          <div className="w-[450px] h-[350px] relative">
            {/* Card 1: Medical Prescription Mock */}
            <motion.div
              initial={{ opacity: 0, y: 40 }}
              animate={{
                opacity: 1,
                y: [0, -10, 0],
              }}
              transition={{
                opacity: { duration: 0.8 },
                y: { repeat: Infinity, duration: 6, ease: "easeInOut" },
              }}
              className="absolute top-4 left-4 w-72 p-5 rounded-2xl glassmorphic border-white/10 bg-white/5 text-white/90 shadow-xl"
            >
              <div className="flex items-center gap-3 mb-3">
                <span className="p-2 rounded-xl bg-success-500/20 text-success-500 text-xs">💊 Medical</span>
                <span className="text-[10px] text-white/50">Rx #92842</span>
              </div>
              <h4 className="font-semibold text-sm mb-1">Amoxicillin 500mg</h4>
              <p className="text-xs text-white/70 mb-2">Take one capsule three times daily for infection resolution.</p>
              <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
                <div className="bg-success-500 h-full w-2/3" />
              </div>
            </motion.div>

            {/* Card 2: Legal Contract Risks Mock */}
            <motion.div
              initial={{ opacity: 0, y: 60 }}
              animate={{
                opacity: 1,
                y: [0, -14, 0],
              }}
              transition={{
                opacity: { duration: 0.8, delay: 0.2 },
                y: { repeat: Infinity, duration: 7, ease: "easeInOut", delay: 0.5 },
              }}
              style={{ x: 100, y: 120 }}
              className="absolute top-16 left-8 w-72 p-5 rounded-2xl glassmorphic border-white/10 bg-white/5 text-white/90 shadow-xl"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="p-2 rounded-xl bg-danger-500/20 text-danger-500 text-xs">⚖️ Contract</span>
                <span className="text-[10px] text-danger-500 font-bold">85 Risk Score</span>
              </div>
              <h4 className="font-semibold text-sm mb-1">Section 12.3 Indemnity</h4>
              <p className="text-xs text-white/70">Uncapped liability for software outages or technical defaults.</p>
            </motion.div>

            {/* Card 3: Scam Detection Alert Mock */}
            <motion.div
              initial={{ opacity: 0, y: 80 }}
              animate={{
                opacity: 1,
                y: [0, -8, 0],
              }}
              transition={{
                opacity: { duration: 0.8, delay: 0.4 },
                y: { repeat: Infinity, duration: 5, ease: "easeInOut", delay: 1.0 },
              }}
              style={{ x: -20, y: 220 }}
              className="absolute top-24 left-12 w-72 p-5 rounded-2xl glassmorphic border-white/10 bg-white/5 text-white/90 shadow-xl"
            >
              <div className="flex items-center gap-3 mb-2">
                <span className="p-2 rounded-xl bg-warning-500/20 text-warning-500 text-xs">⚠️ Phishing Scam</span>
              </div>
              <p className="text-xs text-white/90 font-medium">"Your bank card is suspended. Click link to re-verify."</p>
              <p className="text-[10px] text-danger-500 mt-2">🚫 Urgency tactics detected. Do not click.</p>
            </motion.div>
          </div>
        </div>

        {/* Apple style quote banner */}
        <div className="z-10">
          <h2 className="text-2xl font-bold text-white mb-2 leading-tight">
            Upload Anything. Understand Everything.
          </h2>
          <p className="text-white/60 text-sm max-w-md">
            Instantly decode prescriptions, agreements, bills, and notifications into plain, actionable insights. 100% private.
          </p>
        </div>
      </div>

      {/* Right side (Auth forms panel) */}
      <div className="col-span-1 lg:col-span-5 xl:col-span-4 flex flex-col justify-center p-8 sm:p-12 md:p-16 bg-bg-elevated relative">
        <div className="w-full max-w-sm mx-auto z-10">
          {/* Mobile only wordmark */}
          <div className="lg:hidden flex items-center gap-2 font-bold mb-8 text-black dark:text-white">
            <span className="text-brand-500 text-lg">◈</span> Clarify AI
          </div>
          {children}
        </div>
      </div>
    </div>
  );
}
