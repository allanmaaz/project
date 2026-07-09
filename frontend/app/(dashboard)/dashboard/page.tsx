"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "../../../lib/api";
import { createBrowserSupabaseClient } from "../../../lib/supabase";
import {
  UploadCloud,
  History,
  AlertTriangle,
  FileText,
  Clock,
  ArrowRight,
  TrendingUp,
  Shield,
  Loader2,
} from "lucide-react";
import { motion } from "framer-motion";
import { toast } from "sonner";

export default function DashboardPage() {
  const [stats, setStats] = useState<any>(null);
  const [recentUploads, setRecentUploads] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [userName, setUserName] = useState("User");
  const supabase = createBrowserSupabaseClient();
  const router = useRouter();

  useEffect(() => {
    const loadDashboardData = async () => {
      setIsLoading(true);
      try {
        const { data } = await supabase.auth.getSession();
        if (data.session?.user) {
          setUserName(data.session.user.user_metadata?.full_name ?? "User");
        }

        const statsData = await api.users.getStats();
        setStats(statsData);

        const uploadsData = await api.uploads.list({ page: 1, per_page: 5 });
        setRecentUploads(uploadsData.items);
      } catch (err: any) {
        toast.error("Failed to load dashboard metrics.");
      } finally {
        setIsLoading(false);
      }
    };
    loadDashboardData();
  }, []);

  if (isLoading) {
    return (
      <div className="h-[70dvh] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-brand-500 animate-spin" />
      </div>
    );
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 100 } },
  };

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="show" className="space-y-8">
      {/* Header Greeting */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Hello, {userName}</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Upload documents to instantly understand them in plain language.
          </p>
        </div>
        <Link
          href="/upload"
          className="flex items-center gap-2 px-5 py-2.5 bg-black dark:bg-white text-white dark:text-black font-semibold text-sm rounded-xl hover:opacity-90 active:scale-95 transition-all shadow-md"
        >
          <UploadCloud className="w-4 h-4" />
          Upload Document
        </Link>
      </div>

      {/* Grid Stats */}
      {stats && (
        <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-6 rounded-2xl border border-border bg-bg-elevated shadow-sm flex items-center justify-between">
            <div className="space-y-1">
              <span className="text-xs uppercase tracking-wider font-semibold text-muted-foreground">
                Total Uploads
              </span>
              <p className="text-3xl font-extrabold">{stats.total_uploads}</p>
            </div>
            <div className="p-3 rounded-xl bg-brand-500/10 text-brand-500">
              <FileText className="w-6 h-6" />
            </div>
          </div>

          <div className="p-6 rounded-2xl border border-border bg-bg-elevated shadow-sm flex items-center justify-between">
            <div className="space-y-1">
              <span className="text-xs uppercase tracking-wider font-semibold text-muted-foreground">
                This Month (Free Limit)
              </span>
              <p className="text-3xl font-extrabold">
                {stats.uploads_this_month} <span className="text-sm text-muted-foreground">/ {stats.plan_limit}</span>
              </p>
            </div>
            <div className="p-3 rounded-xl bg-indigo-500/10 text-indigo-500">
              <Clock className="w-6 h-6" />
            </div>
          </div>

          <div className="p-6 rounded-2xl border border-border bg-bg-elevated shadow-sm flex items-center justify-between">
            <div className="space-y-1">
              <span className="text-xs uppercase tracking-wider font-semibold text-muted-foreground">
                Monthly Spending tracked
              </span>
              <p className="text-3xl font-extrabold">
                ${stats.spending_total_this_month.toFixed(2)}
              </p>
            </div>
            <div className="p-3 rounded-xl bg-success-500/10 text-success-500">
              <TrendingUp className="w-6 h-6" />
            </div>
          </div>
        </motion.div>
      )}

      {/* Main sections */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Recent Uploads List */}
        <motion.div variants={itemVariants} className="lg:col-span-8 space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-bold">Recent Uploads</h2>
            <Link
              href="/history"
              className="text-xs text-brand-500 font-semibold hover:underline flex items-center gap-1"
            >
              See all history <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          {recentUploads.length > 0 ? (
            <div className="space-y-3">
              {recentUploads.map((item) => (
                <div
                  key={item.id}
                  onClick={() => router.push(`/analysis/${item.id}`)}
                  className="p-4 rounded-xl border border-border bg-bg-elevated hover:bg-bg-base hover:scale-[1.01] transition-all cursor-pointer flex items-center justify-between shadow-xs group"
                >
                  <div className="flex items-center gap-4 min-w-0">
                    <div className="w-12 h-12 rounded-lg bg-bg-sunken border border-border flex items-center justify-center flex-shrink-0 text-muted-foreground font-bold">
                      {item.thumbnail_url ? (
                        <img
                          src={item.thumbnail_url}
                          alt="thumbnail"
                          className="w-full h-full object-cover rounded-lg"
                        />
                      ) : (
                        "📄"
                      )}
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-semibold truncate group-hover:text-brand-500 transition-all">
                        {item.auto_title || item.original_filename}
                      </p>
                      <p className="text-xs text-muted-foreground capitalize mt-0.5">
                        {item.document_type?.replace("_", " ")} &bull;{" "}
                        {new Date(item.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 flex-shrink-0">
                    {item.risk_level && item.risk_level !== "informational" && (
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                          item.risk_level === "critical" || item.risk_level === "high"
                            ? "bg-danger-50 text-danger-500"
                            : "bg-warning-50 text-warning-500"
                        }`}
                      >
                        {item.risk_level}
                      </span>
                    )}
                    <span className="text-xs font-semibold px-2 py-0.5 rounded bg-bg-sunken border border-border capitalize">
                      {item.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="border border-dashed border-border rounded-2xl p-12 text-center bg-bg-elevated/40">
              <UploadCloud className="w-8 h-8 text-muted-foreground mx-auto mb-3" />
              <p className="text-sm font-semibold text-foreground">No documents uploaded yet</p>
              <p className="text-xs text-muted-foreground mt-1 mb-4 max-w-xs mx-auto">
                Upload a bill, prescription, contract, or message to see the AI details here.
              </p>
              <Link
                href="/upload"
                className="inline-flex items-center gap-2 px-4 py-2 border border-border rounded-lg bg-bg-base hover:bg-neutral-100 dark:hover:bg-neutral-900 text-xs font-semibold transition-all"
              >
                Scan First Document
              </Link>
            </div>
          )}
        </motion.div>

        {/* Security & Platform summary info */}
        <motion.div variants={itemVariants} className="lg:col-span-4 space-y-6">
          <h2 className="text-lg font-bold">Privacy & Security</h2>
          
          <div className="p-6 rounded-2xl border border-border bg-bg-elevated shadow-sm space-y-4">
            <div className="flex gap-4">
              <div className="p-2.5 rounded-lg bg-success-500/10 text-success-500 flex-shrink-0">
                <Shield className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-semibold">100% Encrypted Storage</h4>
                <p className="text-xs text-muted-foreground mt-1 leading-normal">
                  All uploaded documents are encrypted at rest inside private user storage vaults. Nobody but you can access them.
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="p-2.5 rounded-lg bg-brand-500/10 text-brand-500 flex-shrink-0">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-semibold">Not Used For Training</h4>
                <p className="text-xs text-muted-foreground mt-1 leading-normal">
                  Our integration endpoints are configured so that Google Gemini never saves or trains on your document data.
                </p>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}
