"use client";

import React from "react";
import { Search } from "lucide-react";

interface HistoryFiltersProps {
  query: string;
  setQuery: (q: string) => void;
  docType: string;
  setDocType: (t: string) => void;
  riskLevel: string;
  setRiskLevel: (r: string) => void;
}

export default function HistoryFilters({
  query,
  setQuery,
  docType,
  setDocType,
  riskLevel,
  setRiskLevel,
}: HistoryFiltersProps) {
  const documentTypes = [
    { label: "All Types", value: "all" },
    { label: "Medical", value: "medical" },
    { label: "Contract", value: "legal_contract" },
    { label: "Utility Bill", value: "bill_utility" },
    { label: "Bank Statement", value: "bill_bank" },
    { label: "Government", value: "government" },
    { label: "Receipt/Invoice", value: "receipt_invoice" },
    { label: "Scam Alert", value: "scam_message" },
    { label: "Screenshot", value: "screenshot_ui" },
  ];

  const riskLevels = [
    { label: "All Risks", value: "all" },
    { label: "Critical", value: "critical" },
    { label: "High", value: "high" },
    { label: "Medium", value: "medium" },
    { label: "Low", value: "low" },
    { label: "Informational", value: "informational" },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-12 gap-4 bg-bg-elevated border border-border p-4 rounded-2xl shadow-xs">
      {/* Search Input */}
      <div className="relative md:col-span-6">
        <Search className="w-4.5 h-4.5 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search by filename or title..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full pl-9 pr-4 py-2 border border-border rounded-xl bg-bg-base text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all font-semibold"
        />
      </div>

      {/* Doc type Filter */}
      <div className="md:col-span-3">
        <select
          value={docType}
          onChange={(e) => setDocType(e.target.value)}
          className="w-full px-3 py-2 border border-border rounded-xl bg-bg-base text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all font-semibold"
        >
          {documentTypes.map((type) => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
      </div>

      {/* Risk level filter */}
      <div className="md:col-span-3">
        <select
          value={riskLevel}
          onChange={(e) => setRiskLevel(e.target.value)}
          className="w-full px-3 py-2 border border-border rounded-xl bg-bg-base text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all font-semibold"
        >
          {riskLevels.map((risk) => (
            <option key={risk.value} value={risk.value}>
              {risk.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
