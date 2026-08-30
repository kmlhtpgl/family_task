-- Run this in your Supabase SQL Editor (https://supabase.com/dashboard > SQL Editor)
-- Creates the two new tables needed for Quran Memorization and Rewards features.

CREATE TABLE IF NOT EXISTS public.surahs (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    kid_id INTEGER REFERENCES public.kids(id) ON DELETE CASCADE,
    parent_id INTEGER REFERENCES public.parents(id) ON DELETE CASCADE,
    type TEXT NOT NULL DEFAULT 'surah',
    total_ayahs INTEGER NOT NULL,
    memorized_ayahs INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'In Progress',
    last_practiced_date TEXT,
    finished_date TEXT
);

-- Add type column if table already exists without it
ALTER TABLE public.surahs ADD COLUMN IF NOT EXISTS type TEXT DEFAULT 'surah';

CREATE TABLE IF NOT EXISTS public.points_adjustments (
    id SERIAL PRIMARY KEY,
    person_id INTEGER NOT NULL,
    person_type TEXT NOT NULL CHECK (person_type IN ('kid', 'parent')),
    points INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.reward_sessions (
    id SERIAL PRIMARY KEY,
    kid_id INTEGER REFERENCES public.kids(id) ON DELETE CASCADE,
    parent_id INTEGER REFERENCES public.parents(id) ON DELETE CASCADE,
    month TEXT NOT NULL,
    total_points INTEGER NOT NULL DEFAULT 0,
    reward_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
    paid BOOLEAN NOT NULL DEFAULT FALSE,
    paid_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.meeting_notes (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    author TEXT,
    done BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

ALTER TABLE public.meeting_notes ADD COLUMN IF NOT EXISTS done BOOLEAN DEFAULT FALSE;

CREATE TABLE IF NOT EXISTS public.meeting_comments (
    id SERIAL PRIMARY KEY,
    meeting_note_id INTEGER NOT NULL REFERENCES public.meeting_notes(id) ON DELETE CASCADE,
    author TEXT,
    body TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.meeting_templates (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    author TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.meeting_sessions (
    id SERIAL PRIMARY KEY,
    week_date DATE NOT NULL UNIQUE,
    title TEXT,
    closed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

ALTER TABLE public.meeting_notes ADD COLUMN IF NOT EXISTS session_id INTEGER REFERENCES public.meeting_sessions(id) ON DELETE CASCADE;
ALTER TABLE public.meeting_notes ADD COLUMN IF NOT EXISTS week_date DATE;

-- Backfill: assign any existing notes without a session to the most recent past Sunday
DO $$
DECLARE
    legacy_session INTEGER;
BEGIN
    IF EXISTS (SELECT 1 FROM public.meeting_notes WHERE session_id IS NULL) THEN
        INSERT INTO public.meeting_sessions (week_date, title, closed)
        SELECT (CURRENT_DATE - (EXTRACT(DOW FROM CURRENT_DATE)::int))::date, 'Legacy meeting', TRUE
        WHERE NOT EXISTS (
            SELECT 1 FROM public.meeting_sessions
            WHERE week_date = (CURRENT_DATE - (EXTRACT(DOW FROM CURRENT_DATE)::int))::date
        )
        RETURNING id INTO legacy_session;

        UPDATE public.meeting_notes
        SET session_id = COALESCE(legacy_session,
            (SELECT id FROM public.meeting_sessions
             WHERE week_date = (CURRENT_DATE - (EXTRACT(DOW FROM CURRENT_DATE)::int))::date
             LIMIT 1))
        WHERE session_id IS NULL;

        UPDATE public.meeting_notes
        SET week_date = (SELECT week_date FROM public.meeting_sessions WHERE id = meeting_notes.session_id)
        WHERE week_date IS NULL;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS public.app_settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

