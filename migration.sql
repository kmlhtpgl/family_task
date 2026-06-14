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

CREATE TABLE IF NOT EXISTS public.prayer_logs (
    id SERIAL PRIMARY KEY,
    person_id INTEGER NOT NULL,
    person_type TEXT NOT NULL CHECK (person_type IN ('kid', 'parent')),
    prayer_name TEXT NOT NULL CHECK (prayer_name IN ('Fajr', 'Zuhr', 'Asr', 'Maghrib', 'Isha')),
    prayer_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(person_id, person_type, prayer_name, prayer_date)
);
