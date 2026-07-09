"use client";

import React from "react";
import { FileText, Calendar, ShieldAlert } from "lucide-react";
import { useRouter } from "next/navigation";

interface HistoryCardProps {
  upload: {
    id: string;
    auto_title: string | null;
    original_filename: string | null;
    document_type: string | null;
    risk_level: string | null;
    risk_score: number;
    created_at: string;
    thumbnail_url: string | null;
    status: string;
  };
}

export default function HistoryCard({ upload }: HistoryCardProps) {
  const router = useRouter();

  const getRiskBadgeColor = (level: string | null) => {
    switch (level) {
      case "critical":
      case "high":
        return "bg-danger-50 text-danger-500 border-danger-100";
      case "medium":
        return "bg-warning-50 text-warning-500 border-warning-100";
      case "low":
        return "bg-brand-50 text-brand-500 border-brand-100";
      default:
        return "bg-neutral-50 text-muted-foreground border-neutral-100";
    }
  };

  const getThumbnailBackground = (type: string | null) => {
    switch (type) {
      case "medical":
        return "bg-success-500/10 text-success-500";
      case "legal_contract":
        return "bg-danger-500/10 text-danger-500";
      case "bill_utility":
      case "bill_bank":
        return "bg-brand-500/10 text-brand-500";
      case "scam_message":
        return "bg-warning-500/10 text-warning-500";
      default:
        return "bg-neutral-500/10 text-neutral-500";
    }
  };

  return (
    <div
      onClick={() => router.push(`/analysis/${upload.id}`)}
      className="group p-5 bg-bg-elevated border border-border rounded-2xl hover:border-brand-350 cursor-pointer shadow-xs hover:scale-[1.01] hover:shadow-sm transition-all flex flex-col justify-between h-48"
    >
      <div className="space-y-4">
        {/* Top badges */}
        <div className="flex items-center justify-between gap-2">
          <span className="text-[10px] uppercase font-bold tracking-widest text-muted-foreground capitalize">
            {upload.document_type?.replace("_", " ") || "Unknown Type"}
          </span>
          {upload.risk_level && (
            <span
              className={`text-[9px] uppercase font-extrabold px-2 py-0.5 rounded-full border ${getRiskBadgeColor(
                upload.risk_level
              )}`}
            >
              {upload.risk_level}
            </span>
          )}
        </div>

        {/* File icon / Title */}
        <div className="flex items-start gap-3.5">
          <div
            className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 text-sm font-bold ${getThumbnailBackground(
              upload.document_type
            )}`}
          >
            {upload.thumbnail_url ? (
              <img
                src={upload.thumbnail_url}
                alt="thumb"
                className="w-full h-full object-cover rounded-lg"
              />
            ) : (
              <FileText className="w-5.5 h-5.5" />
            )}
          </div>
          <div className="min-w-0">
            <h4 className="text-sm font-extrabold leading-snug text-foreground truncate group-hover:text-brand-500 transition-all">
              {upload.auto_title || upload.original_filename}
            </h4>
            <p className="text-[11px] text-muted-foreground truncate mt-0.5">
              {upload.original_filename}
            </p>
          </div>
        </div>
      </div>

      {/* Date metadata */}
      <div className="flex items-center justify-between border-t border-border/40 pt-3 text-[10px] font-semibold text-muted-foreground">
        <span className="flex items-center gap-1">
          <Calendar className="w-3.5 h-3.5" /> {new Date(upload.created_at).toLocaleDateString()}
        </span>
        <span className="capitalize">{upload.status}</span>
      </div>
    </div>
  );
}
