"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight, ShieldCheck, Sparkles, FileText, Check } from "lucide-react";
import { motion } from "framer-motion";

export default function LandingPage() {
  const features = [
    { title: "Prescriptions", desc: "Decode dosage info, generic compound names, and serious interactions.", icon: "💊" },
    { title: "Contracts & NDAs", desc: "Instantly detect liability loops, hidden fees, and exit conditions.", icon: "⚖️" },
    { title: "Invoices & Utility Bills", desc: "Identify extra fees, consumption summaries, and payment cycles.", icon: "🧾" },
    { title: "Scam Verification", desc: "Block phishing lures and urgency triggers with secure, safe responses.", icon: "🔒" },
  ];

  return (
    <div className="min-h-screen bg-[#06060a] text-white selection:bg-brand-500 selection:text-white overflow-hidden relative">
      {/* Background radial spotlights */}
      <div className="absolute top-[-20%] left-[-10%] w-[60dvw] h-[60dvw] rounded-full bg-brand-900/10 blur-[140px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[50dvw] h-[50dvw] rounded-full bg-indigo-950/15 blur-[120px] pointer-events-none" />

      {/* Header / Navbar */}
      <header className="max-w-7xl mx-auto px-6 py-6 flex items-center justify-between border-b border-white/5 relative z-10">
        <div className="flex items-center gap-2 font-bold text-sm select-none">
          <span className="text-brand-500 text-lg">◈</span> Clarify AI
        </div>
        <div className="flex items-center gap-4 text-xs font-semibold">
          <Link href="/login" className="text-white/60 hover:text-white transition-all">
            Sign In
          </Link>
          <Link
            href="/signup"
            className="py-2 px-4 rounded-xl bg-white text-black hover:opacity-90 active:scale-95 transition-all shadow-md"
          >
            Start Free
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-5xl mx-auto px-6 pt-20 pb-16 text-center space-y-8 relative z-10">
        {/* Eyebrow badge */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="inline-flex items-center gap-2 py-1 px-3 border border-white/10 bg-white/5 rounded-full text-[10px] uppercase font-bold tracking-widest text-brand-350"
        >
          <Sparkles className="w-3.5 h-3.5" /> Powered by Gemini 1.5 Flash
        </motion.div>

        {/* Hero title */}
        <motion.h1
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="text-4xl sm:text-6xl font-extrabold tracking-tight max-w-4xl mx-auto leading-[1.1]"
        >
          Upload Anything. <br />
          <span className="text-gradient-brand">Understand Everything.</span>
        </motion.h1>

        {/* Hero description */}
        <motion.p
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="text-sm sm:text-base text-white/60 max-w-2xl mx-auto leading-relaxed"
        >
          Clarify AI reads prescriptions, contracts, bank statements, scam messages, and screenshots — instantly converting complex language into clear, actionable advice.
        </motion.p>

        {/* Hero CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-3.5"
        >
          <Link
            href="/signup"
            className="w-full sm:w-auto flex items-center justify-center gap-2 py-3 px-6 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-bold text-sm transition-all active:scale-[0.98] shadow-lg shadow-brand-500/10"
          >
            Start Analyzing Free <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            href="/login"
            className="w-full sm:w-auto flex items-center justify-center gap-2 py-3 px-6 rounded-xl border border-white/10 hover:border-white/20 bg-white/5 hover:bg-white/10 text-white font-semibold text-sm transition-all active:scale-[0.98]"
          >
            Sign In
          </Link>
        </motion.div>
      </section>

      {/* Grid of core features */}
      <section className="max-w-7xl mx-auto px-6 py-16 relative z-10">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {features.map((feat, index) => (
            <div
              key={index}
              className="p-6 rounded-3xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.04] transition-all flex flex-col justify-between h-48"
            >
              <span className="text-3xl select-none">{feat.icon}</span>
              <div className="space-y-1 mt-4">
                <h4 className="text-sm font-bold text-white">{feat.title}</h4>
                <p className="text-xs text-white/50 leading-relaxed font-semibold">{feat.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Security callout section */}
      <section className="max-w-4xl mx-auto px-6 py-16 text-center space-y-6 relative z-10 border-t border-white/5">
        <ShieldCheck className="w-12 h-12 text-success-500 mx-auto" />
        <h2 className="text-2xl font-bold">Privacy First. No Training.</h2>
        <p className="text-xs text-white/50 max-w-xl mx-auto leading-relaxed font-semibold">
          All document files are stored in private user vaults and are encrypted at rest. 
          Our Google Gemini API connections are configured so that your sensitive document information is never stored or used to train public models.
        </p>
      </section>

      {/* Footer */}
      <footer className="max-w-7xl mx-auto px-6 py-8 border-t border-white/5 flex flex-col sm:flex-row justify-between items-center gap-4 text-[10px] text-white/40 font-semibold relative z-10">
        <span>© 2026 Clarify AI. All rights reserved.</span>
        <div className="flex gap-6">
          <Link href="/privacy" className="hover:text-white transition-all">Privacy Policy</Link>
          <Link href="/terms" className="hover:text-white transition-all">Terms of Service</Link>
        </div>
      </footer>
    </div>
  );
}
