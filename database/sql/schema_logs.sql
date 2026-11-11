-- ============================================================================
-- PROJETO NEXO - ENGENHARIA DE BANCO DE DADOS & AUDITORIA 360°
-- Arquivo: database/sql/schema_logs.sql
-- Descrição: Sistema de Logs Imutáveis (Append-Only), Trilha de Auditoria
--            Completa (Quem fez, Quando fez, O que fez, Antes e Depois),
--            Logs de Tráfego HTTP e Triggers SQL Nativos.
-- Compatibilidade: SQLite 3.35+ / PostgreSQL 14+
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- 1. TABELA: audit_logs (Trilha de Auditoria de Negócio e Banco - IMUTÁVEL)
-- Registra absolutamente tudo o que acontece no sistema:
--   - QUEM FEZ: usuario_id, usuario_email, usuario_nome, ip_origem, user_agent
--   - QUANDO FEZ: data_hora_utc (ISO 8601) e data_hora_local (America/Sao_Paulo)
--   - O QUE FEZ: acao, categoria_evento, entidade_afetada, entidade_id,
--                resumo_humano, dados_anteriores (JSON) e dados_novos (JSON)
--   - INTEGRIDADE: hash_anterior + hash_integridade (SHA-256 encadeado)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    id                  TEXT PRIMARY KEY,
    data_hora_utc       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    data_hora_local     TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f-03:00', 'now', '-3 hours')),
    usuario_id          TEXT,
    usuario_email       TEXT NOT NULL DEFAULT 'anonimo@nexo.local',
    usuario_nome        TEXT NOT NULL DEFAULT 'Visitante / Sistema',
    ip_origem           TEXT NOT NULL DEFAULT '127.0.0.1',
    user_agent          TEXT NOT NULL DEFAULT 'SQL-Engine/Internal',
    metodo_http         TEXT,
    rota_http           TEXT,
    request_id          TEXT,
    acao                TEXT NOT NULL,
    categoria_evento    TEXT NOT NULL CHECK (categoria_evento IN (
                            'AUTH', 'TRANSACTION', 'PROFILE', 'PREFERENCES',
                            'SECURITY', 'REPORT', 'FRONTEND', 'DATABASE', 'SYSTEM'
                        )),
    severidade          TEXT NOT NULL DEFAULT 'INFO' CHECK (severidade IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    entidade_afetada    TEXT NOT NULL,
    entidade_id         TEXT,
    resumo_humano       TEXT NOT NULL,
    dados_anteriores    TEXT, -- JSON string contendo snapshot ANTES da ação
    dados_novos         TEXT, -- JSON string contendo snapshot DEPOIS da ação
    metadados_extras    TEXT, -- JSON string com contexto adicional
    origem_registro     TEXT NOT NULL DEFAULT 'API_PYTHON' CHECK (origem_registro IN (
                            'API_PYTHON', 'SQL_TRIGGER', 'FRONTEND_TELEMETRY', 'SYSTEM'
                        )),
    hash_anterior       TEXT,
    hash_integridade    TEXT NOT NULL
);

