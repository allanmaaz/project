"use client";

import React from "react";
import { ShieldAlert, Users, Navigation, AlertTriangle, ShieldCheck, HelpCircle } from "lucide-react";

interface DispatchItem {
  priority: number;
  zone: string;
  urgency: string;
  assigned_team: string;
}

interface TeamAllocation {
  unit: string;
  status: string;
  personnel: number;
}

interface DisasterData {
  severity_index: number;
  affected_areas: string[];
  trapped_count_est: number;
  dispatch_queue: DispatchItem[];
  team_allocation: TeamAllocation[];
  safety_advisories: string[];
}

interface DisasterAnalysisProps {
  data: DisasterData;
}

export default function DisasterAnalysis({ data }: DisasterAnalysisProps) {
  if (!data) return null;

  const getSeverityColor = (idx: number) => {
    if (idx >= 8) return "bg-danger-500 text-white border-danger-600";
    if (idx >= 5) return "bg-warning-500 text-white border-warning-600";
    return "bg-success-500 text-white border-success-600";
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency.toLowerCase()) {
      case "critical":
      case "immediate":
        return "bg-danger-50 text-danger-700 dark:bg-danger-950/30 dark:text-danger-400 border-danger-200/50";
      case "high":
        return "bg-warning-50 text-warning-700 dark:bg-warning-950/30 dark:text-warning-400 border-warning-200/50";
      default:
        return "bg-neutral-50 text-neutral-700 dark:bg-neutral-800/40 dark:text-neutral-400 border-border";
    }
  };

  return (
    <div className="space-y-6">
      {/* 1. Header Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Severity Index Card */}
        <div className="p-6 rounded-3xl border border-border bg-bg-elevated shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-bold text-muted-foreground uppercase tracking-wider">Severity Index</h4>
            <ShieldAlert className="w-5 h-5 text-danger-500" />
          </div>
          <div className="mt-4 flex items-baseline space-x-2">
            <span className="text-4xl font-extrabold tracking-tight">{data.severity_index || 0}</span>
            <span className="text-sm text-muted-foreground">/ 10</span>
          </div>
          <div className="mt-4">
            <div className="w-full bg-neutral-100 dark:bg-neutral-800 rounded-full h-2 overflow-hidden">
              <div
                className={`h-full rounded-full ${
                  data.severity_index >= 8 ? "bg-danger-500" : data.severity_index >= 5 ? "bg-warning-500" : "bg-success-500"
                }`}
                style={{ width: `${(data.severity_index || 0) * 10}%` }}
              />
            </div>
            <p className="text-xs text-muted-foreground mt-2 font-semibold">
              {data.severity_index >= 8 ? "Critical Emergency Alert" : data.severity_index >= 5 ? "Moderate Flood Threat" : "Minimal/Local Flood Impact"}
            </p>
          </div>
        </div>

        {/* Trapped Estimation Card */}
        <div className="p-6 rounded-3xl border border-border bg-bg-elevated shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-bold text-muted-foreground uppercase tracking-wider">Est. Stranded Persons</h4>
            <Users className="w-5 h-5 text-brand-500" />
          </div>
          <div className="mt-4">
            <span className="text-4xl font-extrabold tracking-tight">{data.trapped_count_est || 0}</span>
            <p className="text-xs text-muted-foreground mt-4 font-semibold">
              Prioritized list mapped to active dispatch squads.
            </p>
          </div>
        </div>

        {/* Impacted Areas Card */}
        <div className="p-6 rounded-3xl border border-border bg-bg-elevated shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-bold text-muted-foreground uppercase tracking-wider">Affected Areas</h4>
            <Navigation className="w-5 h-5 text-warning-500" />
          </div>
          <div className="mt-4">
            <div className="flex flex-wrap gap-2">
              {data.affected_areas && data.affected_areas.length > 0 ? (
                data.affected_areas.map((area, idx) => (
                  <span
                    key={idx}
                    className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-neutral-100 dark:bg-neutral-800 text-foreground border border-border"
                  >
                    {area}
                  </span>
                ))
              ) : (
                <span className="text-xs text-muted-foreground italic">No specific areas detected.</span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 2. Dispatch Priority Queue & Resource Allocation */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Dispatch Queue Table */}
        <div className="p-6 rounded-3xl border border-border bg-bg-elevated shadow-sm">
          <div className="flex items-center justify-between border-b border-border pb-4 mb-4">
            <h3 className="text-base font-bold text-foreground">Rescue Dispatch Priority Queue</h3>
            <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-brand-50 text-brand-700 dark:bg-brand-950/30 dark:text-brand-400">
              AI Sorted
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-border text-xs font-bold text-muted-foreground uppercase tracking-wider">
                  <th className="pb-3 font-semibold">Zone / Target</th>
                  <th className="pb-3 font-semibold">Urgency</th>
                  <th className="pb-3 font-semibold">Assigned Unit</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/40 text-sm">
                {data.dispatch_queue && data.dispatch_queue.length > 0 ? (
                  data.dispatch_queue.map((item, idx) => (
                    <tr key={idx} className="hover:bg-neutral-50/50 dark:hover:bg-neutral-800/20">
                      <td className="py-3 font-semibold text-foreground flex items-center space-x-2">
                        <span className="inline-flex items-center justify-center w-5 h-5 text-xs font-extrabold rounded bg-brand-100 dark:bg-brand-900/40 text-brand-600 dark:text-brand-400">
                          {idx + 1}
                        </span>
                        <span>{item.zone}</span>
                      </td>
                      <td className="py-3">
                        <span className={`px-2 py-0.5 text-xs font-bold rounded border ${getUrgencyColor(item.urgency)}`}>
                          {item.urgency}
                        </span>
                      </td>
                      <td className="py-3 font-medium text-muted-foreground">{item.assigned_team || "Pending Assignment"}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={3} className="py-8 text-center text-muted-foreground italic">
                      No active dispatch tasks mapped.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Team Allocation Status */}
        <div className="p-6 rounded-3xl border border-border bg-bg-elevated shadow-sm">
          <div className="flex items-center justify-between border-b border-border pb-4 mb-4">
            <h3 className="text-base font-bold text-foreground">Rescue Resource Matrix</h3>
          </div>

          <div className="space-y-4">
            {data.team_allocation && data.team_allocation.length > 0 ? (
              data.team_allocation.map((team, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-2xl border border-border bg-bg-base flex items-center justify-between hover:shadow-sm transition-all"
                >
                  <div className="flex items-center space-x-3">
                    <div className="p-2.5 rounded-xl bg-brand-100 dark:bg-brand-900/40 text-brand-500">
                      <ShieldCheck className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="text-sm font-bold text-foreground">{team.unit}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">Personnel Assigned: {team.personnel}</p>
                    </div>
                  </div>
                  <span
                    className={`px-2.5 py-1 text-xs font-bold rounded-lg border ${
                      team.status.toLowerCase() === "active" || team.status.toLowerCase() === "deployed"
                        ? "bg-success-50 text-success-700 dark:bg-success-950/30 dark:text-success-400 border-success-200"
                        : "bg-warning-50 text-warning-700 dark:bg-warning-950/30 dark:text-warning-400 border-warning-200"
                    }`}
                  >
                    {team.status}
                  </span>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted-foreground italic py-8 text-center">No team allocations defined.</p>
            )}
          </div>
        </div>
      </div>

      {/* 3. Safety Advisories Card */}
      {data.safety_advisories && data.safety_advisories.length > 0 && (
        <div className="p-6 rounded-3xl border border-border bg-danger-500/5 dark:bg-danger-500/10 border-danger-500/20 shadow-sm space-y-4">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-5 h-5 text-danger-500" />
            <h3 className="text-base font-extrabold text-foreground">Emergency Safety & Dispatch Advisories</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
            {data.safety_advisories.map((advisory, idx) => (
              <div key={idx} className="flex items-start space-x-2.5 p-3 rounded-2xl bg-bg-elevated border border-border">
                <span className="inline-flex w-1.5 h-1.5 rounded-full bg-danger-500 mt-2 shrink-0" />
                <p className="text-muted-foreground font-semibold leading-relaxed">{advisory}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
