-- Monthly upload counter reset using pg_cron (Supabase)
-- Run this in Supabase SQL Editor to enable automatic monthly reset

-- Enable pg_cron extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Schedule monthly reset on 1st of each month at 00:00 UTC
SELECT cron.schedule(
    'monthly-upload-reset',
    '0 0 1 * *',  -- At 00:00 on day 1 of every month
    $$
    UPDATE users SET uploads_this_month = 0;
    $$
);

-- To unschedule: SELECT cron.unschedule('monthly-upload-reset');
-- To view jobs: SELECT * FROM cron.job;