-- Migration: Add disaster_data column for Flood & Rescue Dispatch Pipeline
ALTER TABLE analysis_results ADD COLUMN IF NOT EXISTS disaster_data JSONB;
