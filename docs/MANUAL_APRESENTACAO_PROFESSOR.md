# Manual de Apresentação Acadêmica e Técnica — Projeto Nexo
**Guia Completo: Como Foi Feito, Arquitetura, Banco SQL, Logs 360° e Roteiro de Demonstração para o Professor**

---

## 1. Resumo Executivo (O "Pitch" de 1 Minuto para Abrir a Apresentação)

> *"Professor, no **Projeto Nexo** nós construímos uma arquitetura completa dividindo claramente o Front-End (React + TypeScript) do Back-End (Python com FastAPI) e do Banco de Dados Relacional (SQL). Nosso grande diferencial técnico é que, além de toda a regra de negócio de autenticação JWT, perfil e gestão de lançamentos financeiros, implementamos uma **Arquitetura de Auditoria 360° Híbrida (Python + Triggers SQL)** de nível pericial: absolutamente tudo o que acontece no sistema — quem fez, o horário exato de Brasília, de qual IP, o que fez e o estado do dado antes e depois — é gravado de forma imutável (Append-Only) e encadeado com criptografia SHA-256."*

---

## 2. Como o Back-End em Python Foi Feito (FastAPI + Clean Architecture)

Para evitar código bagunçado ("código espaguete"), o Back-End em `backend/app/` foi construído usando **Arquitetura em Camadas (Layered Architecture)**:

1. **Camada de Entrada e Middlewares ([`main.py`](../../backend/app/main.py) e [`audit_middleware.py`](../../backend/app/api/middlewares/audit_middleware.py)):**
   * Toda requisição HTTP que chega ao servidor passa primeiro pelo `AuditAccessMiddleware`.
   * Ele gera um identificador único de rastreamento (`X-Request-ID`), descobre o IP real do cliente, identifica o usuário pelo Token JWT e liga um cronômetro de alta precisão (`time.perf_counter()`).
   * Ao final da requisição, ele grava automaticamente na tabela `access_logs` quanto tempo (em milissegundos) o servidor levou para responder.

2. **Camada de Segurança e Criptografia ([`security.py`](../../backend/app/core/security.py)):**
   * **Senhas:** Nunca salvamos senhas em texto puro. Usamos o algoritmo **PBKDF2-HMAC-SHA256 com 600.000 iterações** e *Salt* aleatório de 16 bytes (padrão recomendado pela OWASP).
   * **Autenticação Stateless + Stateful (JWT com `JTI`):** Ao fazer login, o usuário recebe um token JWT assinado (`HS256`). Cada token possui um ID único (`jti`) gravado na tabela `sessoes_tokens`. Isso permite **revogar o token imediatamente** se o usuário fizer logout ou redefinir a senha.

3. **Camada de Validação de Contratos ([`schemas/`](../../backend/app/schemas/)):**
   * Usamos o **Pydantic v2** para validar rigorosamente todos os JSONs que entram e saem da API (e-mails válidos, valores financeiros maiores que zero, datas ISO `YYYY-MM-DD`, moedas permitidas `BRL | USD | EUR | GBP`).
   * Se alguém enviar um dado inválido, o FastAPI bloqueia antes mesmo de chegar ao banco de dados, retornando erro HTTP `422 Unprocessable Entity` padronizado por [`exceptions.py`](../../backend/app/core/exceptions.py).

4. **Camada de Persistência e ORM ([`db/session.py`](../../backend/app/db/session.py) e [`db/models/entities.py`](../../backend/app/db/models/entities.py)):**
   * Usamos o **SQLAlchemy 2.0** (com tipagem moderna `Mapped[...]`).
   * O banco roda em **SQLite com modo `WAL` (Write-Ahead Logging)** e `PRAGMA foreign_keys = ON` no ambiente local (zero configuração para rodar em aula) e já possui script nativo para **PostgreSQL** em produção.

---

## 3. Como o Banco de Dados em SQL Foi Feito (`database/sql/`)

O banco foi modelado na **3ª Forma Normal (3FN)** e dividido em 4 módulos SQL executados automaticamente pelo inicializador [`init_db.py`](../../backend/app/db/scripts/init_db.py):

