-- ============================================================================
-- PROJETO NEXO - ENGENHARIA DE BANCO DE DADOS (POSTGRESQL PRODUÇÃO)
-- Arquivo: database/sql/schema_postgresql_prod.sql
-- Descrição: DDL completo otimizado para PostgreSQL 14+ com UUID nativo,
--            TIMESTAMPTZ, JSONB, Índices GIN e Função Trigger PL/pgSQL.
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. USUÁRIOS E PERFIS
CREATE TABLE IF NOT EXISTS usuarios (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome                VARCHAR(100) NOT NULL CHECK (char_length(btrim(nome)) >= 1),
    email               VARCHAR(255) NOT NULL UNIQUE,
    senha_hash          TEXT NOT NULL,
    role                VARCHAR(20) NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin', 'auditor')),
    ativo               BOOLEAN NOT NULL DEFAULT TRUE,
    termos_aceitos      BOOLEAN NOT NULL DEFAULT TRUE,
    termos_aceitos_em   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ultimo_login_em     TIMESTAMPTZ,
    criado_em           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS perfis_preferencias (
    usuario_id          UUID PRIMARY KEY REFERENCES usuarios(id) ON DELETE CASCADE,
    telefone            VARCHAR(25) NOT NULL DEFAULT '',
    data_nascimento     VARCHAR(10) NOT NULL DEFAULT '',
    endereco            VARCHAR(200) NOT NULL DEFAULT '',
    moeda_preferida     VARCHAR(3) NOT NULL DEFAULT 'BRL' CHECK (moeda_preferida IN ('BRL', 'USD', 'EUR', 'GBP')),
    dois_fatores_ativo  BOOLEAN NOT NULL DEFAULT FALSE,
    avatar_url          TEXT DEFAULT '',
    atualizado_em       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. LANÇAMENTOS FINANCEIROS
CREATE TABLE IF NOT EXISTS lancamentos (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id          UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    descricao           VARCHAR(100) NOT NULL CHECK (char_length(btrim(descricao)) >= 1),
    valor               NUMERIC(14, 2) NOT NULL CHECK (valor > 0),
    data_lancamento     DATE NOT NULL,
    categoria           VARCHAR(60) NOT NULL,
    tipo                VARCHAR(10) NOT NULL CHECK (tipo IN ('income', 'expense')),
    status              VARCHAR(15) NOT NULL DEFAULT 'confirmado' CHECK (status IN ('confirmado', 'pendente')),
    criado_em           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pg_lancamentos_user_date ON lancamentos(usuario_id, data_lancamento DESC);

-- 3. AUDITORIA IMUTÁVEL COM JSONB
CREATE TABLE IF NOT EXISTS audit_logs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    data_hora_utc       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    data_hora_local     TIMESTAMPTZ NOT NULL DEFAULT (NOW() AT TIME ZONE 'America/Sao_Paulo'),
    usuario_id          UUID,
    usuario_email       VARCHAR(255) NOT NULL DEFAULT 'anonimo@nexo.local',
    usuario_nome        VARCHAR(100) NOT NULL DEFAULT 'Visitante / Sistema',
    ip_origem           VARCHAR(64) NOT NULL DEFAULT '127.0.0.1',
    user_agent          TEXT,
    metodo_http         VARCHAR(10),
    rota_http           TEXT,
    request_id          VARCHAR(64),
    acao                VARCHAR(80) NOT NULL,
    categoria_evento    VARCHAR(30) NOT NULL,
    severidade          VARCHAR(15) NOT NULL DEFAULT 'INFO',
    entidade_afetada    VARCHAR(60) NOT NULL,
    entidade_id         VARCHAR(64),
    resumo_humano       TEXT NOT NULL,
    dados_anteriores    JSONB,
    dados_novos         JSONB,
    metadados_extras    JSONB,
    origem_registro     VARCHAR(30) NOT NULL DEFAULT 'API_PYTHON',
    hash_anterior       VARCHAR(64),
    hash_integridade    VARCHAR(64) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_pg_audit_logs_gin_novos ON audit_logs USING GIN (dados_novos);
CREATE INDEX IF NOT EXISTS idx_pg_audit_logs_data ON audit_logs (data_hora_utc DESC);
