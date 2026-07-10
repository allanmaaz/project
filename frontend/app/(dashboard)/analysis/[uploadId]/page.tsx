"use client";

import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { api } from "../../../../lib/api";
import { Loader2, AlertCircle, Eye, FileText, BarChart3 } from "lucide-react";
import AnalysisHeader from "../../../../components/analysis/AnalysisHeader";
import RiskScore from "../../../../components/analysis/RiskScore";
import SummaryCard from "../../../../components/analysis/SummaryCard";
import AnalysisSectionComponent from "../../../../components/analysis/AnalysisSection";
import ChatPanel from "../../../../components/chat/ChatPanel";
import ChatBottomSheet from "../../../../components/chat/ChatBottomSheet";
import DisasterAnalysis from "../../../../components/analysis/DisasterAnalysis";
import DetectionViewer from "../../../../components/vision/DetectionViewer";
import DetectionPanel from "../../../../components/vision/DetectionPanel";
import VideoFramePlayer from "../../../../components/vision/VideoFramePlayer";
import { toast } from "sonner";

export default function AnalysisPage() {
  const params = useParams();
  const uploadId = params.uploadId as string;

  const [data, setData] = useState<any>(null);
  const [visionData, setVisionData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Navigation tabs: "report" (AI Summary) or "vision" (YOLO Detections Map)
  const [activeTab, setActiveTab] = useState<"report" | "vision">("report");
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  useEffect(() => {
    const fetchAnalysis = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const res = await api.analysis.get(uploadId);
        setData(res);
        
        // Fetch detections separately
        try {
          const visRes = await api.analysis.getDetections(uploadId);
          setVisionData(visRes);
          // If the file is classified as disaster/traffic, default to vision tab
          if (visRes.has_detections || visRes.has_video) {
            setActiveTab("vision");
          }
        } catch (visErr) {
          console.warn("Detections not available for this upload:", visErr);
        }
      } catch (err: any) {
        setError(err.message || "Failed to load document analysis.");
        toast.error("Could not load analysis details.");
      } finally {
        setIsLoading(false);
      }
    };
    if (uploadId) fetchAnalysis();
  }, [uploadId]);

  if (isLoading) {
    return (
      <div className="h-[70dvh] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-brand-500 animate-spin" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-md mx-auto py-12 text-center space-y-4">
        <div className="p-4 rounded-2xl bg-danger-50 text-danger-500 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div className="text-left">
            <p className="font-bold text-sm">Failed to Load Analysis</p>
            <p className="text-xs mt-1 leading-normal">
              {error || "An unexpected error occurred while fetching analysis records."}
            </p>
          </div>
        </div>
        <button
          onClick={() => window.location.reload()}
          className="px-5 py-2.5 bg-black dark:bg-white text-white dark:text-black font-semibold text-sm rounded-xl hover:opacity-90 transition-all active:scale-95 shadow-sm"
        >
          Retry Load
        </button>
      </div>
    );
  }

  const showVisionTab = visionData && (visionData.has_detections || visionData.has_video);
  const rawFileUrl = `${api.getBaseUrl()}/uploads/${uploadId}/raw`; // direct link to storage

  return (
    <div className="space-y-6">
      {/* Upper header */}
      <AnalysisHeader
        uploadId={uploadId}
        title={data.auto_title}
        docType={data.document_type}
        language={data.detected_language}
        riskLevel={data.risk_level}
        riskScore={data.risk_score}
        date={data.created_at}
        thumbnailUrl={null}
      />

      {/* Tab Selectors */}
      {showVisionTab && (
        <div className="flex items-center gap-1.5 p-1 rounded-2xl bg-bg-sunken border border-border w-fit">
          <button
            onClick={() => setActiveTab("vision")}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-xs transition-all active:scale-[0.98] ${
              activeTab === "vision"
                ? "bg-bg-elevated text-brand-500 shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Eye className="w-4 h-4" /> Visual Intelligence
          </button>
          <button
            onClick={() => setActiveTab("report")}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-xs transition-all active:scale-[0.98] ${
              activeTab === "report"
                ? "bg-bg-elevated text-brand-500 shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <FileText className="w-4 h-4" /> AI Situation Report
          </button>
        </div>
      )}

      {/* Main Grid splits */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Side (lg: 8 cols) */}
        <div className="lg:col-span-8 space-y-6">
          {activeTab === "vision" && visionData ? (
            <div className="space-y-6">
              {/* Video Timeline Scrubber */}
              {visionData.has_video && visionData.video_detections ? (
                <VideoFramePlayer
                  videoUrl={rawFileUrl}
                  frames={visionData.video_detections.frames || []}
                  durationSec={visionData.video_detections.duration_sec || 0}
                  videoWidth={visionData.video_detections.video_width || 640}
                  videoHeight={visionData.video_detections.video_height || 360}
                />
              ) : (
                /* Static Image Bounding Box Canvas */
                <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
                  <div className="md:col-span-8">
                    <DetectionViewer
                      imageUrl={rawFileUrl}
                      detections={visionData.detections || []}
                      hoveredIndex={hoveredIndex}
                      setHoveredIndex={setHoveredIndex}
                    />
                  </div>
                  <div className="md:col-span-4 bg-bg-sunken/25 p-4 rounded-3xl border border-border">
                    <DetectionPanel
                      detections={visionData.detections || []}
                      hoveredIndex={hoveredIndex}
                      setHoveredIndex={setHoveredIndex}
                    />
                  </div>
                </div>
              )}
            </div>
          ) : (
            /* Traditional Document AI Report Tab */
            <div className="space-y-6">
              <SummaryCard summary={data.summary} />

              {data.document_type === "disaster_rescue" && data.disaster_data && (
                <DisasterAnalysis data={data.disaster_data} />
              )}

              {/* Collapsible details list */}
              <div className="space-y-4">
                <h2 className="text-lg font-bold flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-brand-500" /> Analysis Breakdown
                </h2>
                {data.sections && data.sections.length > 0 ? (
                  data.sections.map((section: any) => (
                    <AnalysisSectionComponent key={section.id} section={section} />
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground">No sections reported.</p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Right Side: Risk circular meter + chat (lg: 4 cols) */}
        <div className="lg:col-span-4 space-y-6">
          {/* Circular Risk Index */}
          <RiskScore score={data.risk_score} />

          {/* Desktop Q&A Chat Panel */}
          <div className="hidden lg:block h-[450px]">
            <ChatPanel uploadId={uploadId} />
          </div>
        </div>
      </div>

      {/* Mobile Drawer (FAB) Chat */}
      <ChatBottomSheet uploadId={uploadId} />
    </div>
  );
}
