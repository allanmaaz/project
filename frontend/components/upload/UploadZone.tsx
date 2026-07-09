"use client";

import React, { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { UploadCloud, Shield, HelpCircle, FileText } from "lucide-react";
import { motion } from "framer-motion";

interface UploadZoneProps {
  onFileSelect: (file: File) => void;
  disabled: boolean;
}

export default function UploadZone({ onFileSelect, disabled }: UploadZoneProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0 && !disabled) {
        onFileSelect(acceptedFiles[0]);
      }
    },
    [onFileSelect, disabled]
  );

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    disabled,
    accept: {
      "image/jpeg": [".jpg", ".jpeg"],
      "image/png": [".png"],
      "image/webp": [".webp"],
      "application/pdf": [".pdf"],
    },
    maxSize: 20 * 1024 * 1024, // 20MB
    multiple: false,
  });

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-3xl p-12 text-center cursor-pointer transition-all ${
          isDragActive
            ? "border-brand-500 bg-brand-50/50 dark:bg-brand-900/10 scale-[1.01]"
            : "border-border hover:border-brand-350 bg-bg-elevated hover:bg-bg-base"
        } ${isDragReject ? "border-danger-500 bg-danger-50/10" : ""}`}
      >
        <input {...getInputProps()} />
        <div className="max-w-md mx-auto space-y-4">
          {/* Animated upload icon */}
          <motion.div
            animate={isDragActive ? { y: -8, scale: 1.1 } : { y: [0, -4, 0] }}
            transition={isDragActive ? { type: "spring" } : { repeat: Infinity, duration: 2.5, ease: "easeInOut" }}
            className="w-16 h-16 rounded-2xl bg-brand-500/10 text-brand-500 flex items-center justify-center mx-auto"
          >
            <UploadCloud className="w-8 h-8" />
          </motion.div>

          <div className="space-y-1.5">
            <p className="text-base font-bold text-foreground">
              {isDragActive ? "Drop your file here..." : "Drag & drop your document here"}
            </p>
            <p className="text-xs text-muted-foreground font-semibold">
              or <span className="text-brand-500 hover:underline">browse files</span> on your computer
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-4 text-[10px] text-muted-foreground font-semibold">
            <span className="flex items-center gap-1">
              <FileText className="w-3.5 h-3.5" /> PDF, PNG, JPG, WEBP
            </span>
            <span>&bull;</span>
            <span>Max size 20MB</span>
          </div>
        </div>
      </div>

      {/* Safety notes banner */}
      <div className="flex items-center justify-between p-4 rounded-2xl border border-border bg-bg-sunken/30 text-xs text-muted-foreground font-semibold">
        <span className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-success-500" />
          End-to-end encrypted storage &bull; Private and secure.
        </span>
        <span className="flex items-center gap-1 hover:text-foreground cursor-help">
          <HelpCircle className="w-4 h-4" /> Need help?
        </span>
      </div>
    </div>
  );
}
