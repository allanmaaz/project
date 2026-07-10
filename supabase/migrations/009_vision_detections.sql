-- Migration 009: Vision Intelligence columns
-- Adds detections (YOLO bounding boxes), annotated image URL, and video frame count

ALTER TABLE uploads
    ADD COLUMN IF NOT EXISTS detections         JSONB    DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS video_detections   JSONB    DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS annotated_image_url TEXT    DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS video_frame_count   INTEGER DEFAULT 0;

-- Index for querying uploads that have detections
CREATE INDEX IF NOT EXISTS idx_uploads_has_detections
    ON uploads USING GIN (detections);

COMMENT ON COLUMN uploads.detections IS
    'YOLOv9 bounding box detections: [{label, confidence, bbox, color, frame}]';
COMMENT ON COLUMN uploads.video_detections IS
    'Full video frame analysis: {frames, aggregate_summary, person_trend, duration_sec}';
COMMENT ON COLUMN uploads.annotated_image_url IS
    'URL to the annotated image with bounding boxes drawn on it';
COMMENT ON COLUMN uploads.video_frame_count IS
    'Total frame count for video uploads';
