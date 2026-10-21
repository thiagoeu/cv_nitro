-- Schema de Banco de Dados para CV Nitro (Supabase / PostgreSQL)
-- Execute este script no SQL Editor do painel do seu projeto Supabase

CREATE TABLE IF NOT EXISTS applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_title TEXT NOT NULL,
    job_url TEXT DEFAULT '',
    language VARCHAR(10) DEFAULT 'pt',
    technologies JSONB DEFAULT '[]'::JSONB,
    resume_md TEXT NOT NULL,
    cover_letter_md TEXT DEFAULT '',
    job_description TEXT DEFAULT '',
    base_resume TEXT DEFAULT '',
    github_username TEXT DEFAULT '',
    diagnostic JSONB DEFAULT '{}'::JSONB,
    has_cover_letter BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Índice para ordenação rápida por data (mais recentes primeiro)
CREATE INDEX IF NOT EXISTS idx_applications_created_at ON applications (created_at DESC);

-- Habilitar RLS (Row Level Security) e permitir acesso anônimo com a chave pública
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Acesso público anônimo total para aplicações"
ON applications
FOR ALL
TO anon, authenticated
USING (true)
WITH CHECK (true);
