"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { createBrowserSupabaseClient } from "../../lib/supabase";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  History,
  BarChart2,
  Settings,
  LogOut,
  ChevronLeft,
  ChevronRight,
  UploadCloud,
  User,
  Search,
} from "lucide-react";
import { toast } from "sonner";
import CommandPalette from "./CommandPalette";

export default function Sidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [userName, setUserName] = useState<string | null>(null);
  const [isCommandOpen, setIsCommandOpen] = useState(false);
  const [provider, setProvider] = useState("gemini");
  const pathname = usePathname();
  const router = useRouter();
  const supabase = createBrowserSupabaseClient();

  useEffect(() => {
    const fetchUser = async () => {
      const { data } = await supabase.auth.getSession();
      if (data.session?.user) {
        setUserEmail(data.session.user.email ?? null);
        setUserName(data.session.user.user_metadata?.full_name ?? "User");
      }
    };
    fetchUser();
    
    // Load active provider from local storage — but verify Ollama is reachable first
    if (typeof window !== "undefined") {
      const saved = window.localStorage.getItem("llm-provider") || "gemini";
      if (saved === "ollama") {
        // Health-check Ollama before trusting the saved value
        fetch("http://localhost:11434/api/tags", { signal: AbortSignal.timeout(1500) })
          .then(() => setProvider("ollama"))
          .catch(() => {
            // Ollama not running — silently fall back to Gemini
            window.localStorage.setItem("llm-provider", "gemini");
            window.dispatchEvent(new Event("llm-provider-changed"));
            setProvider("gemini");
          });
      } else {
        setProvider("gemini");
      }
    }
    
    // Listen for custom Cmd+K key combo for command palette
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setIsCommandOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const toggleProvider = (newProvider: string) => {
    setProvider(newProvider);
    if (typeof window !== "undefined") {
      window.localStorage.setItem("llm-provider", newProvider);
      window.dispatchEvent(new Event("llm-provider-changed"));
    }
    if (newProvider === "ollama") {
      toast.error("Ollama requires a local install running on port 11434. Chat will auto-fallback to Gemini if unavailable.", { duration: 5000 });
    } else {
      toast.success("Switched to Gemini (Cloud AI)");
    }
  };

  const handleLogout = async () => {
    try {
      await supabase.auth.signOut();
      toast.success("Logged out successfully.");
      router.push("/login");
    } catch {
      toast.error("Error signing out.");
    }
  };

  const navItems = [
    { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { label: "Upload File", href: "/upload", icon: UploadCloud },
    { label: "History", href: "/history", icon: History },
    { label: "Stats & Analytics", href: "/stats", icon: BarChart2 },
  ];

  return (
    <div
      className={`hidden lg:flex flex-col h-screen bg-bg-elevated border-r border-border transition-all duration-300 relative ${
        isCollapsed ? "w-16" : "w-60"
      }`}
    >
      {/* Collapse Toggle */}
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="absolute top-6 -right-3 p-1 rounded-full border border-border bg-bg-elevated text-muted-foreground hover:text-foreground shadow-sm z-50 transition-all hover:scale-105"
      >
        {isCollapsed ? <ChevronRight className="w-4.5 h-4.5" /> : <ChevronLeft className="w-4.5 h-4.5" />}
      </button>

      {/* Header / Logo */}
      <div className="p-6 flex items-center gap-3 overflow-hidden select-none">
        <span className="text-brand-500 font-bold text-xl flex-shrink-0">◈</span>
        <AnimatePresence>
          {!isCollapsed && (
            <motion.span
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              className="font-bold text-base tracking-tight"
            >
              Clarify AI
            </motion.span>
          )}
        </AnimatePresence>
      </div>

      {/* Quick Search Shortcut Button */}
      <div className="px-4 mb-4">
        <button
          onClick={() => setIsCommandOpen(true)}
          className={`flex items-center gap-2 text-left w-full py-2 border border-border rounded-lg bg-bg-base hover:bg-neutral-100 dark:hover:bg-neutral-900 transition-all ${
            isCollapsed ? "px-2 justify-center" : "px-3"
          }`}
        >
          <Search className="w-4 h-4 text-muted-foreground flex-shrink-0" />
          {!isCollapsed && (
            <div className="flex justify-between items-center w-full text-xs text-muted-foreground font-semibold">
              <span>Quick search...</span>
              <kbd className="bg-bg-elevated border border-border px-1.5 py-0.5 rounded text-[10px] font-sans">
                ⌘K
              </kbd>
            </div>
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 space-y-1.5">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 py-2.5 rounded-lg text-sm font-semibold transition-all relative ${
                isActive
                  ? "text-brand-500 bg-brand-50/50 dark:bg-brand-900/10"
                  : "text-muted-foreground hover:text-foreground hover:bg-bg-base"
              } ${isCollapsed ? "px-2 justify-center" : "px-3"}`}
            >
              <Icon className={`w-5 h-5 flex-shrink-0 ${isActive ? "text-brand-500" : ""}`} />
              {!isCollapsed && <span>{item.label}</span>}
              {isActive && !isCollapsed && (
                <motion.div
                  layoutId="active-indicator"
                  className="absolute left-0 top-1/4 bottom-1/4 w-1 bg-brand-500 rounded-r"
                />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer User Info */}
      <div className="p-4 border-t border-border flex flex-col gap-2 bg-bg-sunken/40">
        {/* AI Engine Selector */}
        {!isCollapsed ? (
          <div className="bg-bg-base border border-border rounded-lg p-1 flex gap-1 items-center mb-1">
            <button
              onClick={() => toggleProvider("gemini")}
              className={`flex-1 flex items-center justify-center gap-1.5 py-1 px-2 rounded-md text-[10px] font-bold transition-all ${
                provider === "gemini"
                  ? "bg-brand-500 text-white shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <span>☁️</span> Gemini
            </button>
            <button
              onClick={() => toggleProvider("ollama")}
              className={`flex-1 flex items-center justify-center gap-1.5 py-1 px-2 rounded-md text-[10px] font-bold transition-all ${
                provider === "ollama"
                  ? "bg-brand-500 text-white shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <span>💻</span> Ollama
            </button>
          </div>
        ) : (
          <button
            onClick={() => toggleProvider(provider === "gemini" ? "ollama" : "gemini")}
            className="w-full flex items-center justify-center py-1.5 rounded-lg hover:bg-bg-base text-xs transition-all border border-border mb-1"
            title={`Active AI: ${provider === "gemini" ? "Gemini (Cloud)" : "Ollama (Local)"}. Click to toggle.`}
          >
            <span>{provider === "gemini" ? "☁️" : "💻"}</span>
          </button>
        )}

        <div className={`flex items-center gap-3 overflow-hidden ${isCollapsed ? "justify-center" : ""}`}>
          <div className="w-8 h-8 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-500 flex items-center justify-center font-bold text-sm flex-shrink-0 uppercase">
            {userName ? userName[0] : <User className="w-4 h-4" />}
          </div>
          {!isCollapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold truncate text-foreground">{userName || "User"}</p>
              <p className="text-[10px] text-muted-foreground truncate">{userEmail || ""}</p>
            </div>
          )}
        </div>

        <Link
          href="/settings"
          className={`flex items-center gap-3 py-2 rounded-lg text-xs font-semibold text-muted-foreground hover:text-foreground transition-all hover:bg-bg-base ${
            isCollapsed ? "justify-center" : "px-3"
          }`}
        >
          <Settings className="w-4 h-4 flex-shrink-0" />
          {!isCollapsed && <span>Settings</span>}
        </Link>

        <button
          onClick={handleLogout}
          className={`flex items-center gap-3 py-2 rounded-lg text-xs font-semibold text-danger-500 hover:text-danger-600 hover:bg-danger-50/20 transition-all ${
            isCollapsed ? "justify-center" : "px-3"
          }`}
        >
          <LogOut className="w-4 h-4 flex-shrink-0" />
          {!isCollapsed && <span>Logout</span>}
        </button>
      </div>

      {/* Command Palette Modal */}
      <CommandPalette isOpen={isCommandOpen} onClose={() => setIsCommandOpen(false)} />
    </div>
  );
}
