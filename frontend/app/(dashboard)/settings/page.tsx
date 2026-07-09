"use client";

import React, { useState, useEffect } from "react";
import { api } from "../../../lib/api";
import { useTheme } from "next-themes";
import { toast } from "sonner";
import { Loader2, Settings, User, Eye, Trash2, ArrowUpCircle } from "lucide-react";
import { createBrowserSupabaseClient } from "../../../lib/supabase";
import { useRouter } from "next/navigation";

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const [user, setUser] = useState<any>(null);
  const [fullName, setFullName] = useState("");
  const [preferredLang, setPreferredLang] = useState("en");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isUpgrading, setIsUpgrading] = useState(false);
  const supabase = createBrowserSupabaseClient();
  const router = useRouter();

  useEffect(() => {
    const loadUser = async () => {
      setIsLoading(true);
      try {
        const data = await api.users.me();
        setUser(data);
        setFullName(data.full_name || "");
        setPreferredLang(data.preferred_language || "en");
      } catch {
        toast.error("Failed to load user profile.");
      } finally {
        setIsLoading(false);
      }
    };
    loadUser();
  }, []);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      const updated = await api.users.update({
        full_name: fullName,
        preferred_language: preferredLang,
      });
      setUser(updated);
      toast.success("Profile preferences saved.");
    } catch {
      toast.error("Failed to save changes.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleSimulatedUpgrade = async () => {
    setIsUpgrading(true);
    try {
      const res = await api.users.upgradePlan();
      setUser(res);
      toast.success("Congratulations! You have been upgraded to the Pro Plan (simulated free).");
    } catch {
      toast.error("Upgrade failed.");
    } finally {
      setIsUpgrading(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (!confirm("CRITICAL WARNING: This will permanently delete your account, cancel subscriptions, and purge all your document uploads. This action is irreversible. Proceed?")) return;
    try {
      await api.users.deleteAccount();
      toast.success("Account and data deleted.");
      await supabase.auth.signOut();
      router.push("/signup");
    } catch {
      toast.error("Failed to delete account.");
    }
  };

  if (isLoading) {
    return (
      <div className="h-[70dvh] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-brand-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight">Account Settings</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Customize UI preferences, update user profiles, or manage subscription configurations.
        </p>
      </div>

      {/* Profile Form */}
      <form onSubmit={handleSaveProfile} className="p-6 rounded-3xl border border-border bg-bg-elevated shadow-sm space-y-4">
        <h3 className="text-base font-bold flex items-center gap-2">
          <User className="w-5 h-5 text-brand-500" /> Profile Settings
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">
              Display Name
            </label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full py-2 px-3 border border-border rounded-xl bg-bg-base text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all font-semibold"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">
              AI Output Language
            </label>
            <select
              value={preferredLang}
              onChange={(e) => setPreferredLang(e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-xl bg-bg-base text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all font-semibold"
            >
              <option value="en">English</option>
              <option value="es">Español (Spanish)</option>
              <option value="fr">Français (French)</option>
              <option value="de">Deutsch (German)</option>
              <option value="pt">Português (Portuguese)</option>
            </select>
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <button
            type="submit"
            disabled={isSaving}
            className="flex items-center gap-2 py-2 px-4 bg-black dark:bg-white text-white dark:text-black font-semibold text-xs rounded-xl hover:opacity-90 active:scale-95 transition-all"
          >
            {isSaving && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
            Save Settings
          </button>
        </div>
      </form>

      {/* Appearance card */}
      <div className="p-6 rounded-3xl border border-border bg-bg-elevated shadow-sm space-y-4">
        <h3 className="text-base font-bold flex items-center gap-2">
          <Eye className="w-5 h-5 text-brand-500" /> Appearance & Theme
        </h3>
        <p className="text-xs text-muted-foreground leading-normal">
          Toggle theme styling preferences between light mode, dark mode, or system default settings.
        </p>

        <div className="flex gap-2">
          {["light", "dark", "system"].map((t) => (
            <button
              key={t}
              onClick={() => setTheme(t)}
              className={`flex-1 py-2 px-3 text-xs font-semibold border rounded-xl capitalize transition-all ${
                theme === t
                  ? "border-brand-500 bg-brand-50/50 dark:bg-brand-900/10 text-brand-500"
                  : "border-border bg-bg-base hover:bg-neutral-100 dark:hover:bg-neutral-900"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Upgrade membership card */}
      {user && (
        <div className="p-6 rounded-3xl border border-border bg-bg-elevated shadow-sm space-y-4">
          <h3 className="text-base font-bold flex items-center gap-2">
            <ArrowUpCircle className="w-5 h-5 text-brand-500" /> Manage Membership Plan
          </h3>
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <p className="text-sm font-bold capitalize">Active Plan: {user.plan}</p>
              <p className="text-xs text-muted-foreground">
                {user.plan === "free"
                  ? "Unlock unlimited document uploads and 4x higher chat limits."
                  : "Thank you for supporting Clarify AI!"}
              </p>
            </div>
            {user.plan === "free" && (
              <button
                onClick={handleSimulatedUpgrade}
                disabled={isUpgrading}
                className="flex items-center gap-2 py-2 px-4 bg-brand-500 text-white font-semibold text-xs rounded-xl hover:opacity-90 active:scale-95 transition-all"
              >
                {isUpgrading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                Upgrade to Pro (Free)
              </button>
            )}
          </div>
        </div>
      )}

      {/* Danger Zone */}
      <div className="p-6 rounded-3xl border border-danger-100 bg-danger-50/5 shadow-sm space-y-4">
        <h3 className="text-base font-bold text-danger-500 flex items-center gap-2">
          <Trash2 className="w-5 h-5" /> Danger Zone
        </h3>
        <p className="text-xs text-muted-foreground leading-normal">
          Once deleted, your account can never be restored. All document scan summaries, metadata records, and transaction logs will be permanently deleted from our servers.
        </p>
        <button
          onClick={handleDeleteAccount}
          className="w-full sm:w-auto py-2 px-4 border border-danger-200 hover:bg-danger-50 text-danger-500 font-semibold text-xs rounded-xl transition-all active:scale-[0.98]"
        >
          Permanently Delete Account
        </button>
      </div>
    </div>
  );
}