| Arquivo SQL | Tabelas / Objetos Criados | Por que foi feito assim? |
| :--- | :--- | :--- |
| **[`schema_usuarios.sql`](../../database/sql/schema_usuarios.sql)** | `usuarios`, `perfis_preferencias`, `sessoes_tokens`, `codigos_recuperacao` | Separa dados críticos de login (`usuarios`) dos dados pessoais/preferências (`perfis_preferencias` em relação 1:1 com `ON DELETE CASCADE`). |
| **[`schema_projetos.sql`](../../database/sql/schema_projetos.sql)** | `categorias_padrao`, `lancamentos` + Índices Compostos | Garante via `CHECK (valor > 0)` no próprio SQL que nunca existirá lançamento negativo ou zerado, e usa índices `(usuario_id, data_lancamento DESC)` para deixar o Dashboard instantâneo. |
| **[`schema_relatorios.sql`](../../database/sql/schema_relatorios.sql)** | `relatorios_exportados`, `vw_resumo_mensal_usuario`, `vw_despesas_por_categoria` | Cria **Views SQL analíticas** que já calculam soma de receitas, despesas, saldo líquido e distribuição por categoria direto no motor do banco. |
| **[`schema_logs.sql`](../../database/sql/schema_logs.sql)** | `audit_logs`, `access_logs`, `vw_auditoria_completa` + **6 Triggers SQL** | Implementa a rastreabilidade total e a proteção contra exclusão/adulteração de logs direto no SQL. |

---

## 4. Como Funciona o Sistema de Logs e Auditoria 360° (O Ponto Alto da Explicação)

Se o professor perguntar *"Como vocês garantem que tudo o que acontece no site é rastreado e que os logs são confiáveis?"*, explique os **4 Pilares** que implementamos:

### Pilar 1 — Dupla Camada de Captura (Python + Triggers SQL)
* **Pelo Python ([`audit_logger.py`](../../backend/app/core/audit_logger.py)):** Quando o usuário faz qualquer ação pela API (cadastro, login, erro de senha, criar/editar/excluir lançamento, mudar moeda ou perfil), o Python grava em `audit_logs` quem fez, o IP, o navegador, o horário de Brasília, uma frase em português explicando o que houve e o JSON de **antes** e **depois**.
* **Pelo Banco SQL ([`schema_logs.sql`](../../database/sql/schema_logs.sql)):** E se alguém abrir o banco de dados por fora do site e alterar um valor direto via comando SQL? Nós criamos **Triggers Nativos (`AFTER INSERT`, `AFTER UPDATE`, `AFTER DELETE`)** nas tabelas `lancamentos` e `usuarios`. O próprio banco detecta a mudança e grava um log com `origem_registro = 'SQL_TRIGGER'`, salvando o valor antigo (`OLD`) e o valor novo (`NEW`).

### Pilar 2 — Logs Imutáveis (`Append-Only`) no SQL
* Criamos dois triggers de segurança máxima no banco: `trg_audit_logs_prevent_update` e `trg_audit_logs_prevent_delete`.
* Se qualquer pessoa (mesmo com acesso ao banco) tentar rodar `DELETE FROM audit_logs` ou `UPDATE audit_logs`, o banco aborta a operação na hora com o erro:
  `VIOLACAO DE SEGURANCA NEXO: A tabela audit_logs e imutavel (Append-Only).`

### Pilar 3 — Hash Chain SHA-256 (Estilo Blockchain)
* Cada linha gravada em `audit_logs` busca o `hash_integridade` do log anterior (`hash_anterior`) e calcula um novo hash `SHA-256` somando os dados atuais. Isso cria uma corrente criptográfica: nenhuma linha do histórico pode ser adulterada sem quebrar a cadeia.

### Pilar 4 — Sanitização Automática de Dados Sensíveis (LGPD / Segurança)
* Antes de gravar qualquer JSON nos logs, a função `sanitize_payload()` varre o dicionário e substitui campos como `password`, `senha`, `token` ou `code` por `"[REDACTED]"`. Assim, auditamos que a troca de senha aconteceu, mas nunca vazamos a senha no log.

