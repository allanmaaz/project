"use client";

import React, { useState, useEffect } from "react";
import { api } from "../../../lib/api";
import { Loader2, DollarSign, FileText, CheckCircle2, TrendingUp, AlertTriangle } from "lucide-react";
import { toast } from "sonner";

export default function StatsPage() {
  const [stats, setStats] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadStats = async () => {
      setIsLoading(true);
      try {
        const data = await api.users.getStats();
        setStats(data);
      } catch {
        toast.error("Failed to load statistics.");
      } finally {
        setIsLoading(false);
      }
    };
    loadStats();
  }, []);

  if (isLoading) {
    return (
      <div className="h-[70dvh] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-brand-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight">Stats & Analytics</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Aggregated insights, monthly budget trackers, and risk factor distributions.
        </p>
      </div>

      {stats && (
        <>
          {/* Card Summary row */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="p-5 rounded-2xl border border-border bg-bg-elevated flex items-center gap-4 shadow-xs">
              <div className="p-3 bg-brand-500/10 text-brand-500 rounded-xl">
                <FileText className="w-5.5 h-5.5" />
              </div>
              <div>
                <span className="text-[10px] uppercase font-bold text-muted-foreground">Total Scans</span>
                <p className="text-2xl font-extrabold mt-0.5">{stats.total_uploads}</p>
              </div>
            </div>

            <div className="p-5 rounded-2xl border border-border bg-bg-elevated flex items-center gap-4 shadow-xs">
              <div className="p-3 bg-success-500/10 text-success-500 rounded-xl">
                <DollarSign className="w-5.5 h-5.5" />
              </div>
              <div>
                <span className="text-[10px] uppercase font-bold text-muted-foreground">Budget Tracked</span>
                <p className="text-2xl font-extrabold mt-0.5">${stats.spending_total_this_month.toFixed(2)}</p>
              </div>
            </div>

            <div className="p-5 rounded-2xl border border-border bg-bg-elevated flex items-center gap-4 shadow-xs">
              <div className="p-3 bg-indigo-500/10 text-indigo-500 rounded-xl">
                <CheckCircle2 className="w-5.5 h-5.5" />
              </div>
              <div>
                <span className="text-[10px] uppercase font-bold text-muted-foreground">Usage Left</span>
                <p className="text-2xl font-extrabold mt-0.5">{stats.uploads_remaining}</p>
              </div>
            </div>

            <div className="p-5 rounded-2xl border border-border bg-bg-elevated flex items-center gap-4 shadow-xs">
              <div className="p-3 bg-warning-500/10 text-warning-500 rounded-xl">
                <TrendingUp className="w-5.5 h-5.5" />
              </div>
              <div>
                <span className="text-[10px] uppercase font-bold text-muted-foreground">Active Plan</span>
                <p className="text-2xl font-extrabold mt-0.5 capitalize">{stats.plan}</p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Document Types card */}
            <div className="p-6 rounded-3xl border border-border bg-bg-elevated shadow-sm space-y-4">
              <h3 className="text-base font-bold">Document Category Distribution</h3>
              <div className="space-y-3">
                {stats.document_types_breakdown && stats.document_types_breakdown.length > 0 ? (
                  stats.document_types_breakdown.map((item: any, idx: number) => (
                    <div key={idx} className="space-y-1.5">
                      <div className="flex justify-between items-center text-xs font-semibold">
                        <span className="capitalize">{item.name.replace("_", " ")}</span>
                        <span>{item.value} uploads</span>
                      </div>
                      <div className="w-full bg-bg-sunken h-2 rounded-full overflow-hidden">
                        <div
                          className="bg-brand-500 h-full"
                          style={{
                            width: `${(item.value / Math.max(stats.total_uploads, 1)) * 100}%`,
                          }}
                        />
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-muted-foreground py-6 text-center">No categories to display yet.</p>
                )}
              </div>
            </div>

            {/* Risk Index breakdowns */}
            <div className="p-6 rounded-3xl border border-border bg-bg-elevated shadow-sm space-y-4">
              <h3 className="text-base font-bold">Risk Factors Identified</h3>
              <div className="space-y-4">
                {Object.keys(stats.risk_breakdown).length > 0 ? (
                  Object.entries(stats.risk_breakdown).map(([level, count]: [string, any], idx) => {
                    let barColor = "bg-success-500";
                    if (level === "critical" || level === "high") barColor = "bg-danger-500";
                    else if (level === "medium") barColor = "bg-warning-500";
                    
                    return (
                      <div key={idx} className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-2 text-xs font-semibold capitalize min-w-[100px]">
                          <AlertTriangle className={`w-4 h-4 ${level === "high" || level === "critical" ? "text-danger-500" : "text-muted-foreground"}`} />
                          <span>{level}</span>
                        </div>
                        <div className="flex-1 bg-bg-sunken h-2 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${barColor}`}
                            style={{
                              width: `${(count / Math.max(stats.total_uploads, 1)) * 100}%`,
                            }}
                          />
                        </div>
                        <span className="text-xs font-bold text-muted-foreground w-12 text-right">
                          {count}
                        </span>
                      </div>
                    );
                  })
                ) : (
                  <p className="text-xs text-muted-foreground py-6 text-center">No risk indexes computed yet.</p>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
