-- ==============================================================================
-- Multi-Agent-TourAI: Phase 2C Database Migration
-- Migration: 002_create_application_auth.sql
-- Description: Establishes application-owned authentication tables (app_users,
--              auth_identities, auth_sessions, auth_verification_tokens),
--              safely migrates existing Supabase users from auth.users, and updates
--              user_threads foreign key referencing app_users(id).
--
-- SECURITY & LEAST-PRIVILEGE GUARANTEES:
--   - Non-destructive: Does NOT drop public.user_threads or LangGraph checkpoints.
--   - Preserves all existing checkpoint_writes, checkpoint_blobs, and store records.
--   - Safe data migration: Excludes NULL/empty emails, normalizes to lowercase.
--   - Supabase bcrypt password hashes are deliberately NOT migrated to Argon2id.
--   - Single-use, time-limited verification tokens table for secure onboarding.
--   - Replaces foreign key on user_threads to app_users(id).
--   - Grants least-privilege DML permissions to runtime role 'tourai_app'.
--   - Denies direct PostgREST client access (anon, authenticated) via RLS & REVOKE.
--   - Avoids destructive CASCADE in rollback.
-- ==============================================================================

BEGIN;

-- 1. Create app_users table
CREATE TABLE IF NOT EXISTS public.app_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    display_name TEXT,
    avatar_url TEXT,
    email_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Case-insensitive unique index for email lookups
CREATE UNIQUE INDEX IF NOT EXISTS idx_app_users_email_lower ON public.app_users (LOWER(email));

-- 2. Create auth_identities table
CREATE TABLE IF NOT EXISTS public.auth_identities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.app_users(id) ON DELETE CASCADE,
    provider TEXT NOT NULL, -- 'email' or 'google'
    provider_user_id TEXT NOT NULL, -- normalized email address for 'email', Google immutable 'sub' for 'google'
    password_hash TEXT NULL, -- Argon2id hash (stored only for 'email' provider)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_identities_provider_user UNIQUE (provider, provider_user_id)
);

CREATE INDEX IF NOT EXISTS idx_auth_identities_user_id ON public.auth_identities (user_id);

-- Ensure at most one email identity per user
CREATE UNIQUE INDEX IF NOT EXISTS uq_auth_identities_user_email_provider 
    ON public.auth_identities (user_id) WHERE provider = 'email';

-- 3. Create auth_sessions table
CREATE TABLE IF NOT EXISTS public.auth_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.app_users(id) ON DELETE CASCADE,
    refresh_token_hash TEXT UNIQUE NOT NULL, -- SHA-256 hash of refresh token
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_id ON public.auth_sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_token_hash ON public.auth_sessions (refresh_token_hash);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_active ON public.auth_sessions (user_id, expires_at) WHERE revoked_at IS NULL;

-- 4. Create auth_verification_tokens table (for secure email ownership & password setup)
CREATE TABLE IF NOT EXISTS public.auth_verification_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.app_users(id) ON DELETE CASCADE,
    token_hash TEXT UNIQUE NOT NULL, -- SHA-256 hash of random secret token
    token_type TEXT NOT NULL CHECK (token_type IN ('password_setup', 'email_verify', 'password_reset')),
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_auth_verification_tokens_lookup 
    ON public.auth_verification_tokens (token_hash, token_type) 
    WHERE used_at IS NULL;

-- 5. Automatically maintain updated_at on app_users
DROP TRIGGER IF EXISTS trg_app_users_updated_at ON public.app_users;
CREATE TRIGGER trg_app_users_updated_at
    BEFORE UPDATE ON public.app_users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

-- 6. Safe Data Migration: Map existing Supabase auth.users -> app_users
INSERT INTO public.app_users (id, email, display_name, email_verified, is_active, created_at, updated_at)
SELECT 
    id,
    LOWER(TRIM(email)),
    COALESCE(raw_user_meta_data->>'full_name', raw_user_meta_data->>'name', split_part(email, '@', 1)),
    COALESCE(email_confirmed_at IS NOT NULL, FALSE),
    TRUE,
    created_at,
    COALESCE(updated_at, created_at)