-- Índices para buscas instantâneas por usuário, data/hora, ação e entidade
CREATE INDEX IF NOT EXISTS idx_audit_logs_data_utc ON audit_logs(data_hora_utc DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_usuario ON audit_logs(usuario_id, data_hora_utc DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_email ON audit_logs(usuario_email);
CREATE INDEX IF NOT EXISTS idx_audit_logs_acao ON audit_logs(acao, categoria_evento);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entidade ON audit_logs(entidade_afetada, entidade_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_severidade ON audit_logs(severidade);

-- ----------------------------------------------------------------------------
-- 2. TABELA: access_logs (Tráfego HTTP de Todas as Requisições da API)
-- Registra cada chamada HTTP recebida pelo servidor, tempo de resposta em ms,
-- status code, rota, query string, IP e tamanho da resposta.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS access_logs (
    id                      TEXT PRIMARY KEY,
    data_hora_utc           TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    data_hora_local         TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f-03:00', 'now', '-3 hours')),
    request_id              TEXT NOT NULL UNIQUE,
    usuario_id              TEXT,
    usuario_email           TEXT,
    metodo_http             TEXT NOT NULL,
    rota                    TEXT NOT NULL,
    query_params            TEXT,
    status_code             INTEGER NOT NULL,
    tempo_resposta_ms       REAL NOT NULL,
    ip_origem               TEXT NOT NULL,
    user_agent              TEXT,
    erro_detalhe            TEXT
);

CREATE INDEX IF NOT EXISTS idx_access_logs_data ON access_logs(data_hora_utc DESC);
CREATE INDEX IF NOT EXISTS idx_access_logs_usuario ON access_logs(usuario_id, data_hora_utc DESC);
CREATE INDEX IF NOT EXISTS idx_access_logs_status ON access_logs(status_code);
CREATE INDEX IF NOT EXISTS idx_access_logs_rota ON access_logs(rota);

-- ----------------------------------------------------------------------------
-- 3. PROTEÇÃO DE IMUTABILIDADE (APPEND-ONLY) EM audit_logs
-- Impede que qualquer pessoa ou script altere ou apague registros de auditoria.
-- ----------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_audit_logs_prevent_update;
CREATE TRIGGER trg_audit_logs_prevent_update
BEFORE UPDATE ON audit_logs
BEGIN
    SELECT RAISE(ABORT, 'VIOLACAO DE SEGURANCA NEXO: A tabela audit_logs e imutavel (Append-Only). Atualizacoes nao sao permitidas.');
END;

DROP TRIGGER IF EXISTS trg_audit_logs_prevent_delete;
CREATE TRIGGER trg_audit_logs_prevent_delete
BEFORE DELETE ON audit_logs
BEGIN
    SELECT RAISE(ABORT, 'VIOLACAO DE SEGURANCA NEXO: A tabela audit_logs e imutavel (Append-Only). Exclusoes nao sao permitidas.');
END;

-- ----------------------------------------------------------------------------
-- 4. TRIGGERS SQL NATIVOS DE AUDITORIA AUTOMÁTICA NAS TABELAS DE DOMÍNIO
-- Garantem que qualquer INSERT, UPDATE ou DELETE em `lancamentos` ou `usuarios`
-- gere um registro automático de nível de banco (`SQL_TRIGGER`) com os valores
-- exatos antes (OLD) e depois (NEW).
-- ----------------------------------------------------------------------------

-- 4.1 Trigger: Novo Lançamento Financeiro (INSERT em lancamentos)
DROP TRIGGER IF EXISTS trg_audit_lancamentos_insert;
CREATE TRIGGER trg_audit_lancamentos_insert
AFTER INSERT ON lancamentos
BEGIN
    INSERT INTO audit_logs (
        id,
        data_hora_utc,
        data_hora_local,
        usuario_id,
        usuario_email,
        usuario_nome,
        acao,
        categoria_evento,
        severidade,
        entidade_afetada,
        entidade_id,
        resumo_humano,
        dados_anteriores,
        dados_novos,
        origem_registro,
        hash_integridade
    )
    VALUES (
        'sql-trg-' || lower(hex(randomblob(12))),
        strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
        strftime('%Y-%m-%dT%H:%M:%f-03:00', 'now', '-3 hours'),
        NEW.usuario_id,
        COALESCE((SELECT email FROM usuarios WHERE id = NEW.usuario_id), 'desconhecido@nexo.local'),
        COALESCE((SELECT nome FROM usuarios WHERE id = NEW.usuario_id), 'Usuário'),
        'SQL_LANCAMENTO_INSERT',
        'DATABASE',
        'INFO',
        'lancamentos',
        NEW.id,
        '[SQL Trigger] Lançamento criado (' || NEW.tipo || '): "' || NEW.descricao || '" no valor de ' || printf('%.2f', NEW.valor) || ' na categoria ' || NEW.categoria,
        NULL,
        json_object(
            'id', NEW.id,
            'usuario_id', NEW.usuario_id,
            'descricao', NEW.descricao,
            'valor', NEW.valor,
            'data_lancamento', NEW.data_lancamento,
            'categoria', NEW.categoria,
            'tipo', NEW.tipo,
            'status', NEW.status
        ),
        'SQL_TRIGGER',
        lower(hex(randomblob(32)))
    );
END;

-- 4.2 Trigger: Edição de Lançamento Financeiro (UPDATE em lancamentos)
DROP TRIGGER IF EXISTS trg_audit_lancamentos_update;
CREATE TRIGGER trg_audit_lancamentos_update
AFTER UPDATE ON lancamentos
BEGIN
    INSERT INTO audit_logs (
        id,
        data_hora_utc,
        data_hora_local,
        usuario_id,
        usuario_email,
        usuario_nome,
        acao,
        categoria_evento,
        severidade,
        entidade_afetada,
        entidade_id,
        resumo_humano,
        dados_anteriores,
        dados_novos,
        origem_registro,
        hash_integridade
    )
    VALUES (
        'sql-trg-' || lower(hex(randomblob(12))),
        strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
        strftime('%Y-%m-%dT%H:%M:%f-03:00', 'now', '-3 hours'),
        NEW.usuario_id,
        COALESCE((SELECT email FROM usuarios WHERE id = NEW.usuario_id), 'desconhecido@nexo.local'),
        COALESCE((SELECT nome FROM usuarios WHERE id = NEW.usuario_id), 'Usuário'),
        'SQL_LANCAMENTO_UPDATE',
        'DATABASE',
        'INFO',
        'lancamentos',
        NEW.id,
        '[SQL Trigger] Lançamento atualizado: "' || OLD.descricao || '" (' || printf('%.2f', OLD.valor) || ') -> "' || NEW.descricao || '" (' || printf('%.2f', NEW.valor) || ')',
        json_object(
            'id', OLD.id,
            'descricao', OLD.descricao,
            'valor', OLD.valor,
            'data_lancamento', OLD.data_lancamento,
            'categoria', OLD.categoria,
            'tipo', OLD.tipo,
            'status', OLD.status
        ),
        json_object(
            'id', NEW.id,
            'descricao', NEW.descricao,
            'valor', NEW.valor,
            'data_lancamento', NEW.data_lancamento,
            'categoria', NEW.categoria,
            'tipo', NEW.tipo,
            'status', NEW.status
        ),
        'SQL_TRIGGER',
        lower(hex(randomblob(32)))
    );
END;

-- 4.3 Trigger: Exclusão de Lançamento Financeiro (DELETE em lancamentos)
DROP TRIGGER IF EXISTS trg_audit_lancamentos_delete;
CREATE TRIGGER trg_audit_lancamentos_delete
AFTER DELETE ON lancamentos
BEGIN
    INSERT INTO audit_logs (
        id,
        data_hora_utc,
        data_hora_local,
        usuario_id,
        usuario_email,
        usuario_nome,
        acao,
        categoria_evento,
        severidade,
        entidade_afetada,
        entidade_id,
        resumo_humano,
        dados_anteriores,
        dados_novos,
        origem_registro,
        hash_integridade
    )
    VALUES (
        'sql-trg-' || lower(hex(randomblob(12))),
        strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
        strftime('%Y-%m-%dT%H:%M:%f-03:00', 'now', '-3 hours'),
        OLD.usuario_id,
        COALESCE((SELECT email FROM usuarios WHERE id = OLD.usuario_id), 'desconhecido@nexo.local'),
        COALESCE((SELECT nome FROM usuarios WHERE id = OLD.usuario_id), 'Usuário'),
        'SQL_LANCAMENTO_DELETE',
        'DATABASE',
        'WARNING',
        'lancamentos',
        OLD.id,
        '[SQL Trigger] Lançamento excluído (' || OLD.tipo || '): "' || OLD.descricao || '" no valor de ' || printf('%.2f', OLD.valor),
        json_object(
            'id', OLD.id,
            'usuario_id', OLD.usuario_id,
            'descricao', OLD.descricao,
            'valor', OLD.valor,
            'data_lancamento', OLD.data_lancamento,
            'categoria', OLD.categoria,
            'tipo', OLD.tipo,
            'status', OLD.status
        ),
        NULL,
        'SQL_TRIGGER',
        lower(hex(randomblob(32)))
    );
END;

-- 4.4 Trigger: Alteração em Conta de Usuário (UPDATE em usuarios)
DROP TRIGGER IF EXISTS trg_audit_usuarios_update;
CREATE TRIGGER trg_audit_usuarios_update
AFTER UPDATE ON usuarios
BEGIN
    INSERT INTO audit_logs (
        id,
        data_hora_utc,
        data_hora_local,
        usuario_id,
        usuario_email,
        usuario_nome,
        acao,
        categoria_evento,
        severidade,
        entidade_afetada,
        entidade_id,
        resumo_humano,
        dados_anteriores,
        dados_novos,
        origem_registro,
        hash_integridade
    )
    VALUES (
        'sql-trg-' || lower(hex(randomblob(12))),
        strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
        strftime('%Y-%m-%dT%H:%M:%f-03:00', 'now', '-3 hours'),
        NEW.id,
        NEW.email,
        NEW.nome,
        'SQL_USUARIO_UPDATE',
        'DATABASE',
        CASE WHEN OLD.senha_hash != NEW.senha_hash THEN 'WARNING' ELSE 'INFO' END,
        'usuarios',
        NEW.id,
        '[SQL Trigger] Registro de usuário atualizado para ' || NEW.email ||
        CASE WHEN OLD.senha_hash != NEW.senha_hash THEN ' (Hash de senha alterado)' ELSE '' END,
        json_object(
            'id', OLD.id,
            'nome', OLD.nome,
            'email', OLD.email,
            'role', OLD.role,
            'ativo', OLD.ativo,
            'senha_alterada', (OLD.senha_hash != NEW.senha_hash)
        ),
        json_object(
            'id', NEW.id,
            'nome', NEW.nome,
            'email', NEW.email,
            'role', NEW.role,
            'ativo', NEW.ativo,
            'senha_alterada', (OLD.senha_hash != NEW.senha_hash)
        ),
        'SQL_TRIGGER',
        lower(hex(randomblob(32)))
    );
END;

-- ----------------------------------------------------------------------------
-- 5. VIEW DE AUDITORIA COMPLETA (vw_auditoria_completa)
-- Facilita consultas diretas no banco exibindo Quem fez, Quando fez, O que fez,
-- Rota, IP, Severidade e os estados Antes/Depois lado a lado.
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS vw_auditoria_completa;
CREATE VIEW vw_auditoria_completa AS
SELECT
    a.id AS log_id,
    a.data_hora_local AS quando_fez_brasilia,
    a.data_hora_utc AS quando_fez_utc,
    a.usuario_nome AS quem_fez_nome,
    a.usuario_email AS quem_fez_email,
    a.usuario_id AS quem_fez_id,
    a.ip_origem AS de_qual_ip,
    a.acao AS codigo_acao,
    a.categoria_evento AS modulo,
    a.severidade,
    a.resumo_humano AS o_que_fez,
    a.entidade_afetada,
    a.entidade_id,
    a.dados_anteriores AS como_estava_antes,
    a.dados_novos AS como_ficou_depois,
    a.metodo_http,
    a.rota_http,
    a.origem_registro,
    a.hash_integridade
FROM audit_logs a
ORDER BY a.data_hora_utc DESC;
