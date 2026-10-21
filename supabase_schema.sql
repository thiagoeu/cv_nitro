-- Schema de Banco de Dados para CV Nitro (Supabase / PostgreSQL)
-- Execute este script no SQL Editor do painel do seu projeto Supabase

-- 1. Tabela de Candidaturas e Currículos
CREATE TABLE IF NOT EXISTS public.applications (
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

-- Garantir adição de user_id caso a tabela já exista sem essa coluna
ALTER TABLE public.applications ADD COLUMN IF NOT EXISTS user_id UUID;

-- Índices para buscas e ordenação rápida
CREATE INDEX IF NOT EXISTS idx_applications_created_at ON public.applications (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_applications_user_id ON public.applications (user_id);

-- Habilitar RLS em applications
ALTER TABLE public.applications ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Acesso público anônimo total para aplicações" ON public.applications;
DROP POLICY IF EXISTS "Acesso público anônimo e autenticado para aplicações" ON public.applications;
DROP POLICY IF EXISTS "Usuários gerenciam suas próprias aplicações ou anônimas" ON public.applications;

CREATE POLICY "Usuários gerenciam suas próprias aplicações ou anônimas"
ON public.applications
FOR ALL
TO anon, authenticated
USING (
    (auth.uid() IS NOT NULL AND auth.uid() = user_id)
    OR (user_id IS NULL)
)
WITH CHECK (
    (auth.uid() IS NOT NULL AND auth.uid() = user_id)
    OR (user_id IS NULL)
);

-- 2. Tabela de Perfil do Candidato (Reaproveitamento de Dados e Cache)
CREATE TABLE IF NOT EXISTS public.user_profiles (
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

-- Caso a tabela user_profiles já tenha sido criada anteriormente sem algumas colunas:
ALTER TABLE public.user_profiles ADD COLUMN IF NOT EXISTS user_id UUID;
ALTER TABLE public.user_profiles ADD COLUMN IF NOT EXISTS email TEXT DEFAULT '';
ALTER TABLE public.user_profiles ADD COLUMN IF NOT EXISTS full_name TEXT DEFAULT '';
ALTER TABLE public.user_profiles ADD COLUMN IF NOT EXISTS base_resume TEXT DEFAULT '';
ALTER TABLE public.user_profiles ADD COLUMN IF NOT EXISTS github_username TEXT DEFAULT '';
ALTER TABLE public.user_profiles ADD COLUMN IF NOT EXISTS cached_repos JSONB DEFAULT '[]'::JSONB;
ALTER TABLE public.user_profiles ADD COLUMN IF NOT EXISTS skills JSONB DEFAULT '[]'::JSONB;
ALTER TABLE public.user_profiles ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now());
ALTER TABLE public.user_profiles ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now());

-- Habilitar RLS em user_profiles
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Acesso a perfis de usuário" ON public.user_profiles;
DROP POLICY IF EXISTS "Usuários gerenciam seu próprio perfil" ON public.user_profiles;

CREATE POLICY "Usuários gerenciam seu próprio perfil"
ON public.user_profiles
FOR ALL
TO anon, authenticated
USING (
    (auth.uid() IS NOT NULL AND auth.uid() = user_id)
    OR (auth.uid() IS NULL)
)
WITH CHECK (
    (auth.uid() IS NOT NULL AND auth.uid() = user_id)
    OR (auth.uid() IS NULL)
);

-- 3. Trigger Automático para Criar Perfil quando Novo Usuário se Cadastra no Supabase Auth
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_profiles (user_id, email, full_name, created_at, updated_at)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', split_part(NEW.email, '@', 1)),
        NOW(),
        NOW()
    )
    ON CONFLICT (user_id) DO UPDATE
    SET 
        email = EXCLUDED.email,
        updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Recriar trigger de forma segura e idempotente
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