FROM auth.users
WHERE email IS NOT NULL AND TRIM(email) != ''
ON CONFLICT (id) DO UPDATE
SET email = EXCLUDED.email,
    updated_at = EXCLUDED.updated_at;

-- Create email identity with NULL password_hash
-- (Supabase bcrypt hashes are NOT migrated to Argon2id; password setup requires verified email link)
INSERT INTO public.auth_identities (user_id, provider, provider_user_id, password_hash, created_at)
SELECT 
    id,
    'email',
    LOWER(TRIM(email)),
    NULL,
    created_at
FROM auth.users
WHERE email IS NOT NULL AND TRIM(email) != ''
  AND NOT EXISTS (
      SELECT 1 FROM public.auth_identities 
      WHERE (provider = 'email' AND provider_user_id = LOWER(TRIM(auth.users.email)))
         OR (user_id = auth.users.id AND provider = 'email')
  );

-- 7. Update public.user_threads foreign key
-- Drop old foreign key constraint pointing to auth.users(id)
ALTER TABLE public.user_threads DROP CONSTRAINT IF EXISTS user_threads_user_id_fkey;

-- Add new foreign key constraint pointing to public.app_users(id)
ALTER TABLE public.user_threads
    ADD CONSTRAINT user_threads_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES public.app_users(id) ON DELETE CASCADE;

-- 8. Row Level Security (RLS) & Access Lockdown
ALTER TABLE public.app_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.auth_identities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.auth_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.auth_verification_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_threads ENABLE ROW LEVEL SECURITY;

-- Revoke direct permissions from PostgREST client roles
REVOKE ALL ON public.app_users FROM anon, authenticated;
REVOKE ALL ON public.auth_identities FROM anon, authenticated;
REVOKE ALL ON public.auth_sessions FROM anon, authenticated;
REVOKE ALL ON public.auth_verification_tokens FROM anon, authenticated;
REVOKE ALL ON public.user_threads FROM anon, authenticated;

-- Drop old Supabase auth.uid() policies from user_threads
DROP POLICY IF EXISTS "Users can only read own threads" ON public.user_threads;
DROP POLICY IF EXISTS "Users can only insert own threads" ON public.user_threads;
DROP POLICY IF EXISTS "Users can only update own threads" ON public.user_threads;
DROP POLICY IF EXISTS "Users can only delete own threads" ON public.user_threads;

-- Explicitly deny PostgREST anon and authenticated roles
DROP POLICY IF EXISTS "Deny postgrest app_users" ON public.app_users;
CREATE POLICY "Deny postgrest app_users" ON public.app_users FOR ALL TO anon, authenticated USING (false);

DROP POLICY IF EXISTS "Deny postgrest auth_identities" ON public.auth_identities;
CREATE POLICY "Deny postgrest auth_identities" ON public.auth_identities FOR ALL TO anon, authenticated USING (false);

DROP POLICY IF EXISTS "Deny postgrest auth_sessions" ON public.auth_sessions;
CREATE POLICY "Deny postgrest auth_sessions" ON public.auth_sessions FOR ALL TO anon, authenticated USING (false);

DROP POLICY IF EXISTS "Deny postgrest auth_verification_tokens" ON public.auth_verification_tokens;
CREATE POLICY "Deny postgrest auth_verification_tokens" ON public.auth_verification_tokens FOR ALL TO anon, authenticated USING (false);

DROP POLICY IF EXISTS "Deny postgrest user_threads" ON public.user_threads;
CREATE POLICY "Deny postgrest user_threads" ON public.user_threads FOR ALL TO anon, authenticated USING (false);

