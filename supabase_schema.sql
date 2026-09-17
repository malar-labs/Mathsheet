-- MathSheet Pro — learner accounts and saved progress.
-- Paste this into the Supabase SQL Editor and run it once:
-- https://supabase.com/dashboard/project/_/sql
--
-- Safe to re-run: every statement is IF NOT EXISTS.

create table if not exists learners (
    id              bigint generated always as identity primary key,
    -- lower-cased, what they type to sign in
    username        text        not null unique,
    -- what they typed, shown back to them with their own capitals
    display_name    text        not null,
    pin_hash        text        not null,
    grade           integer,
    created_at      timestamptz not null default now(),
    last_seen       timestamptz not null default now(),
    -- A 4-digit PIN is only 10,000 guesses, so the lockout below is the real
    -- defence, not the hash. Five wrong tries parks the account for 15 minutes.
    failed_attempts integer     not null default 0,
    locked_until    timestamptz
);

create table if not exists progress (
    learner_id  bigint      not null references learners(id) on delete cascade,
    unit_key    text        not null,   -- "grade9_rational-numbers"
    question_id text        not null,
    verdict     text        not null check (verdict in ('correct', 'close', 'wrong')),
    attempts    integer     not null default 1,
    updated_at  timestamptz not null default now(),
    primary key (learner_id, unit_key, question_id)
);

create index if not exists progress_learner_unit_idx on progress (learner_id, unit_key);

-- The app reaches Supabase with the service_role key, which bypasses RLS, so
-- enabling RLS with no policies costs the app nothing and means the publishable
-- key — which is designed to be public — can read no learner data at all.
alter table learners enable row level security;
alter table progress enable row level security;