---

## 5. Roteiro Prático de Demonstração ao Vivo (Passo a Passo para Mostrar em Aula)

Siga estes 4 passos no terminal na frente do professor (leva menos de 3 minutos):

### Passo 1: Rodar a Suíte de Testes Automatizada (Mostra tudo funcionando de uma vez)
Abra o terminal na pasta do projeto e execute:
```powershell
cd backend
python -m tests.test_nexo_api
```
**O que mostrar ao professor:** Em menos de 2 segundos, o script testa 12 fluxos completos (cadastro, falha de login, login com JWT, edição de perfil, criação/edição/exclusão de lançamentos, dashboard, relatório, exportação CSV e tenta deletar os logs para provar que o Trigger SQL bloqueia!).

### Passo 2: Mostrar os Logs Formatados no Terminal (Quem fez, Hora e O que fez)
Ainda na pasta `backend`, rode:
```powershell
python -m app.db.scripts.inspect_logs --limit 15
```
**O que mostrar ao professor:** O terminal exibirá uma tabela detalhada mostrando cada ação realizada, o nome e e-mail do autor, o horário exato de Brasília (`-03:00`), o IP, se veio da API Python (`API_PYTHON`), do Front-End (`FRONTEND_TELEMETRY`) ou do Gatilho do Banco (`SQL_TRIGGER`), e a descrição em português.

Em seguida, mostre o log de tráfego HTTP com o tempo em milissegundos:
```powershell
python -m app.db.scripts.inspect_logs --access --limit 15
```

### Passo 3: Subir o Servidor e Abrir o Swagger UI no Navegador
```powershell
python -m uvicorn app.main:app --reload --port 8000
```
Abra no navegador:
* **`http://localhost:8000/docs`** -> Mostre todas as rotas documentadas e divididas por módulos (*Autenticação*, *Perfil*, *Lançamentos*, *Dashboard*, *Auditoria 360°*).
* **`http://localhost:8000/api/v1/logs/timeline`** -> Mostre o JSON em tempo real retornando `quando_fez`, `quem_fez`, `o_que_fez`, `antes` e `depois`.
* **`http://localhost:8000/api/v1/logs/export?format=csv`** -> Mostre que ao acessar essa URL o sistema já baixa automaticamente uma planilha `.csv` pronta para abrir no Excel com toda a auditoria!

---

## 6. Possíveis Perguntas do Professor (e Respostas Nota 10)

1. **Professor:** *"Por que vocês usaram FastAPI em vez de Flask ou Django?"*
   * **Sua Resposta:** *"Escolhemos o FastAPI pela alta performance assíncrona (baseado em Starlette/ASGI), pela validação automática de tipos com Pydantic v2 — que evita erros de contrato entre Front-End e Back-End — e pela geração nativa da documentação OpenAPI/Swagger em `/docs`."*

2. **Professor:** *"Se um usuário editar um lançamento de R$ 2.800 para R$ 3.250, vocês perdem o valor antigo?"*
   * **Sua Resposta:** *"Na tabela principal `lancamentos` o valor é atualizado para R$ 3.250, mas na tabela `audit_logs` nós salvamos dois campos JSON: `dados_anteriores` (com os R$ 2.800) e `dados_novos` (com os R$ 3.250), tanto via código Python quanto via Trigger `AFTER UPDATE` do próprio SQL."*

3. **Professor:** *"Como vocês garantem que ninguém vai apagar o rastro no banco de dados depois de fazer algo errado?"*
   * **Sua Resposta:** *"Implementamos Triggers `BEFORE UPDATE` e `BEFORE DELETE` na tabela `audit_logs` usando `RAISE(ABORT, ...)` no SQL, tornando a tabela estritamente Append-Only (apenas inserção), além de gravarmos uma cópia em tempo real em arquivo `.jsonl` no disco e aplicarmos hash SHA-256 encadeado em cada registro."*
