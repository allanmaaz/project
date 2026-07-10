"use client";

import React, { useState, useRef, useEffect } from "react";
import { Play, Pause, RotateCcw, Video, Users, Clock } from "lucide-react";
import DetectionViewer, { Detection } from "./DetectionViewer";

interface VideoFrame {
  frame_index: number;
  timestamp_sec: number;
  timestamp_label: string;
  detections: Detection[];
  summary: Record<string, number>;
  total_objects: number;
}

interface VideoFramePlayerProps {
  videoUrl: string;
  frames: VideoFrame[];
  durationSec: number;
  videoWidth: number;
  videoHeight: number;
}

export default function VideoFramePlayer({
  videoUrl,
  frames,
  durationSec,
  videoWidth,
  videoHeight,
}: VideoFramePlayerProps) {
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const playIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Sync state with HTML video element
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleTimeUpdate = () => {
      setCurrentTime(video.currentTime);
    };

    const handleEnded = () => {
      setIsPlaying(false);
    };

    video.addEventListener("timeupdate", handleTimeUpdate);
    video.addEventListener("ended", handleEnded);

    return () => {
      video.removeEventListener("timeupdate", handleTimeUpdate);
      video.removeEventListener("ended", handleEnded);
    };
  }, []);

  const handlePlayPause = () => {
    const video = videoRef.current;
    if (!video) return;

    if (isPlaying) {
      video.pause();
    } else {
      video.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleReset = () => {
    const video = videoRef.current;
    if (!video) return;
    video.currentTime = 0;
    setCurrentTime(0);
    if (isPlaying) {
      video.pause();
      setIsPlaying(false);
    }
  };

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value);
    const video = videoRef.current;
    if (video) {
      video.currentTime = time;
    }
    setCurrentTime(time);
  };

  // Find the closest frame to the current timestamp
  const getDetectionsForTime = (): Detection[] => {
    if (!frames || frames.length === 0) return [];
    
    // Find frame closest to currentTime
    let closestFrame = frames[0];
    let minDiff = Math.abs(frames[0].timestamp_sec - currentTime);
    
    for (const f of frames) {
      const diff = Math.abs(f.timestamp_sec - currentTime);
      if (diff < minDiff) {
        minDiff = diff;
        closestFrame = f;
      }
    }
    
    // If the closest frame is too far (e.g. >3s away), maybe return empty or closest
    // Since frame interval is 5s, we just return the closest frame
    return closestFrame.detections;
  };

  const activeDetections = getDetectionsForTime();

  // Get active counts summary
  const summary = activeDetections.reduce((acc, det) => {
    acc[det.label] = (acc[det.label] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const personCount = summary["person"] || 0;

  const secToLabel = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <div className="space-y-4">
      {/* Video Container with Canvas Overlay */}
      <div className="relative rounded-3xl overflow-hidden border border-border bg-bg-sunken flex items-center justify-center select-none shadow-xl aspect-video max-w-3xl mx-auto">
        <video
          ref={videoRef}
          src={videoUrl}
          className="w-full h-full object-contain"
          preload="auto"
        />

        {/* Dynamic Canvas Bounding Box Overlays */}
        <div className="absolute inset-0 pointer-events-none">
          <DetectionViewer
            imageUrl=""
            detections={activeDetections}
            hoveredIndex={hoveredIndex}
            setHoveredIndex={setHoveredIndex}
            videoDimensions={{ w: videoWidth, h: videoHeight }}
          />
        </div>
      </div>

      {/* Frame / Video Player Controls */}
      <div className="p-4 rounded-3xl border border-border bg-bg-elevated max-w-3xl mx-auto space-y-4 shadow-sm">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <button
              onClick={handlePlayPause}
              className="p-2.5 rounded-2xl bg-brand-500 hover:bg-brand-600 text-white font-bold transition-all shadow-md active:scale-95"
            >
              {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 fill-white" />}
            </button>
            <button
              onClick={handleReset}
              className="p-2.5 rounded-2xl border border-border bg-bg-sunken hover:bg-bg-base transition-all font-semibold"
            >
              <RotateCcw className="w-5 h-5" />
            </button>
          </div>

          {/* Time indicator */}
          <span className="text-xs font-black text-muted-foreground flex items-center gap-1.5 bg-bg-sunken px-3 py-1.5 rounded-2xl border border-border">
            <Clock className="w-3.5 h-3.5 text-brand-500" />
            {secToLabel(currentTime)} / {secToLabel(durationSec)}
          </span>
        </div>

        {/* Slider scrubber */}
        <input
          type="range"
          min={0}
          max={durationSec || 1}
          step={0.1}
          value={currentTime}
          onChange={handleSliderChange}
          className="w-full h-1.5 bg-bg-sunken hover:bg-bg-sunken/80 rounded-lg appearance-none cursor-pointer accent-brand-500"
        />

        {/* Real-time frame statistics bar */}
        <div className="flex items-center justify-between border-t border-border pt-3.5 text-xs">
          <span className="font-bold flex items-center gap-1.5">
            <Video className="w-4 h-4 text-brand-500" /> Active Frame Stats
          </span>

          <span className="font-bold text-muted-foreground flex items-center gap-4">
            <span className="flex items-center gap-1 text-danger-500">
              <Users className="w-4 h-4" /> Humans: {personCount}
            </span>
            <span>&bull;</span>
            <span>Total Objects: {activeDetections.length}</span>
          </span>
        </div>
      </div>
    </div>
  );
}
