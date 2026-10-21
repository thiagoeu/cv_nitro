-- Schema de Banco de Dados para CV Nitro (Supabase / PostgreSQL)
-- Execute este script no SQL Editor do painel do seu projeto Supabase

-- 1. Tabela de Candidaturas e Currículos
CREATE TABLE IF NOT EXISTS applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
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

-- Garantir adição de user_id caso a tabela já exista
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'applications' AND column_name = 'user_id') THEN 
        ALTER TABLE applications ADD COLUMN user_id UUID; 
    END IF; 
END $$;

-- Índices para buscas e ordenação rápida
CREATE INDEX IF NOT EXISTS idx_applications_created_at ON applications (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_applications_user_id ON applications (user_id);

-- Habilitar RLS em applications
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Acesso público anônimo total para aplicações" ON applications;
CREATE POLICY "Acesso público anônimo e autenticado para aplicações"
ON applications
FOR ALL
TO anon, authenticated
USING (true)
WITH CHECK (true);

-- 2. Tabela de Perfil do Candidato (Reaproveitamento de Dados e Cache)
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id UUID PRIMARY KEY,
    email TEXT DEFAULT '',
    full_name TEXT DEFAULT '',
    base_resume TEXT DEFAULT '',
    github_username TEXT DEFAULT '',
    cached_repos JSONB DEFAULT '[]'::JSONB,
    skills JSONB DEFAULT '[]'::JSONB,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Habilitar RLS em user_profiles
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Acesso a perfis de usuário" ON user_profiles;
CREATE POLICY "Acesso a perfis de usuário"
ON user_profiles
FOR ALL
TO anon, authenticated
USING (true)
WITH CHECK (true);