-- 9. Dedicated Application Runtime Role ('tourai_app')
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'tourai_app') THEN
        CREATE ROLE tourai_app WITH LOGIN PASSWORD 'CHANGE_ME_SECURE_PASSWORD';
    END IF;
END $$;

-- Schema USAGE
GRANT USAGE ON SCHEMA public TO tourai_app;

-- Grant least-privilege DML permissions on application tables
GRANT SELECT, INSERT, UPDATE, DELETE ON public.app_users TO tourai_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.auth_identities TO tourai_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.auth_sessions TO tourai_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.auth_verification_tokens TO tourai_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.user_threads TO tourai_app;

-- Grant least-privilege DML permissions on LangGraph checkpoint & store tables
GRANT SELECT, INSERT, UPDATE, DELETE ON public.checkpoints TO tourai_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.checkpoint_writes TO tourai_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.checkpoint_blobs TO tourai_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.checkpoint_migrations TO tourai_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.store TO tourai_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.store_migrations TO tourai_app;

-- Grant explicit RLS policies for tourai_app on all secured tables
DROP POLICY IF EXISTS "Allow tourai_app app_users" ON public.app_users;
CREATE POLICY "Allow tourai_app app_users" ON public.app_users FOR ALL TO tourai_app USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow tourai_app auth_identities" ON public.auth_identities;
CREATE POLICY "Allow tourai_app auth_identities" ON public.auth_identities FOR ALL TO tourai_app USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow tourai_app auth_sessions" ON public.auth_sessions;
CREATE POLICY "Allow tourai_app auth_sessions" ON public.auth_sessions FOR ALL TO tourai_app USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow tourai_app auth_verification_tokens" ON public.auth_verification_tokens;
CREATE POLICY "Allow tourai_app auth_verification_tokens" ON public.auth_verification_tokens FOR ALL TO tourai_app USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow tourai_app user_threads" ON public.user_threads;
CREATE POLICY "Allow tourai_app user_threads" ON public.user_threads FOR ALL TO tourai_app USING (true) WITH CHECK (true);

COMMIT;

-- ==============================================================================
-- ROLLBACK STRATEGY (Non-destructive to checkpoints and user_threads data):
-- To reverse this migration safely:
--   BEGIN;
--   -- 1. Restore user_threads foreign key back to auth.users(id)
--   ALTER TABLE public.user_threads DROP CONSTRAINT IF EXISTS user_threads_user_id_fkey;
--   ALTER TABLE public.user_threads ADD CONSTRAINT user_threads_user_id_fkey
--       FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
--
--   -- 2. Restore user_threads policies if reverting to Supabase GoTrue
--   DROP POLICY IF EXISTS "Deny postgrest user_threads" ON public.user_threads;
--   DROP POLICY IF EXISTS "Allow tourai_app user_threads" ON public.user_threads;
--   GRANT ALL ON public.user_threads TO authenticated;
--   CREATE POLICY "Users can only read own threads" ON public.user_threads FOR SELECT TO authenticated USING (auth.uid() = user_id);
--   CREATE POLICY "Users can only insert own threads" ON public.user_threads FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
--   CREATE POLICY "Users can only update own threads" ON public.user_threads FOR UPDATE TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
--   CREATE POLICY "Users can only delete own threads" ON public.user_threads FOR DELETE TO authenticated USING (auth.uid() = user_id);
--
--   -- 3. Drop application auth tables (ordered by foreign key dependency, avoiding CASCADE)
--   DROP TABLE IF EXISTS public.auth_verification_tokens;
--   DROP TABLE IF EXISTS public.auth_sessions;
--   DROP TABLE IF EXISTS public.auth_identities;
--   DROP TABLE IF EXISTS public.app_users;
--
--   -- 4. Clean up tourai_app grants
--   REVOKE ALL ON ALL TABLES IN SCHEMA public FROM tourai_app;
--   DROP ROLE IF EXISTS tourai_app;
--   COMMIT;
-- ==============================================================================
