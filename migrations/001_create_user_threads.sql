-- ==============================================================================
-- Multi-Agent-TourAI: Phase 2 Database Migration
-- Migration: 001_create_user_threads.sql
-- Description: Creates the user_threads ownership table with Row-Level Security (RLS)
--              to bind LangGraph threads to authenticated Supabase users.
-- ==============================================================================

-- 1. Create table in public schema (accessible via Supabase authenticated clients and direct pooler)
CREATE TABLE IF NOT EXISTS public.user_threads (
    thread_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT 'New Journey',
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'archived', 'failed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Indexes for efficient lookup by user and ordering by recency
CREATE INDEX IF NOT EXISTS idx_user_threads_user_id_updated_at 
    ON public.user_threads (user_id, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_user_threads_status 
    ON public.user_threads (status);

-- 3. Trigger to automatically update updated_at timestamp on row modifications
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_user_threads_updated_at ON public.user_threads;
CREATE TRIGGER trg_user_threads_updated_at
    BEFORE UPDATE ON public.user_threads
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

-- 4. Row Level Security (RLS)
-- Protects user_threads when accessed through PostgREST or Supabase Client SDK
ALTER TABLE public.user_threads ENABLE ROW LEVEL SECURITY;

-- Select Policy: Users can only see their own threads
DROP POLICY IF EXISTS "Users can only read own threads" ON public.user_threads;
CREATE POLICY "Users can only read own threads" 
    ON public.user_threads
    FOR SELECT 
    TO authenticated 
    USING (auth.uid() = user_id);

-- Insert Policy: Users can only insert threads owned by themselves
DROP POLICY IF EXISTS "Users can only insert own threads" ON public.user_threads;
CREATE POLICY "Users can only insert own threads" 
    ON public.user_threads
    FOR INSERT 
    TO authenticated 
    WITH CHECK (auth.uid() = user_id);

-- Update Policy: Users can only update their own threads
DROP POLICY IF EXISTS "Users can only update own threads" ON public.user_threads;
CREATE POLICY "Users can only update own threads" 
    ON public.user_threads
    FOR UPDATE 
    TO authenticated 
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Delete Policy: Users can only delete their own threads
DROP POLICY IF EXISTS "Users can only delete own threads" ON public.user_threads;
CREATE POLICY "Users can only delete own threads" 
    ON public.user_threads
    FOR DELETE 
    TO authenticated 
    USING (auth.uid() = user_id);

-- ==============================================================================
-- ROLLBACK INSTRUCTIONS:
-- To reverse this migration, execute:
--   DROP TABLE IF EXISTS public.user_threads CASCADE;
--   DROP FUNCTION IF EXISTS public.handle_updated_at() CASCADE;
-- ==============================================================================

