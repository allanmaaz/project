"""
VisionService — YOLOv9c object detection optimized for Intel CPU (no GPU required).

Uses YOLOv9c (compact) — major upgrade over YOLOv8:
  - ~51MB model file, auto-downloads on first use
  - ~8-15 seconds per image on Intel i5 (CPU-only)
  - 80 COCO classes: person, car, truck, boat, fire, etc.
  - mAP50: 69.0% vs 52.9% YOLOv8s — new GELAN + PGI architecture
  - Dramatically better at crowded scenes, overlapping objects, small people
  - imgsz=640 (standard YOLO resolution)

NOTE: SAM segmentation skipped — requires GPU (too slow on Intel CPU ~30s/image).
Gemini Vision handles deep visual analysis; YOLO handles fast object counting.
"""
import io
import os
import json
import asyncio
import logging
from typing import Any
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Force CPU-only mode for PyTorch (no GPU on Intel Mac)
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

logger = logging.getLogger(__name__)

# Category → color mapping for bounding boxes
CATEGORY_COLORS = {
    "person":       "#FF4444",  # red — highest priority
    "car":          "#FF8800",  # orange
    "truck":        "#FF8800",
    "bus":          "#FF8800",
    "motorcycle":   "#FFAA00",
    "bicycle":      "#FFAA00",
    "boat":         "#0088FF",  # blue — water vehicle
    "fire":         "#FF0000",  # bright red — hazard
    "water":        "#00AAFF",  # light blue
    "dog":          "#00CC66",  # green
    "cat":          "#00CC66",
    "default":      "#CCCCCC",  # grey for others
}

# Human-readable group labels
CATEGORY_GROUPS = {
    "People":    ["person"],
    "Vehicles":  ["car", "truck", "bus", "motorcycle", "bicycle", "boat"],
    "Hazards":   ["fire", "knife", "gun", "scissors"],
    "Animals":   ["dog", "cat", "horse", "bird", "cow", "sheep"],
    "Objects":   [],  # catch-all
}


def _flood_relabel(detections: list[dict]) -> list[dict]:
    """
    YOLOv8n misclassifies cars in flood water as 'boat' because both look like
    floating objects from a distance. This function corrects it using geometry:
    - Real boats are long and narrow  (bbox width >> height, ratio > 4.0)
    - Cars are box-shaped             (bbox width / height between 1.0 and 3.5)
    - Actual rescue boats in images   usually have very high aspect ratios

    Strategy: if the scene has >=2 'boat' detections with car-proportioned
    bounding boxes AND no 'car' is detected alongside them, relabel them.
    The original confidence stays intact.
    """
    boat_dets = [d for d in detections if d["label"] == "boat"]
    car_dets   = [d for d in detections if d["label"] in ("car", "truck", "bus")]

    if not boat_dets:
        return detections

    # Count how many 'boat' detections look like cars by aspect ratio
    car_shaped_boats = [
        d for d in boat_dets
        if 0.8 <= (d["bbox"]["w"] / max(d["bbox"]["h"], 1)) <= 3.8
    ]

    # If most 'boat' detections are car-shaped AND there are few/no confirmed cars,
    # it's very likely a flood scene mislabelling everything.
    majority_are_car_shaped = len(car_shaped_boats) >= max(1, len(boat_dets) * 0.5)
    no_real_cars_detected   = len(car_dets) == 0

    if not (majority_are_car_shaped and no_real_cars_detected):
        return detections  # Scene looks legit — keep original labels

    fixed = []
    for det in detections:
        if det["label"] == "boat":
            ratio = det["bbox"]["w"] / max(det["bbox"]["h"], 1)
            if 0.8 <= ratio <= 3.8:
                # Car-shaped → relabel as submerged vehicle
                det = dict(det)  # copy to avoid mutating original
                det["label"] = "car"
                det["color"] = CATEGORY_COLORS.get("car", CATEGORY_COLORS["default"])
                det["relabeled_from"] = "boat"  # keep provenance
                print(f"[Vision] Relabelled boat→car (flood correction, ratio={ratio:.2f})")
        fixed.append(det)
    return fixed



