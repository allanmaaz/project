"use client";

import React from "react";
import { Detection } from "./DetectionViewer";
import { Users, Truck, AlertTriangle, ShieldCheck, Cpu } from "lucide-react";

interface DetectionPanelProps {
  detections: Detection[];
  hoveredIndex: number | null;
  setHoveredIndex: (index: number | null) => void;
}

export default function DetectionPanel({
  detections,
  hoveredIndex,
  setHoveredIndex,
}: DetectionPanelProps) {
  // Count counts of labels
  const summary = detections.reduce((acc, det) => {
    acc[det.label] = (acc[det.label] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  // Categorize for grouped view
  const categories = {
    People: detections.filter((d) => d.label === "person"),
    Vehicles: detections.filter((d) =>
      ["car", "truck", "bus", "motorcycle", "bicycle", "boat"].includes(d.label)
    ),
    Hazards: detections.filter((d) =>
      ["fire", "knife", "gun", "scissors", "stop sign"].includes(d.label)
    ),
    Other: detections.filter(
      (d) =>
        !["person", "car", "truck", "bus", "motorcycle", "bicycle", "boat", "fire", "knife", "gun", "scissors", "stop sign"].includes(
          d.label
        )
    ),
  };

  const getIcon = (catName: string) => {
    switch (catName) {
      case "People":
        return <Users className="w-4 h-4 text-brand-500" />;
      case "Vehicles":
        return <Truck className="w-4 h-4 text-warning-500" />;
      case "Hazards":
        return <AlertTriangle className="w-4 h-4 text-danger-500" />;
      default:
        return <Cpu className="w-4 h-4 text-muted-foreground" />;
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-black uppercase tracking-wider text-muted-foreground mb-3 flex items-center gap-1.5">
          <ShieldCheck className="w-4 h-4" /> Vision Summary
        </h3>
        {detections.length === 0 ? (
          <div className="text-xs text-muted-foreground italic p-4 text-center rounded-2xl border border-dashed border-border bg-bg-sunken/40">
            No objects detected by YOLOv8n CPU model.
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(summary).map(([label, count]) => {
              const sampleDet = detections.find((d) => d.label === label);
              const color = sampleDet?.color || "#CCCCCC";
              return (
                <div
                  key={label}
                  className="flex items-center justify-between p-3 rounded-2xl border border-border bg-bg-elevated hover:bg-bg-sunken/40 transition-colors font-bold text-xs"
                >
                  <span className="capitalize flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
                    {label}
                  </span>
                  <span className="bg-bg-sunken px-2 py-0.5 rounded text-[10px] text-foreground font-black">
                    x{count}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {detections.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-xs font-black uppercase tracking-wider text-muted-foreground">
            Detected Objects List ({detections.length})
          </h3>
          <div className="max-h-[300px] overflow-y-auto space-y-4 pr-1 scrollbar-thin">
            {Object.entries(categories).map(([catName, list]) => {
              if (list.length === 0) return null;
              return (
                <div key={catName} className="space-y-2">
                  <div className="flex items-center gap-1.5 text-[10px] font-black uppercase tracking-widest text-muted-foreground">
                    {getIcon(catName)}
                    <span>{catName}</span>
                  </div>
                  <div className="space-y-1">
                    {list.map((det) => {
                      const globalIndex = detections.indexOf(det);
                      const isHovered = hoveredIndex === globalIndex;
                      return (
                        <div
                          key={globalIndex}
                          onMouseEnter={() => setHoveredIndex(globalIndex)}
                          onMouseLeave={() => setHoveredIndex(null)}
                          className={`flex items-center justify-between p-2.5 rounded-xl border transition-all cursor-pointer text-xs font-bold ${
                            isHovered
                              ? "border-brand-500 bg-brand-50/10 dark:bg-brand-900/10 scale-[1.01]"
                              : "border-border/50 hover:border-brand-350 bg-bg-sunken/20 hover:bg-bg-elevated"
                          }`}
                        >
                          <span className="capitalize flex items-center gap-2">
                            <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: det.color }} />
                            {det.label}
                          </span>
                          <span className="text-[10px] font-semibold text-muted-foreground">
                            Conf: {Math.round(det.confidence * 100)}%
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
      )}
    </div>
  );
}
