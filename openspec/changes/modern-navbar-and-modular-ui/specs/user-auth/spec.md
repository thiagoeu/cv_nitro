# Spec Delta

## Purpose

Fornece interfaces dedicadas de autenticação com páginas separadas para login e cadastro, validação de credenciais com limpeza de erros e proteção de dados com RLS no Supabase.

## ADDED Requirements

### Requirement: Páginas dedicadas de login e cadastro
O sistema SHALL disponibilizar telas independentes e dedicadas para login e cadastro de usuários, permitindo alternar de modo intuitivo e focado.

#### Scenario: Acesso à página de login
- **WHEN** o usuário não autenticado clica em Entrar na barra superior
- **THEN** a tela de login dedicada é renderizada com campos de e-mail e senha e link para cadastro

#### Scenario: Acesso à página de cadastro
- **WHEN** o usuário clica em Criar Conta na barra superior ou na tela de login
- **THEN** a tela de cadastro dedicada é renderizada com campos de nome, e-mail e senha

### Requirement: Proteção de dados com RLS no banco
O sistema SHALL aplicar políticas de Row Level Security (RLS) no Supabase vinculando os registros ao identificador único `auth.uid() = user_id`.

#### Scenario: Acesso a dados autenticados com RLS
- **WHEN** um usuário autenticado consulta suas candidaturas e perfil
- **THEN** o banco de dados restringe o retorno exclusivamente às linhas pertencentes ao `user_id` autenticado
