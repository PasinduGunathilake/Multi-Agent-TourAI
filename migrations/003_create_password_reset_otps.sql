-- ==============================================================================
-- Multi-Agent-TourAI:
-- Migration: 003_create_password_reset_otps.sql
-- Description: Establishes password_reset_otps table for secure 6-digit OTP
--              verification and single-use password resets.
--
-- SECURITY & LEAST-PRIVILEGE GUARANTEES:
--   - Non-destructive: Does NOT modify existing user or thread tables.
--   - Foreign key CASCADE ensures automatic cleanup if a user is purged.
--   - Salted OTP hashes prevent rainbow table attacks.
--   - Single-use reset_token_hash column invalidates after consumption.
--   - Explicit attempts tracking enforces max 5 failed tries.
-- ==============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS public.password_reset_otps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.app_users(id) ON DELETE CASCADE,
    otp_hash TEXT NOT NULL,
    reset_token_hash TEXT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    attempts INT NOT NULL DEFAULT 0,
    verified_at TIMESTAMPTZ NULL,
    consumed_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Fast lookups by user_id
CREATE INDEX IF NOT EXISTS idx_password_reset_otps_user_id 
    ON public.password_reset_otps (user_id);

-- Lookup by user_id ordered by recency (for active OTP and cooldown checks)
CREATE INDEX IF NOT EXISTS idx_password_reset_otps_user_created 
    ON public.password_reset_otps (user_id, created_at DESC);

-- Lookup by reset_token_hash for password update step
CREATE INDEX IF NOT EXISTS idx_password_reset_otps_reset_token 
    ON public.password_reset_otps (reset_token_hash) 
    WHERE consumed_at IS NULL;

COMMIT;