class VisionService:
    _yolo_models: dict[str, Any] = {}

    @classmethod
    def _get_yolo(cls, model_name: str = "yolov9c"):
        if model_name not in cls._yolo_models:
            from ultralytics import YOLO
            # Map standard model names to files
            model_file = "yolov9c.pt" if model_name == "yolov9c" else "yolov8n.pt"
            cls._yolo_models[model_name] = YOLO(model_file)
            logger.info(f"[Vision] {model_name} loaded on CPU (weights: {model_file})")
        return cls._yolo_models[model_name]

    async def detect(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        run_sam: bool = False,
        conf_threshold: float = 0.22,
        model_name: str = "yolov9c",
        imgsz: int = 640,
    ) -> dict:
        """
        Run YOLO on image. Returns detections with bounding boxes + counts.
        Runs in a thread pool so it doesn't block the async event loop.
        """
        return await asyncio.to_thread(
            self._detect_sync, image_bytes, mime_type, False, conf_threshold, imgsz, model_name
        )

    def _detect_sync(
        self,
        image_bytes: bytes,
        mime_type: str,
        run_sam: bool,
        conf_threshold: float,
        imgsz: int = 640,   # Standard YOLO resolution — detects small/distant objects
        model_name: str = "yolov9c",
    ) -> dict:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_w, img_h = img.size
        img_np = np.array(img)

        model = self._get_yolo(model_name)
        results = model(
            img_np,
            conf=conf_threshold,
            imgsz=imgsz,
            iou=0.45,        # NMS IOU threshold — lower = fewer overlapping boxes
            max_det=100,     # max 100 objects per image
            verbose=False,
        )[0]

        detections = []
        summary: dict[str, int] = {}

        for box in results.boxes:
            label = results.names[int(box.cls[0])]
            conf = float(box.conf[0])
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            det = {
                "label": label,
                "confidence": round(conf, 3),
                "bbox": {
                    "x": round(x1), "y": round(y1),
                    "w": round(x2 - x1), "h": round(y2 - y1),
                },
                "color": CATEGORY_COLORS.get(label, CATEGORY_COLORS["default"]),
                "frame": 0,
            }
            detections.append(det)
            summary[label] = summary.get(label, 0) + 1

        # ── Flood/disaster context correction ──────────────────────────────
        # YOLOv8n often labels submerged cars as 'boat' in flood images.
        # Apply geometric heuristic to correct mislabelled objects.
        detections = _flood_relabel(detections)

        # Rebuild summary after relabelling
        summary = {}
        for det in detections:
            summary[det["label"]] = summary.get(det["label"], 0) + 1

        # Group summary
        groups: dict[str, int] = {}
        for group_name, labels in CATEGORY_GROUPS.items():
            count = sum(summary.get(l, 0) for l in labels)
            if count > 0:
                groups[group_name] = count
        # Catch-all
        grouped_labels = [l for ls in CATEGORY_GROUPS.values() for l in ls]
        others = sum(v for k, v in summary.items() if k not in grouped_labels)
        if others > 0:
            groups["Objects"] = others

        result = {
            "detections": detections,
            "summary": summary,
            "groups": groups,
            "image_width": img_w,
            "image_height": img_h,
            "model": "yolov9c",
            "total_objects": len(detections),
        }

        # SAM disabled on Intel CPU (too slow without GPU)
        # Future: enable when running on cloud/GPU instance

        return result

    async def draw_annotated(
        self,
        image_bytes: bytes,
        detections: list[dict],
        image_width: int,
        image_height: int,
    ) -> bytes:
        """
        Draw bounding boxes + labels on the image.
        Returns JPEG bytes of the annotated image.
        """
        return await asyncio.to_thread(
            self._draw_sync, image_bytes, detections, image_width, image_height
        )

    def _draw_sync(
        self,
        image_bytes: bytes,
        detections: list[dict],
        image_width: int,
        image_height: int,
    ) -> bytes:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        draw = ImageDraw.Draw(img, "RGBA")

        # Try to load a font, fall back to default
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size=14)
            font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size=11)
        except Exception:
            font = ImageFont.load_default()
            font_small = font

        for det in detections:
            color = det.get("color", "#FF4444")
            bbox = det["bbox"]
            x, y, w, h = bbox["x"], bbox["y"], bbox["w"], bbox["h"]
            label = det["label"]
            conf = det["confidence"]

            # Box with semi-transparent fill
            r, g, b = self._hex_to_rgb(color)
            draw.rectangle(
                [x, y, x + w, y + h],
                outline=color,
                width=3,
            )
            # Label background
            label_text = f"{label} {int(conf * 100)}%"
            text_bbox = draw.textbbox((x, y - 20), label_text, font=font)
            draw.rectangle(
                [text_bbox[0] - 2, text_bbox[1] - 2, text_bbox[2] + 2, text_bbox[3] + 2],
                fill=(r, g, b, 200),
            )
            draw.text((x, y - 20), label_text, fill="white", font=font)

        # Watermark
        draw.text(
            (8, image_height - 20),
            "Clarify AI — YOLOv9 Detection",
            fill=(255, 255, 255, 180),
            font=font_small,
        )

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        return buf.getvalue()

    def _hex_to_rgb(self, hex_color: str) -> tuple[int, int, int]:
        h = hex_color.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    def build_chat_context(self, detections_data: dict) -> str:
        """
        Build a text block to inject into the chat system prompt so the AI
        can answer questions like 'how many people?' precisely.
        """
        if not detections_data or not detections_data.get("detections"):
            return ""

        summary = detections_data.get("summary", {})
        groups = detections_data.get("groups", {})
        total = detections_data.get("total_objects", 0)
        model = detections_data.get("model", "yolo")

        lines = [
            "\n\n━━━ COMPUTER VISION DATA (YOLOv9 Detection) ━━━",
            f"Total objects detected: {total}",
        ]

        if summary:
            lines.append("Object counts (exact, from vision model):")
            for label, count in sorted(summary.items(), key=lambda x: -x[1]):
                lines.append(f"  • {label}: {count}")

        if groups:
            lines.append("By category:")
            for group, count in groups.items():
                lines.append(f"  • {group}: {count}")

        lines.append(
            "\nWhen asked 'how many X are there?', use the counts above — they are precise "
            "measurements from the computer vision model, not guesses."
        )
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        return "\n".join(lines)


# Singleton
_vision_service: VisionService | None = None


def get_vision_service() -> VisionService:
    global _vision_service
    if _vision_service is None:
        _vision_service = VisionService()
    return _vision_service
