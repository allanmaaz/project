CREATE TABLE analysis_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  upload_id UUID UNIQUE NOT NULL REFERENCES uploads(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  summary TEXT NOT NULL,
  sections JSONB NOT NULL DEFAULT '[]',
  detected_entities JSONB DEFAULT '{}',
  warnings JSONB DEFAULT '[]',
  recommendations JSONB DEFAULT '[]',
  timeline JSONB DEFAULT '[]',
  spending_data JSONB,
  medical_data JSONB,
  scam_data JSONB,
  risk_breakdown JSONB,
  model_used TEXT NOT NULL,
  token_usage JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE analysis_results ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users own analysis" ON analysis_results FOR ALL
  USING (user_id IN (SELECT id FROM users WHERE supabase_user_id = auth.uid()));

CREATE INDEX idx_analysis_upload_id ON analysis_results(upload_id);
