import { useState, useRef, useEffect, useCallback } from "react";
import { api } from "../lib/api";
import { useRouter } from "next/navigation";

export type UploadState = "idle" | "selected" | "uploading" | "processing" | "completed" | "error";
export type UploadStep = "ocr" | "classification" | "analysis" | "done" | "failed";

export const useUpload = () => {
  const [state, setState] = useState<UploadState>("idle");
  const [progress, setProgress] = useState(0);
  const [step, setStep] = useState<UploadStep>("ocr");
  const [error, setError] = useState<string | null>(null);
  const [uploadId, setUploadId] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [fileSize, setFileSize] = useState<number | null>(null);

  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const retryCountRef = useRef(0);
  const router = useRouter();

  const cleanup = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  }, []);

  useEffect(() => {
    return cleanup;
  }, [cleanup]);

  const uploadFile = async (file: File, retryCount = 0) => {
    cleanup();
    setError(null);
    setFileName(file.name);
    setFileSize(file.size);
    setState("uploading");
    setProgress(10);

    const maxRetries = 3;
    const baseDelay = 1000;

    const attemptUpload = async () => {
      try {
        // Step 1: Upload to Supabase Storage & insert record
        const res = await api.uploads.create(file);
        const id = res.upload_id;
        setUploadId(id);
        
        setState("processing");
        setProgress(30);
        setStep("ocr");

        // Step 2: Poll status from FastAPI
        pollIntervalRef.current = setInterval(async () => {
          try {
            const statusRes = await api.uploads.getStatus(id);
            
            if (statusRes.status === "processing") {
              setStep(statusRes.step);
              setProgress(statusRes.progress_percent);
            } else if (statusRes.status === "completed") {
              cleanup();
              setProgress(100);
              setStep("done");
              setState("completed");
              router.push(`/analysis/${id}`);
            } else if (statusRes.status === "failed") {
              cleanup();
              setError(statusRes.error || "Document analysis failed.");
              setState("error");
            }
          } catch (err: any) {
            cleanup();
            setError(err.message || "Error polling document status.");
            setState("error");
          }
        }, 1500);

      } catch (err: any) {
        // Retry on server errors (5xx) or network errors
        const isRetryable = err.status >= 500 || err.name === "TypeError";
        if (isRetryable && retryCount < maxRetries) {
          const delay = baseDelay * Math.pow(2, retryCount);
          await new Promise(resolve => setTimeout(resolve, delay));
          await attemptUpload(); // Recursive retry
        } else {
          cleanup();
          setError(err.message || "Failed to upload document.");
          setState("error");
        }
      }
    };

    await attemptUpload();
  };

  const cancelUpload = async () => {
    cleanup();
    if (uploadId) {
      try {
        await api.uploads.delete(uploadId);
      } catch (err) {
        console.error("Failed to delete cancelled upload:", err);
      }
    }
    reset();
  };

  const reset = () => {
    cleanup();
    setState("idle");
    setProgress(0);
    setStep("ocr");
    setError(null);
    setUploadId(null);
    setFileName(null);
    setFileSize(null);
    retryCountRef.current = 0;
  };

  return {
    state,
    progress,
    step,
    error,
    fileName,
    fileSize,
    uploadFile,
    cancelUpload,
    reset,
  };
};
