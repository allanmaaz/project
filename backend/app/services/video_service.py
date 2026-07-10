"""
VideoService — OpenCV frame extraction + per-frame YOLOv9 detection.

Flow:
  1. Decode video bytes with OpenCV
  2. Sample 1 frame per second (configurable)
  3. Run YOLOv9 on each sampled frame
  4. Return frame timeline + aggregate stats
  5. Generate a 3x3 thumbnail grid of key frames
"""
import io
import cv2
import asyncio
import logging
import numpy as np
from PIL import Image
from typing import Any

logger = logging.getLogger(__name__)

# Intel i5 optimization:
# At 30fps video: skip 150 frames = analyze 1 frame every 5 seconds
# This keeps total YOLO time under ~40s for a 60s video on CPU
FRAME_SAMPLE_INTERVAL = 150   # 1 frame per 5 seconds at 30fps
MAX_FRAMES_TO_ANALYZE = 20    # cap: 20 frames × ~2s/frame = ~40s max


class VideoService:

    async def process_video(
        self,
        video_bytes: bytes,
        vision_service,  # injected VisionService
    ) -> dict:
        """
        Extract frames from video, run YOLO on each, return timeline.
        """
        return await asyncio.to_thread(
            self._process_sync, video_bytes, vision_service
        )

    def _process_sync(self, video_bytes: bytes, vision_service) -> dict:
        # Write to a temp buffer OpenCV can read
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(video_bytes)
            tmp_path = f.name

        try:
            cap = cv2.VideoCapture(tmp_path)
            if not cap.isOpened():
                return {"error": "Could not open video file", "frames": []}

            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration_sec = total_frames / fps
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            frame_results = []
            frame_idx = 0
            sampled = 0
            aggregate_summary: dict[str, int] = {}

            # Key frames for thumbnail grid
            key_frames_bgr = []

            while cap.isOpened() and sampled < MAX_FRAMES_TO_ANALYZE:
                ret, frame_bgr = cap.read()
                if not ret:
                    break

                if frame_idx % FRAME_SAMPLE_INTERVAL == 0:
                    timestamp_sec = frame_idx / fps

                    # Convert BGR → RGB → bytes for VisionService
                    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(frame_rgb)
                    buf = io.BytesIO()
                    pil_img.save(buf, format="JPEG", quality=70)
                    frame_bytes = buf.getvalue()

                    # Run YOLO (sync, already in thread)
                    det_result = vision_service._detect_sync(frame_bytes, "image/jpeg", False, 0.35)

                    frame_data = {
                        "frame_index": frame_idx,
                        "timestamp_sec": round(timestamp_sec, 1),
                        "timestamp_label": self._sec_to_label(timestamp_sec),
                        "detections": det_result["detections"],
                        "summary": det_result["summary"],
                        "total_objects": det_result["total_objects"],
                    }
                    frame_results.append(frame_data)

                    # Aggregate
                    for label, count in det_result["summary"].items():
                        aggregate_summary[label] = max(
                            aggregate_summary.get(label, 0), count
                        )

                    # Save key frames (every 10th sampled frame)
                    if sampled % 10 == 0 and len(key_frames_bgr) < 9:
                        key_frames_bgr.append(frame_bgr.copy())

                    sampled += 1

                frame_idx += 1

            cap.release()

            # Build trend data — person count over time
            person_trend = [
                {"t": f["timestamp_sec"], "count": f["summary"].get("person", 0)}
                for f in frame_results
            ]

            # Generate thumbnail grid bytes
            thumbnail_grid_bytes = self._make_thumbnail_grid(key_frames_bgr)

            return {
                "frame_count": total_frames,
                "sampled_frames": sampled,
                "fps": round(fps, 1),
                "duration_sec": round(duration_sec, 1),
                "video_width": width,
                "video_height": height,
                "frames": frame_results,
                "aggregate_summary": aggregate_summary,
                "person_trend": person_trend,
                "thumbnail_grid": thumbnail_grid_bytes,  # bytes for upload
            }
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    def _sec_to_label(self, secs: float) -> str:
        m = int(secs // 60)
        s = int(secs % 60)
        return f"{m}:{s:02d}"

    def _make_thumbnail_grid(self, frames_bgr: list) -> bytes | None:
        """Create a 3-column grid of key frame thumbnails."""
        if not frames_bgr:
            return None
        try:
            thumb_size = (213, 120)  # 3 cols × 213 = 640px wide
            thumbs = []
            for f in frames_bgr[:9]:
                resized = cv2.resize(f, thumb_size)
                rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
                thumbs.append(rgb)

            # Pad to 9 with black
            while len(thumbs) < 9:
                thumbs.append(np.zeros((120, 213, 3), dtype=np.uint8))

            rows = [
                np.hstack(thumbs[0:3]),
                np.hstack(thumbs[3:6]),
                np.hstack(thumbs[6:9]),
            ]
            grid = np.vstack(rows)
            pil = Image.fromarray(grid)
            buf = io.BytesIO()
            pil.save(buf, format="JPEG", quality=75)
            return buf.getvalue()
        except Exception as e:
            logger.warning(f"[Video] Thumbnail grid failed: {e}")
            return None

    def build_chat_context(self, video_data: dict) -> str:
        """Inject video analysis into chat context."""
        if not video_data or "frames" not in video_data:
            return ""

        agg = video_data.get("aggregate_summary", {})
        trend = video_data.get("person_trend", [])
        duration = video_data.get("duration_sec", 0)
        sampled = video_data.get("sampled_frames", 0)

        lines = [
            "\n\n━━━ VIDEO ANALYSIS DATA (YOLOv9 Frame Detection) ━━━",
            f"Duration: {duration}s | Frames analyzed: {sampled}",
            "Peak object counts across all frames:",
        ]
        for label, count in sorted(agg.items(), key=lambda x: -x[1]):
            lines.append(f"  • {label}: up to {count} at once")

        if trend:
            peak = max(trend, key=lambda x: x["count"])
            if peak["count"] > 0:
                lines.append(
                    f"Person count peaked at {peak['count']} people at {peak['t']}s"
                )

        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(lines)


_video_service: VideoService | None = None


def get_video_service() -> VideoService:
    global _video_service
    if _video_service is None:
        _video_service = VideoService()
    return _video_service
