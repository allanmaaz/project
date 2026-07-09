CREATE TABLE uploads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  original_filename TEXT,
  storage_path TEXT NOT NULL,
  file_type TEXT NOT NULL,
  file_size_bytes INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending','processing','completed','failed')),
  document_type TEXT,
  detected_language TEXT DEFAULT 'en',
  confidence_score FLOAT,
  risk_level TEXT CHECK (risk_level IN ('critical','high','medium','low','informational')),
  risk_score INTEGER DEFAULT 0,
  urgency TEXT CHECK (urgency IN ('immediate','within_24h','within_week','no_urgency')),
  extracted_text TEXT,
  auto_title TEXT,
  thumbnail_url TEXT,
  error_message TEXT,
  suggested_questions JSONB DEFAULT '[]',
  processing_started_at TIMESTAMPTZ,
  processing_completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE uploads ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users own uploads" ON uploads FOR ALL
  USING (user_id IN (SELECT id FROM users WHERE supabase_user_id = auth.uid()));

CREATE INDEX idx_uploads_user_id ON uploads(user_id);
CREATE INDEX idx_uploads_status ON uploads(status);
CREATE INDEX idx_uploads_document_type ON uploads(document_type);
CREATE INDEX idx_uploads_risk_level ON uploads(risk_level);
CREATE INDEX idx_uploads_created_at ON uploads(created_at DESC);
