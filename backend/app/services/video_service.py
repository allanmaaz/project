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
# For smooth timeline playback: sample 1 frame every 10 frames (~3 frames per second at 30fps)
# To keep CPU time low, we use YOLOv8n (nano) at imgsz=320.
# ~0.15 seconds per frame = ~15-20 seconds total for a 30s video.
FRAME_SAMPLE_INTERVAL = 10    # 3 frames per second at 30fps
MAX_FRAMES_TO_ANALYZE = 150   # Up to 50 seconds of video timeline


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
            best_frame_bgr = None
            max_objects = -1

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

                    # Run YOLOv8n on CPU (fast, ~0.15s per frame at imgsz=320)
                    det_result = vision_service._detect_sync(
                        frame_bytes, "image/jpeg", False, 0.28, imgsz=320, model_name="yolov8n"
                    )

                    # Track frame with most objects for visual pipeline context
                    total_objs = det_result["total_objects"]
                    if total_objs > max_objects:
                        max_objects = total_objs
                        best_frame_bgr = frame_bgr.copy()

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

            # Convert best frame to JPEG bytes
            best_frame_bytes = None
            if best_frame_bgr is not None:
                try:
                    best_rgb = cv2.cvtColor(best_frame_bgr, cv2.COLOR_BGR2RGB)
                    pil_best = Image.fromarray(best_rgb)
                    buf_best = io.BytesIO()
                    pil_best.save(buf_best, format="JPEG", quality=80)
                    best_frame_bytes = buf_best.getvalue()
                except Exception as e:
                    logger.warning(f"[Video] Failed to serialize best frame: {e}")

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
                "best_frame_bytes": best_frame_bytes,    # representative frame for LLM visual pipeline
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
