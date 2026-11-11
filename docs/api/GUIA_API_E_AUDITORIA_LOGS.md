# Guia Completo da API e Manual de Consulta de Logs — Projeto Nexo

Este guia documenta todos os endpoints da API REST (`/api/v1`) e mostra todas as formas de consultar os **Logs de Auditoria e Tráfego** em **Python**, **API REST** e **SQL**.

---

## 1. Como Iniciar o Servidor Back-End

No terminal, a partir da raiz do projeto (`Project_Nexo`):

```powershell
# 1. Entre na pasta do backend
cd backend

# 2. (Opcional) Inicialize/verifique o banco SQL e os seeds manualmente
python -m app.db.scripts.init_db

# 3. Inicie o servidor FastAPI com recarregamento automático
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

* **Swagger UI (Documentação Interativa):** `http://localhost:8000/docs`
* **ReDoc:** `http://localhost:8000/redoc`
* **Healthcheck:** `http://localhost:8000/health`

> [!TIP]
> **Conta de Administrador pré-cadastrada pelo Seed (`admin_seed.json`):**
> * **E-mail:** `admin@nexo.com`
> * **Senha:** `Admin@Nexo2026`

---

## 2. Como Consultar Todos os Logs (Quem fez, a Hora que fez e O que fez)

Você tem **4 maneiras** imediatas de receber e inspecionar tudo o que acontece no site:

### Forma 1: Pelo Terminal via Script Python CLI (`inspect_logs.py`)
Sem precisar abrir navegador ou cliente SQL, execute dentro da pasta `backend/`:

```powershell
# Ver os últimos 25 eventos de auditoria (Quem fez, Hora de Brasília, IP e O que fez)
python -m app.db.scripts.inspect_logs

# Filtrar apenas o que um usuário específico fez
python -m app.db.scripts.inspect_logs --email admin@nexo.com

# Filtrar por módulo (AUTH, TRANSACTION, PROFILE, PREFERENCES, SECURITY, DATABASE, FRONTEND)
python -m app.db.scripts.inspect_logs --category TRANSACTION

# Ver o log de tráfego HTTP (todas as rotas chamadas, status code e tempo em ms)
python -m app.db.scripts.inspect_logs --access --limit 50
```

### Forma 2: Pela API REST (JSON / Navegador / Swagger)
* **Linha do Tempo Humana (`GET /api/v1/logs/timeline`):**
  Retorna uma lista cronológica limpa:
  ```json
  {
    "ok": true,
    "count": 1,
    "timeline": [
      {
        "log_id": "9f8c1d22-...",
        "quando_fez": "2026-11-10T20:50:08.677-03:00",
        "quem_fez": "Gabriel Nonato Senior <gabriel@nexo.com>",
        "o_que_fez": "Gabriel Nonato Senior (gabriel@nexo.com) editou o lançamento 'Aluguel Apartamento' -> 'Aluguel + Condomínio' (Valor: 2800.00 -> 3250.00).",
        "acao": "TRANSACTION_UPDATED",
        "modulo": "TRANSACTION",
        "severidade": "INFO",
        "ip": "127.0.0.1",
        "rota": "PUT /api/v1/transactions/dc1ebf1a-...",
        "antes": {
          "description": "Aluguel Apartamento",
          "amount": 2800.0,
          "status": "pendente"
        },
        "depois": {
          "description": "Aluguel + Condomínio",
          "amount": 3250.0,
          "status": "confirmado"
        }
      }
    ]
  }
  ```
* **Busca Avançada de Auditoria (`GET /api/v1/logs/audit`):**
  Suporta parâmetros de filtro: `?email=...&acao=...&categoria=...&origem=...&severidade=...&data_inicio=YYYY-MM-DD&data_fim=YYYY-MM-DD&q=texto`.
* **Estatísticas Gerais (`GET /api/v1/logs/stats`):**
  Retorna total de ações, usuários mais ativos, contagem por categoria e latência média HTTP.
* **Exportação para Excel/CSV ou JSON (`GET /api/v1/logs/export?format=csv`):**
  Baixa imediatamente a planilha `nexo_audit_logs.csv` com todo o histórico.

### Forma 3: Diretamente em SQL (`vw_auditoria_completa`)
Abra o arquivo `backend/data/nexo.db` em qualquer cliente SQL (DBeaver, VS Code SQLite Viewer) e execute:

