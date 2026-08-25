# Projeto Nexo - Sistema de Perícia Computacional

O **Projeto Nexo** é uma plataforma moderna, com foco em alta performance e simplicidade acadêmica, voltada exclusivamente para a área de **Perícia Computacional**. O sistema visa auxiliar investigadores e peritos através de painéis analíticos, monitoramento de logs e geração de relatórios forenses.

## Tecnologias Utilizadas

A arquitetura técnica foi definida pensando em performance e facilidade de manutenção:

*   **Frontend:** [Vue.js 3](https://vuejs.org/) + [Vite](https://vitejs.dev/) - Alta reatividade e builds extremamente rápidos.
*   **Backend:** [Python](https://www.python.org/) + [FastAPI](https://fastapi.tiangolo.com/) - Processamento veloz, tipagem estática e documentação automática nativa (Swagger/OpenAPI).
*   **Banco de Dados:** SQL (SQLite / PostgreSQL) - Estruturado para armazenar Usuários, Logs, Projetos Periciais e Métricas.

## Equipe
*   **Erica:** Análise de Requisitos e Documentação (RF, RNF, Regras de Negócio e especificações de UI/UX).
*   **Gabriel & Luiza:** Engenharia de Software (Desenvolvimento Frontend/Backend e Prototipagem).

## Telas do Sistema (Escopo Principal)

Para manter o projeto factível e focado, mapeamos as seguintes telas indispensáveis:

1.  **Autenticação de Login, Cadastro e Recuperação de Senha:** Controle de acesso seguro aos recursos da plataforma.
2.  **Dashboard de Métricas Forenses:** Visão geral e gráfica das investigações.
3.  **Terminal/Grid de Logs em tempo real:** Monitoramento ativo e dinâmico das atividades analisadas.
4.  **Tela de Relatório Final:** Exportação de dados formatados e conclusivos sobre as investigações (ex: PDF).

### Telas já prototipadas / Desenvolvidas:

<div align="center">
  <img src="docs/images/login.png" alt="Tela de Login" width="45%">
  <img src="docs/images/signup.png" alt="Tela de Cadastro" width="45%">
  <br>
  <img src="docs/images/password_reset.png" alt="Recuperação de Senha" width="45%">
  <img src="docs/images/password_reset_code.png" alt="Código de Recuperação" width="45%">
</div>

## Arquitetura de Dados (Mapeamento Inicial)
Para sustentar o ecossistema forense, teremos no mínimo 4 entidades relacionais base:
1.  **Tabela de Usuários:** Autenticação, perfis e permissões dos peritos.
2.  **Tabela de Projetos_Periciais:** Agrupamento das investigações ativas, dados do alvo analisado.
3.  **Tabela de Logs:** Registro e trilhas de auditoria das ferramentas monitoradas.
4.  **Tabela de Relatórios:** Histórico de documentação gerada pelo sistema.

## Como Iniciar (Getting Started)

*-Instruções a serem preenchidas após a finalização da infraestrutura base*

```bash
# Clone o repositório
git clone https://github.com/SeuUsuario/Project_Nexo.git

# Acesso ao diretório
cd Project_Nexo

# Instalação das dependências e execução do backend/frontend...
```

---
*Este arquivo README foi estruturado com base nas práticas modernas de documentação e análise de requisitos.*
