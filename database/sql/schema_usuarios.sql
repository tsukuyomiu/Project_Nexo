-- ============================================================================
-- PROJETO NEXO - ENGENHARIA DE BANCO DE DADOS
-- Arquivo: database/sql/schema_usuarios.sql
-- Descrição: Modelagem física das tabelas de Identidade, Autenticação,
--            Perfis, Preferências, Sessões JWT e Recuperação de Senha.
-- Compatibilidade: SQLite 3.35+ / PostgreSQL 14+
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- 1. TABELA: usuarios
-- Armazena as credenciais, status da conta, aceite de termos e nível de acesso.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
    id                  TEXT PRIMARY KEY,
    nome                TEXT NOT NULL CHECK (length(trim(nome)) >= 1 AND length(nome) <= 100),
    email               TEXT NOT NULL UNIQUE CHECK (length(email) <= 255 AND email LIKE '%_@_%.__%'),
    senha_hash          TEXT NOT NULL,
    role                TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin', 'auditor')),
    ativo               INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1)),
    termos_aceitos      INTEGER NOT NULL DEFAULT 1 CHECK (termos_aceitos IN (0, 1)),
    termos_aceitos_em   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    ultimo_login_em     TEXT,
    criado_em           TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    atualizado_em       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);
CREATE INDEX IF NOT EXISTS idx_usuarios_role ON usuarios(role);
CREATE INDEX IF NOT EXISTS idx_usuarios_criado_em ON usuarios(criado_em DESC);

-- ----------------------------------------------------------------------------
-- 2. TABELA: perfis_preferencias
-- Relação 1:1 com `usuarios`. Armazena dados pessoais editáveis na tela
-- de Perfil (/perfil) e preferências de moeda e segurança (2FA).
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS perfis_preferencias (
    usuario_id          TEXT PRIMARY KEY,
    telefone            TEXT NOT NULL DEFAULT '' CHECK (length(telefone) <= 25),
    data_nascimento     TEXT NOT NULL DEFAULT '' CHECK (data_nascimento = '' OR length(data_nascimento) = 10),
    endereco            TEXT NOT NULL DEFAULT '' CHECK (length(endereco) <= 200),
    moeda_preferida     TEXT NOT NULL DEFAULT 'BRL' CHECK (moeda_preferida IN ('BRL', 'USD', 'EUR', 'GBP')),
    dois_fatores_ativo  INTEGER NOT NULL DEFAULT 0 CHECK (dois_fatores_ativo IN (0, 1)),
    avatar_url          TEXT DEFAULT '',
    atualizado_em       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 3. TABELA: sessoes_tokens
-- Controle de sessões autenticadas (JWT JTI), permitindo rastrear dispositivos
-- conectados e revogar tokens em caso de logout ou troca de senha.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sessoes_tokens (
    id                  TEXT PRIMARY KEY,
    usuario_id          TEXT NOT NULL,
    token_jti           TEXT NOT NULL UNIQUE,
    ip_origem           TEXT,
    user_agent          TEXT,
    revogado            INTEGER NOT NULL DEFAULT 0 CHECK (revogado IN (0, 1)),
    revogado_em         TEXT,
    expira_em           TEXT NOT NULL,
    criado_em           TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sessoes_usuario ON sessoes_tokens(usuario_id);
CREATE INDEX IF NOT EXISTS idx_sessoes_jti ON sessoes_tokens(token_jti);

-- ----------------------------------------------------------------------------
-- 4. TABELA: codigos_recuperacao
-- Suporta o fluxo de 2 etapas da tela /redefinir-senha (envio de código de
-- segurança por e-mail + redefinição da senha com expiração e limite de uso).
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS codigos_recuperacao (
    id                  TEXT PRIMARY KEY,
    usuario_id          TEXT NOT NULL,
    email               TEXT NOT NULL,
    codigo_hash         TEXT NOT NULL,
    utilizado           INTEGER NOT NULL DEFAULT 0 CHECK (utilizado IN (0, 1)),
    tentativas          INTEGER NOT NULL DEFAULT 0,
    ip_solicitante      TEXT,
    expira_em           TEXT NOT NULL,
    utilizado_em        TEXT,
    criado_em           TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_codigos_rec_email ON codigos_recuperacao(email, utilizado);
CREATE INDEX IF NOT EXISTS idx_codigos_rec_usuario ON codigos_recuperacao(usuario_id);
