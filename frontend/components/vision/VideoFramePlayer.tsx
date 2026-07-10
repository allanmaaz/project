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

  // Sync state with HTML video element at native monitor refresh rate (90fps/120fps)
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    let rafId: number;

    const syncTime = () => {
      setCurrentTime(video.currentTime);
      if (isPlaying) {
        rafId = requestAnimationFrame(syncTime);
      }
    };

    const handleEnded = () => {
      setIsPlaying(false);
    };

    // Fast time update for scrubbing/seeking when paused
    const handleTimeUpdate = () => {
      if (!isPlaying) {
        setCurrentTime(video.currentTime);
      }
    };

    video.addEventListener("ended", handleEnded);
    video.addEventListener("timeupdate", handleTimeUpdate);

    if (isPlaying) {
      rafId = requestAnimationFrame(syncTime);
    }

    return () => {
      video.removeEventListener("ended", handleEnded);
      video.removeEventListener("timeupdate", handleTimeUpdate);
      if (rafId) {
        cancelAnimationFrame(rafId);
      }
    };
  }, [isPlaying]);

  const handlePlayPause = () => {
    const video = videoRef.current;
    if (!video) return;

    if (isPlaying) {
      video.pause();
      setIsPlaying(false);
    } else {
      video.play();
      setIsPlaying(true);
    }
  };

  const handleReset = () => {
    const video = videoRef.current;
    if (!video) return;
    video.currentTime = 0;
    setCurrentTime(0);
    video.pause();
    setIsPlaying(false);
  };

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value);
    const video = videoRef.current;
    if (video) {
      video.currentTime = time;
    }
    setCurrentTime(time);
  };

  // Smoothly interpolate bounding boxes between frames (LERP)
  const getDetectionsForTime = (): Detection[] => {
    if (!frames || frames.length === 0) return [];
    if (frames.length === 1) return frames[0].detections;

    // Sort frames by timestamp to be absolutely safe
    const sorted = [...frames].sort((a, b) => a.timestamp_sec - b.timestamp_sec);

    // Find the bounding frames for the currentTime
    let prevFrame = sorted[0];
    let nextFrame = sorted[sorted.length - 1];

    for (let i = 0; i < sorted.length - 1; i++) {
      if (currentTime >= sorted[i].timestamp_sec && currentTime <= sorted[i + 1].timestamp_sec) {
        prevFrame = sorted[i];
        nextFrame = sorted[i + 1];
        break;
      }
    }

    // If we are outside bounds, return boundary detections
    if (currentTime <= sorted[0].timestamp_sec) return sorted[0].detections;
    if (currentTime >= sorted[sorted.length - 1].timestamp_sec) return sorted[sorted.length - 1].detections;

    const tDiff = nextFrame.timestamp_sec - prevFrame.timestamp_sec;
    if (tDiff <= 0.05) return prevFrame.detections; // Avoid division by zero

    const pct = (currentTime - prevFrame.timestamp_sec) / tDiff;

    const interpolated: Detection[] = [];

    // Track matched next detections so we can add unmatched ones
    const matchedNextIndices = new Set<number>();

    // Greedy IoU/distance matching of detections between prev and next frames
    for (const dPrev of prevFrame.detections) {
      let bestMatchIdx = -1;
      let minDistance = 99999;

      // Find closest same-label detection in next frame
      nextFrame.detections.forEach((dNext, idx) => {
        if (dNext.label !== dPrev.label || matchedNextIndices.has(idx)) return;

        // Calculate center-point Euclidean distance
        const prevCx = dPrev.bbox.x + dPrev.bbox.w / 2;
        const prevCy = dPrev.bbox.y + dPrev.bbox.h / 2;
        const nextCx = dNext.bbox.x + dNext.bbox.w / 2;
        const nextCy = dNext.bbox.y + dNext.bbox.h / 2;
        const dist = Math.sqrt(Math.pow(nextCx - prevCx, 2) + Math.pow(nextCy - prevCy, 2));

        // Bbox centers shouldn't be too far apart (max 150px) to prevent wrong matches
        if (dist < minDistance && dist < 150) {
          minDistance = dist;
          bestMatchIdx = idx;
        }
      });

      if (bestMatchIdx !== -1) {
        matchedNextIndices.add(bestMatchIdx);
        const dNext = nextFrame.detections[bestMatchIdx];

        // LERP coordinates
        interpolated.push({
          ...dPrev,
          confidence: dPrev.confidence + pct * (dNext.confidence - dPrev.confidence),
          bbox: {
            x: dPrev.bbox.x + pct * (dNext.bbox.x - dPrev.bbox.x),
            y: dPrev.bbox.y + pct * (dNext.bbox.y - dPrev.bbox.y),
            w: dPrev.bbox.w + pct * (dNext.bbox.w - dPrev.bbox.w),
            h: dPrev.bbox.h + pct * (dNext.bbox.h - dPrev.bbox.h),
          },
        });
      } else {
        // Unmatched object disappearing — fade size to 0 or only show in first half of interval
        if (pct < 0.5) {
          interpolated.push({
            ...dPrev,
            bbox: {
              ...dPrev.bbox,
              // Shrink slowly as it fades out
              w: dPrev.bbox.w * (1 - pct * 2),
              h: dPrev.bbox.h * (1 - pct * 2),
            },
          });
        }
      }
    }

    // Add unmatched appearing next detections
    nextFrame.detections.forEach((dNext, idx) => {
      if (matchedNextIndices.has(idx)) return;
      // Fade in from second half of interval
      if (pct >= 0.5) {
        const localPct = (pct - 0.5) * 2; // 0 to 1
        interpolated.push({
          ...dNext,
          bbox: {
            ...dNext.bbox,
            w: dNext.bbox.w * localPct,
            h: dNext.bbox.h * localPct,
          },
        });
      }
    });

    return interpolated;
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
