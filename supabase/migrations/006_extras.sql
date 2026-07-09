CREATE TABLE shared_analyses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  upload_id UUID NOT NULL REFERENCES uploads(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  share_token TEXT UNIQUE NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  view_count INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE shared_analyses ENABLE ROW LEVEL SECURITY;

-- Shared link can be viewed publicly by anyone who has the share token
CREATE POLICY "Public read shared" ON shared_analyses FOR SELECT
  USING (NOW() < expires_at);

CREATE POLICY "Users own shared" ON shared_analyses FOR ALL
  USING (user_id IN (SELECT id FROM users WHERE supabase_user_id = auth.uid()));

CREATE INDEX idx_shared_token ON shared_analyses(share_token);