```sql
-- 1. Ver tudo o que aconteceu no site (Quem fez, Quando fez e O que fez)
SELECT
    quando_fez_brasilia,
    quem_fez_nome,
    quem_fez_email,
    de_qual_ip,
    codigo_acao,
    o_que_fez,
    como_estava_antes,
    como_ficou_depois
FROM vw_auditoria_completa
ORDER BY quando_fez_utc DESC;

-- 2. Auditar especificamente edições ou exclusões financeiras
SELECT *
FROM vw_auditoria_completa
WHERE modulo = 'TRANSACTION'
  AND codigo_acao IN ('TRANSACTION_UPDATED', 'TRANSACTION_DELETED');

-- 3. Auditar tentativas de login malsucedidas ou eventos de segurança
SELECT *
FROM vw_auditoria_completa
WHERE severidade IN ('WARNING', 'ERROR', 'CRITICAL');
```

### Forma 4: Arquivos Estruturados em Disco (`backend/logs/`)
* `backend/logs/nexo_audit.jsonl`: Cada linha é um objeto JSON completo de auditoria.
* `backend/logs/nexo_access.jsonl`: Cada linha é uma requisição HTTP cronometrada.

---

## 3. Resumo de Todos os Endpoints da API (`/api/v1`)

| Categoria | Método | Endpoint | Autenticação | Descrição |
| :--- | :--- | :--- | :--- | :--- |
| **Auth** | `POST` | `/api/v1/auth/signup` | Pública | Cria usuário + perfil e retorna token JWT |
| **Auth** | `POST` | `/api/v1/auth/login` | Pública | Autentica usuário e retorna token JWT |
| **Auth** | `POST` | `/api/v1/auth/logout` | Bearer JWT | Revoga o token JWT da sessão atual |
| **Auth** | `POST` | `/api/v1/auth/forgot-password` | Pública | Gera código de 6 dígitos para recuperação |
| **Auth** | `POST` | `/api/v1/auth/reset-password` | Pública | Valida código de 6 dígitos e redefine a senha |
| **Auth** | `POST` | `/api/v1/auth/change-password` | Bearer JWT | Troca a senha do usuário logado |
| **Usuários** | `GET` | `/api/v1/users/me` | Bearer JWT | Retorna perfil e preferências do usuário |
| **Usuários** | `PUT` | `/api/v1/users/me/profile` | Bearer JWT | Atualiza nome, e-mail, telefone, nascimento e endereço |
| **Usuários** | `PUT` | `/api/v1/users/me/preferences` | Bearer JWT | Atualiza moeda (`BRL`, `USD`, `EUR`, `GBP`) e 2FA |
| **Lançamentos** | `GET` | `/api/v1/transactions` | Bearer JWT | Lista receitas e despesas do usuário |
| **Lançamentos** | `GET` | `/api/v1/transactions/categories` | Pública | Lista categorias oficiais de receita e despesa |
| **Lançamentos** | `POST` | `/api/v1/transactions` | Bearer JWT | Registra nova receita ou despesa |
| **Lançamentos** | `PUT` | `/api/v1/transactions/{id}` | Bearer JWT | Edita lançamento existente |
| **Lançamentos** | `DELETE` | `/api/v1/transactions/{id}` | Bearer JWT | Remove lançamento existente |
| **Dashboard** | `GET` | `/api/v1/dashboard/summary` | Bearer JWT | Retorna totais do mês, mês anterior e gráfico por categoria |
| **Dashboard** | `POST` | `/api/v1/dashboard/reports` | Bearer JWT | Gera relatório consolidado com hash SHA-256 |
| **Logs** | `GET` | `/api/v1/logs/audit` | Dev / Admin | Consulta completa da tabela `audit_logs` |
| **Logs** | `GET` | `/api/v1/logs/timeline` | Dev / Admin | Feed cronológico legível para humanos |
| **Logs** | `GET` | `/api/v1/logs/access` | Dev / Admin | Histórico de tráfego HTTP e latência |
| **Logs** | `GET` | `/api/v1/logs/stats` | Dev / Admin | Estatísticas gerais de uso e auditoria |
| **Logs** | `GET` | `/api/v1/logs/export` | Dev / Admin | Download dos logs em `.csv` ou `.json` |
| **Logs** | `POST` | `/api/v1/logs/frontend-event` | Opcional | Registra telemetria/eventos vindos do Front-End |
