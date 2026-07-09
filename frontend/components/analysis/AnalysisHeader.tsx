"use client";

import React, { useState } from "react";
import { Download, Share2, Trash2, Globe, Calendar, FileText } from "lucide-react";
import { api } from "../../lib/api";
import { toast } from "sonner";
import { useRouter } from "next/navigation";

interface AnalysisHeaderProps {
  uploadId: string;
  title: string;
  docType: string;
  language: string;
  riskLevel: string;
  riskScore: number;
  date: string;
  thumbnailUrl: string | null;
}

export default function AnalysisHeader({
  uploadId,
  title,
  docType,
  language,
  riskLevel,
  riskScore,
  date,
  thumbnailUrl,
}: AnalysisHeaderProps) {
  const [isSharing, setIsSharing] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const router = useRouter();

  const handleExport = async () => {
    try {
      const url = api.analysis.getExportUrl(uploadId, null);
      // Create a temporary link to download
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `ClarifyAI_${title.replace(/\s+/g, "_")}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      toast.success("Analysis exported as PDF.");
    } catch {
      toast.error("Failed to export PDF.");
    }
  };

  const handleShare = async () => {
    setIsSharing(true);
    try {
      const res = await api.analysis.share(uploadId);
      const shareUrl = `${window.location.origin}${res.share_url}`;
      await navigator.clipboard.writeText(shareUrl);
      toast.success("Share link copied to clipboard!");
    } catch {
      toast.error("Failed to generate share link.");
    } finally {
      setIsSharing(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this document? This action cannot be undone.")) return;
    setIsDeleting(true);
    try {
      await api.uploads.delete(uploadId);
      toast.success("Document deleted.");
      router.push("/dashboard");
    } catch {
      toast.error("Failed to delete document.");
      setIsDeleting(false);
    }
  };

  return (
    <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 border-b border-border pb-6">
      {/* File Info */}
      <div className="flex items-center gap-4 min-w-0">
        <div className="w-16 h-16 rounded-2xl bg-bg-sunken border border-border flex items-center justify-center flex-shrink-0 text-muted-foreground font-bold">
          {thumbnailUrl ? (
            <img src={thumbnailUrl} alt={title} className="w-full h-full object-cover rounded-2xl" />
          ) : (
            <FileText className="w-8 h-8 text-brand-500" />
          )}
        </div>
        <div className="min-w-0 space-y-1.5">
          <h1 className="text-2xl font-extrabold tracking-tight text-foreground truncate">{title}</h1>
          <div className="flex flex-wrap items-center gap-2 text-xs font-semibold text-muted-foreground">
            <span className="capitalize px-2 py-0.5 rounded bg-bg-sunken border border-border">
              {docType.replace("_", " ")}
            </span>
            <span className="flex items-center gap-1">
              <Globe className="w-3.5 h-3.5" /> {language.toUpperCase()}
            </span>
            <span className="flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5" /> {new Date(date).toLocaleDateString()}
            </span>
          </div>
        </div>
      </div>

      {/* Quick Action buttons */}
      <div className="flex items-center gap-2.5 w-full md:w-auto">
        <button
          onClick={handleExport}
          className="flex-1 md:flex-initial flex items-center justify-center gap-2 py-2.5 px-4 border border-border rounded-xl bg-bg-elevated hover:bg-bg-base text-sm font-semibold transition-all active:scale-[0.98]"
        >
          <Download className="w-4 h-4" /> Export PDF
        </button>
        <button
          onClick={handleShare}
          disabled={isSharing}
          className="flex-1 md:flex-initial flex items-center justify-center gap-2 py-2.5 px-4 border border-border rounded-xl bg-bg-elevated hover:bg-bg-base text-sm font-semibold transition-all active:scale-[0.98] disabled:opacity-50"
        >
          <Share2 className="w-4 h-4" /> Share
        </button>
        <button
          onClick={handleDelete}
          disabled={isDeleting}
          className="p-2.5 border border-danger-100 rounded-xl bg-bg-elevated hover:bg-danger-50 text-danger-500 hover:text-danger-600 transition-all active:scale-[0.98] disabled:opacity-50"
          aria-label="Delete analysis"
        >
          <Trash2 className="w-4.5 h-4.5" />
        </button>
      </div>
    </div>
  );
}
