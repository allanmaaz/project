CREATE TABLE chat_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  upload_id UUID NOT NULL REFERENCES uploads(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user','assistant')),
  content TEXT NOT NULL,
  token_count INTEGER,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users own chat" ON chat_messages FOR ALL
  USING (user_id IN (SELECT id FROM users WHERE supabase_user_id = auth.uid()));

CREATE INDEX idx_chat_upload_id ON chat_messages(upload_id);
CREATE INDEX idx_chat_created_at ON chat_messages(created_at ASC);
