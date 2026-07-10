"use client";

import React from "react";
import { Detection } from "./DetectionViewer";
import { Users, Truck, AlertTriangle, ShieldCheck, Cpu, Package } from "lucide-react";

interface DetectionPanelProps {
  detections: Detection[];
  hoveredIndex: number | null;
  setHoveredIndex: (index: number | null) => void;
}

const CATEGORY_DEF = {
  People: {
    labels: ["person"],
    icon: Users,
    color: "text-red-400",
    bg: "bg-red-500/10",
    border: "border-red-500/20",
  },
  Vehicles: {
    labels: ["car", "truck", "bus", "motorcycle", "bicycle", "boat"],
    icon: Truck,
    color: "text-amber-400",
    bg: "bg-amber-500/10",
    border: "border-amber-500/20",
  },
  Hazards: {
    labels: ["fire", "knife", "gun", "scissors", "stop sign"],
    icon: AlertTriangle,
    color: "text-red-500",
    bg: "bg-red-600/10",
    border: "border-red-600/20",
  },
  Other: {
    labels: [] as string[],
    icon: Package,
    color: "text-muted-foreground",
    bg: "bg-bg-sunken/40",
    border: "border-border",
  },
};

const allKnownLabels = Object.values(CATEGORY_DEF).flatMap((c) => c.labels);

export default function DetectionPanel({
  detections,
  hoveredIndex,
  setHoveredIndex,
}: DetectionPanelProps) {
  if (detections.length === 0) {
    return (
      <div className="text-xs text-muted-foreground italic p-6 text-center rounded-2xl border border-dashed border-border bg-bg-sunken/40">
        No objects detected by YOLO.
      </div>
    );
  }

  // Build label → count map
  const summary = detections.reduce((acc, det) => {
    acc[det.label] = (acc[det.label] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  // Categorise
  const categories = Object.entries(CATEGORY_DEF).map(([name, def]) => {
    let list: Detection[];
    if (name === "Other") {
      list = detections.filter((d) => !allKnownLabels.includes(d.label));
    } else {
      list = detections.filter((d) => def.labels.includes(d.label));
    }
    return { name, def, list };
  }).filter((c) => c.list.length > 0);

  return (
    <div className="space-y-5">
      {/* ── Summary chips row ─────────────────────────────── */}
      <div>
        <h3 className="text-xs font-black uppercase tracking-wider text-muted-foreground mb-3 flex items-center gap-1.5">
          <ShieldCheck className="w-3.5 h-3.5" /> Vision Summary · {detections.length} objects
        </h3>
        <div className="flex flex-wrap gap-2">
          {Object.entries(summary).map(([label, count]) => {
            const sample = detections.find((d) => d.label === label);
            const color = sample?.color || "#9ca3af";
            return (
              <span
                key={label}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold text-white shadow-sm"
                style={{ backgroundColor: color }}
              >
                <span className="capitalize">{label}</span>
                <span className="bg-white/25 rounded-full px-1.5 py-0.5 text-[10px] font-black leading-none">
                  ×{count}
                </span>
              </span>
            );
          })}
        </div>
      </div>

      {/* ── Categorised list ──────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2 gap-4">
        {categories.map(({ name, def, list }) => {
          const Icon = def.icon;
          return (
            <div key={name} className={`rounded-2xl border p-3.5 ${def.bg} ${def.border}`}>
              <div className={`flex items-center gap-1.5 text-[10px] font-black uppercase tracking-widest mb-2.5 ${def.color}`}>
                <Icon className="w-3.5 h-3.5" />
                <span>{name}</span>
                <span className="ml-auto opacity-60">{list.length}</span>
              </div>
              <div className="space-y-1.5">
                {list.map((det) => {
                  const globalIndex = detections.indexOf(det);
                  const isHovered = hoveredIndex === globalIndex;
                  return (
                    <div
                      key={globalIndex}
                      onMouseEnter={() => setHoveredIndex(globalIndex)}
                      onMouseLeave={() => setHoveredIndex(null)}
                      className={`flex items-center justify-between px-3 py-2 rounded-xl border cursor-pointer transition-all text-xs font-semibold ${
                        isHovered
                          ? "border-brand-500/50 bg-brand-500/10 scale-[1.01] shadow-sm"
                          : "border-transparent bg-bg-elevated/60 hover:bg-bg-elevated"
                      }`}
                    >
                      <span className="flex items-center gap-2 capitalize">
                        <span
                          className="w-2 h-2 rounded-full flex-shrink-0"
                          style={{ backgroundColor: det.color }}
                        />
                        {det.label}
                        {(det as any).relabeled_from && (
                          <span className="text-[9px] text-muted-foreground italic">
                            (was {(det as any).relabeled_from})
                          </span>
                        )}
                      </span>
                      <span className="text-[10px] text-muted-foreground font-bold tabular-nums">
                        {Math.round(det.confidence * 100)}%
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
