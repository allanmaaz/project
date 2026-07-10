"use client";

import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Eye, Info } from "lucide-react";

export interface Detection {
  label: string;
  confidence: number;
  bbox: { x: number; y: number; w: number; h: number };
  color: string;
  frame: number;
}

interface DetectionViewerProps {
  imageUrl: string;
  detections: Detection[];
  hoveredIndex: number | null;
  setHoveredIndex: (index: number | null) => void;
  videoDimensions?: { w: number; h: number };
}

export default function DetectionViewer({
  imageUrl,
  detections,
  hoveredIndex,
  setHoveredIndex,
  videoDimensions,
}: DetectionViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState({ x: 1, y: 1 });
  const [naturalSize, setNaturalSize] = useState(videoDimensions || { w: 1, h: 1 });
  const [isImageLoaded, setIsImageLoaded] = useState(!imageUrl);

  const handleImageLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const img = e.currentTarget;
    setNaturalSize({ w: img.naturalWidth || 1, h: img.naturalHeight || 1 });
    setIsImageLoaded(true);
  };

  // Re-calculate box scale when container size or natural size changes
  useEffect(() => {
    if (!containerRef.current || !isImageLoaded) return;

    const updateScale = () => {
      const rect = containerRef.current!.getBoundingClientRect();
      // Bbox coords are absolute pixels relative to natural size
      setScale({
        x: rect.width / naturalSize.w,
        y: rect.height / naturalSize.h,
      });
    };

    updateScale();
    window.addEventListener("resize", updateScale);
    return () => window.removeEventListener("resize", updateScale);
  }, [naturalSize, isImageLoaded, detections]);

  return (
    <div className="space-y-3">
      {/* Toolbar row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Eye className="w-4 h-4 text-brand-500" />
          <span className="text-sm font-black text-foreground">Interactive Detection Map</span>
          {detections.length > 0 && (
            <span className="px-2 py-0.5 rounded-full bg-brand-500/15 text-brand-400 text-[10px] font-black">
              {detections.length} objects
            </span>
          )}
        </div>
        <span className="text-[10px] text-muted-foreground flex items-center gap-1 font-semibold hidden sm:flex">
          <Info className="w-3 h-3" /> Hover to inspect
        </span>
      </div>

      <div
        ref={containerRef}
        className="relative rounded-3xl overflow-hidden border border-border bg-bg-sunken flex items-center justify-center select-none shadow-inner"
        style={{ aspectRatio: naturalSize.w / naturalSize.h }}
      >
        {imageUrl && (
          /* eslint-disable-next-line @next/next/no-img-element */
          <img
            src={imageUrl}
            alt="Visual Analysis"
            className="w-full h-full object-contain pointer-events-none"
            onLoad={handleImageLoad}
          />
        )}

        {isImageLoaded &&
          detections.map((det, index) => {
            const { x, y, w, h } = det.bbox;
            const left = x * scale.x;
            const top = y * scale.y;
            const width = w * scale.x;
            const height = h * scale.y;

            const isHovered = hoveredIndex === index;

            return (
              <React.Fragment key={index}>
                {/* Bounding box wrapper */}
                <motion.div
                  className="absolute cursor-pointer rounded"
                  style={{
                    left,
                    top,
                    width,
                    height,
                    border: `2px solid ${det.color}`,
                    backgroundColor: isHovered
                      ? `${det.color}25` // 15% opacity fill on hover
                      : `${det.color}05`, // 2% opacity fill default
                    boxShadow: isHovered
                      ? `0 0 12px ${det.color}80, inset 0 0 8px ${det.color}80`
                      : "none",
                    zIndex: isHovered ? 40 : 10,
                  }}
                  onMouseEnter={() => setHoveredIndex(index)}
                  onMouseLeave={() => setHoveredIndex(null)}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.3 }}
                >
                  {/* Small tag */}
                  <span
                    className="absolute text-[9px] font-bold text-white px-1.5 py-0.5 rounded shadow-md pointer-events-none"
                    style={{
                      backgroundColor: det.color,
                      top: height > 24 ? 2 : -18,
                      left: 2,
                    }}
                  >
                    {det.label}
                  </span>
                </motion.div>

                {/* Floating details popup */}
                <AnimatePresence>
                  {isHovered && (
                    <motion.div
                      initial={{ opacity: 0, y: 4, scale: 0.95 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: 4, scale: 0.95 }}
                      className="absolute z-50 p-3 rounded-2xl border border-border bg-bg-elevated/95 backdrop-blur-md shadow-xl text-xs space-y-1 w-44 pointer-events-none font-semibold text-foreground"
                      style={{
                        left: Math.min(
                          Math.max(8, left + width / 2 - 88),
                          (containerRef.current?.getBoundingClientRect().width || 0) - 184
                        ),
                        top: top - 68 > 8 ? top - 68 : top + height + 8,
                      }}
                    >
                      <div className="flex items-center justify-between">
                        <span className="capitalize text-brand-500 font-bold">{det.label}</span>
                        <span
                          className="px-1.5 py-0.5 rounded text-[10px] font-black text-white"
                          style={{ backgroundColor: det.color }}
                        >
                          {Math.round(det.confidence * 100)}%
                        </span>
                      </div>
                      <div className="text-[10px] text-muted-foreground">
                        Location: X={Math.round(x)}, Y={Math.round(y)}
                      </div>
                      <div className="text-[10px] text-muted-foreground">
                        Dimensions: {Math.round(w)}x{Math.round(h)} px
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </React.Fragment>
            );
          })}
      </div>
    </div>
  );
}
