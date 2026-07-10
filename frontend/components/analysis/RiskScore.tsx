"use client";

import React, { useEffect, useState } from "react";
import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";

interface RiskScoreProps {
  score: number;
}

export default function RiskScore({ score }: RiskScoreProps) {
  const [percent, setPercent] = useState(0);

  useEffect(() => {
    // Animate local display number
    const timeout = setTimeout(() => setPercent(score), 300);
    return () => clearTimeout(timeout);
  }, [score]);

  // Radius details for SVG circle
  const r = 26;
  const circ = 2 * Math.PI * r; // ~163.36
  const strokeOffset = circ - (percent / 100) * circ;

  const getRiskColor = (s: number) => {
    if (s >= 80) return "stroke-danger-500 text-danger-500";
    if (s >= 50) return "stroke-warning-500 text-warning-500";
    if (s >= 25) return "stroke-brand-500 text-brand-500";
    return "stroke-success-500 text-success-500";
  };

  const getRiskLabel = (s: number) => {
    if (s >= 80) return "Critical Risk";
    if (s >= 50) return "Moderate Risk";
    if (s >= 25) return "Low Risk";
    return "Minimal Risk";
  };

  return (
    <div className="flex flex-col items-center text-center p-6 bg-bg-elevated border border-border rounded-3xl shadow-sm">
      <div className="relative w-32 h-32 flex items-center justify-center">
        {/* Progress SVG */}
        <svg className="w-full h-full -rotate-90" viewBox="0 0 60 60">
          {/* Base background circle */}
          <circle
            cx="30"
            cy="30"
            r={r}
            className="stroke-neutral-200 dark:stroke-neutral-800 fill-none"
            strokeWidth="4.5"
          />
          {/* Active progress circle */}
          <motion.circle
            cx="30"
            cy="30"
            r={r}
            className={`fill-none transition-all duration-1000 ease-out ${getRiskColor(score)}`}
            strokeWidth="4.5"
            strokeDasharray={circ}
            initial={{ strokeDashoffset: circ }}
            animate={{ strokeDashoffset: strokeOffset }}
            strokeLinecap="round"
          />
        </svg>

        {/* Center Text displaying percentage */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-extrabold tracking-tight">{percent}</span>
          <span className="text-[10px] uppercase font-bold tracking-widest text-muted-foreground mt-0.5">
            / 100
          </span>
        </div>
      </div>

      <div className="mt-4 space-y-1">
        <h4 className="text-sm font-bold text-foreground">{getRiskLabel(score)}</h4>
        <p className="text-xs text-muted-foreground font-semibold">
          AI computed risk index
        </p>
      </div>
    </div>
  );
}
