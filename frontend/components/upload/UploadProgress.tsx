"use client";

import React from "react";
import { UploadStep } from "../../hooks/useUpload";
import { Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { Progress } from "../../components/ui/progress"; // Make simple Radix progress bar placeholder or render inline

interface UploadProgressProps {
  progress: number;
  step: UploadStep;
  fileName: string | null;
  fileSize: number | null;
  error: string | null;
  onCancel: () => void;
  onRetry: () => void;
}

export default function UploadProgress({
  progress,
  step,
  fileName,
  fileSize,
  error,
  onCancel,
  onRetry,
}: UploadProgressProps) {
  const getStepLabel = (s: UploadStep) => {
    switch (s) {
      case "ocr":
        return "Extracting document text (OCR)...";
      case "classification":
        return "Classifying document type...";
      case "analysis":
        return "Analyzing content using Gemini AI...";
      case "done":
        return "Analysis completed!";
      case "failed":
        return "Failed to process document.";
    }
  };

  const formatSize = (bytes: number | null) => {
    if (!bytes) return "";
    const kb = bytes / 1024;
    if (kb < 1024) return `${kb.toFixed(1)} KB`;
    return `${(kb / 1024).toFixed(1)} MB`;
  };

  return (
    <div className="p-6 rounded-3xl border border-border bg-bg-elevated shadow-sm space-y-6">
      {/* File Metadata */}
      <div className="flex items-center justify-between border-b border-border pb-4">
        <div className="min-w-0">
          <p className="text-sm font-semibold truncate text-foreground">{fileName || "Uploading file..."}</p>
          <p className="text-xs text-muted-foreground mt-0.5">{formatSize(fileSize)}</p>
        </div>
        {step !== "done" && step !== "failed" && (
          <button
            onClick={onCancel}
            className="text-xs font-bold text-muted-foreground hover:text-danger-500 transition-all"
          >
            Cancel
          </button>
        )}
      </div>

      {error ? (
        <div className="space-y-4">
          <div className="p-4 rounded-2xl bg-danger-50 text-danger-500 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-bold">Processing Error</p>
              <p className="text-xs mt-1 leading-normal">{error}</p>
            </div>
          </div>
          <div className="flex gap-3">
            <button
              onClick={onRetry}
              className="flex-1 py-2.5 bg-black dark:bg-white text-white dark:text-black font-semibold text-sm rounded-xl hover:opacity-90 transition-all"
            >
              Try Again
            </button>
            <button
              onClick={onCancel}
              className="flex-1 py-2.5 border border-border bg-bg-base hover:bg-neutral-100 text-sm font-semibold rounded-xl transition-all"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Progress Slider */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs font-semibold text-muted-foreground">
              <span>{getStepLabel(step)}</span>
              <span>{progress}%</span>
            </div>
            {/* Simple progress bar */}
            <div className="w-full bg-bg-sunken h-2 rounded-full overflow-hidden">
              <div
                className="bg-brand-500 h-full transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          {/* Loader indicator status */}
          <div className="flex items-center gap-3 text-xs text-muted-foreground font-semibold">
            {step !== "done" ? (
              <Loader2 className="w-4 h-4 text-brand-500 animate-spin" />
            ) : (
              <CheckCircle2 className="w-4 h-4 text-success-500" />
            )}
            <span>This should take less than 15 seconds. Please keep this tab open.</span>
          </div>
        </div>
      )}
    </div>
  );
}
