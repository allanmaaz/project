"use client";

import React from "react";
import { useUpload } from "../../../hooks/useUpload";
import UploadZone from "../../../components/upload/UploadZone";
import UploadProgress from "../../../components/upload/UploadProgress";

export default function UploadPage() {
  const {
    state,
    progress,
    step,
    error,
    fileName,
    fileSize,
    uploadFile,
    cancelUpload,
    reset,
  } = useUpload();

  return (
    <div className="max-w-xl mx-auto space-y-6 pt-6">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-extrabold tracking-tight">Upload Document</h1>
        <p className="text-sm text-muted-foreground max-w-md mx-auto leading-relaxed">
          Upload any medical prescription, legal contract, bank statement, or utility bill to instantly understand it.
        </p>
      </div>

      {state === "idle" && (
        <UploadZone onFileSelect={uploadFile} disabled={false} />
      )}

      {(state === "uploading" || state === "processing" || state === "error") && (
        <UploadProgress
          progress={progress}
          step={step}
          fileName={fileName}
          fileSize={fileSize}
          error={error}
          onCancel={cancelUpload}
          onRetry={reset}
        />
      )}
    </div>
  );
}
