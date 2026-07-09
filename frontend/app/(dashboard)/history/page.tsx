"use client";

import React, { useState, useEffect } from "react";
import { api } from "../../../lib/api";
import HistoryFilters from "../../../components/history/HistoryFilters";
import HistoryCard from "../../../components/history/HistoryCard";
import { Loader2, History as HistoryIcon } from "lucide-react";
import { toast } from "sonner";

export default function HistoryPage() {
  const [uploads, setUploads] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [query, setQuery] = useState("");
  const [docType, setDocType] = useState("all");
  const [riskLevel, setRiskLevel] = useState("all");
  const [isLoading, setIsLoading] = useState(true);

  // Debounced search queries
  useEffect(() => {
    const fetchHistory = async () => {
      setIsLoading(true);
      try {
        const res = await api.uploads.list({
          page,
          per_page: 12,
          q: query || undefined,
          doc_type: docType,
          risk_level: riskLevel,
        });
        setUploads(res.items);
        setTotal(res.total);
      } catch {
        toast.error("Failed to load document history.");
      } finally {
        setIsLoading(false);
      }
    };
    fetchHistory();
  }, [page, query, docType, riskLevel]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight">Document History</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Review, filter, and search all your analyzed documents.
        </p>
      </div>

      {/* Toolbar filters */}
      <HistoryFilters
        query={query}
        setQuery={setQuery}
        docType={docType}
        setDocType={setDocType}
        riskLevel={riskLevel}
        setRiskLevel={setRiskLevel}
      />

      {/* Grid listing */}
      {isLoading ? (
        <div className="h-[40dvh] flex items-center justify-center">
          <Loader2 className="w-8 h-8 text-brand-500 animate-spin" />
        </div>
      ) : uploads.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
          {uploads.map((upload) => (
            <HistoryCard key={upload.id} upload={upload} />
          ))}
        </div>
      ) : (
        <div className="border border-dashed border-border rounded-3xl p-16 text-center bg-bg-elevated/40 max-w-lg mx-auto">
          <HistoryIcon className="w-10 h-10 text-muted-foreground/60 mx-auto mb-3" />
          <p className="text-sm font-bold text-foreground">No documents found</p>
          <p className="text-xs text-muted-foreground mt-1 mb-4 leading-normal">
            We couldn&apos;t find any documents matching your filters or search keywords. Try adjusting your query.
          </p>
          <button
            onClick={() => {
              setQuery("");
              setDocType("all");
              setRiskLevel("all");
            }}
            className="px-4 py-2 border border-border rounded-lg bg-bg-base hover:bg-neutral-100 text-xs font-semibold transition-all"
          >
            Clear All Filters
          </button>
        </div>
      )}
    </div>
  );
}
