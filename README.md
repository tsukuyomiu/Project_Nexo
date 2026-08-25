<div id="topo"></div>

<div align="center">
  <img src="docs/images/nexo_banner.jpg" alt="Projeto Nexo Banner">
</div>

<br>

<div align="center">
  <a href="https://github.com/seu-usuario/projeto-nexo">
    <img src="https://img.shields.io/badge/Language-Python%20%7C%20Vue.js-3776AB?style=flat-square&logo=python&logoColor=white" alt="Language">
  </a>
  <a href="https://github.com/seu-usuario/projeto-nexo">
    <img src="https://img.shields.io/badge/OS-Windows%20%7C%20Linux%20%7C%20macOS-0078D6?style=flat-square&logo=windows&logoColor=white" alt="OS">
  </a>
  <a href="https://github.com/seu-usuario/projeto-nexo">
    <img src="https://img.shields.io/badge/License-MIT-00599C?style=flat-square&logo=opensourceinitiative&logoColor=white" alt="License">
  </a>
  <a href="https://github.com/seu-usuario/projeto-nexo">
    <img src="https://img.shields.io/badge/PRs-Welcome-brightgreen?style=flat-square&logo=github&logoColor=white" alt="PRs Welcome">
  </a>
  <a href="https://github.com/seu-usuario/projeto-nexo">
    <img src="https://img.shields.io/badge/Status-Em%20Desenvolvimento-FFB000?style=flat-square&logo=git&logoColor=white" alt="Status">
  </a>
  <a href="https://github.com/seu-usuario/projeto-nexo">
    <img src="https://img.shields.io/badge/Build-Passing-success?style=flat-square&logo=githubactions&logoColor=white" alt="Build">
  </a>
  <a href="https://github.com/seu-usuario/projeto-nexo">
    <img src="https://img.shields.io/badge/Docs-Swagger%20UI-85EA2D?style=flat-square&logo=swagger&logoColor=black" alt="Docs">
  </a>
</div>

<br>

<div align="center">
  <img src="https://img.shields.io/badge/Vue.js-35495E?style=for-the-badge&logo=vue.js&logoColor=4FC08D" alt="Vue.js">
  <img src="https://img.shields.io/badge/Vite-B73BFE?style=for-the-badge&logo=vite&logoColor=FFD62E" alt="Vite">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite">
  <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL">
</div>

<div align="center">
  <br>
  <b>Apoie nosso projeto compartilhando:</b><br>
  <br>
  <a href="https://twitter.com/intent/tweet?text=Confira%20o%20Projeto%20Nexo&url=https://github.com/seu-usuario/projeto-nexo">
    <img src="https://img.shields.io/badge/Compartilhar-000000?style=flat-square&logo=x&logoColor=white" alt="Compartilhar no X">
  </a>
  <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/seu-usuario/projeto-nexo">
    <img src="https://img.shields.io/badge/Compartilhar-0077B5?style=flat-square&logo=linkedin&logoColor=white" alt="Compartilhar no LinkedIn">
  </a>
  <a href="https://www.facebook.com/sharer/sharer.php?u=https://github.com/seu-usuario/projeto-nexo">
    <img src="https://img.shields.io/badge/Compartilhar-1877F2?style=flat-square&logo=facebook&logoColor=white" alt="Compartilhar no Facebook">
  </a>
  <a href="https://reddit.com/submit?url=https://github.com/seu-usuario/projeto-nexo&title=Projeto%20Nexo">
    <img src="https://img.shields.io/badge/Compartilhar-FF4500?style=flat-square&logo=reddit&logoColor=white" alt="Compartilhar no Reddit">
  </a>
  <a href="https://t.me/share/url?url=https://github.com/seu-usuario/projeto-nexo&text=Confira%20o%20Projeto%20Nexo">
    <img src="https://img.shields.io/badge/Compartilhar-26A5E4?style=flat-square&logo=telegram&logoColor=white" alt="Compartilhar no Telegram">
  </a>
</div>

<br>

<details>
  <summary>Tabela de Conteudos</summary>
  <ul>
    <li><a href="#visao-geral">Visão Geral</a></li>
    <li><a href="#telas-do-projeto">Telas do Projeto</a></li>
    <li><a href="#tecnologias-e-arquitetura">Tecnologias e Arquitetura</a></li>
    <li><a href="#equipe">Equipe</a></li>
    <li><a href="#como-rodar">Como Rodar</a></li>
  </ul>
</details>

---

<h2 id="visao-geral">Visão Geral</h2>

O Projeto Nexo é um sistema voltado para a área de Perícia Computacional. O foco principal é aliar alta performance com simplicidade acadêmica, fornecendo uma plataforma robusta para a análise e a emissão de relatórios forenses. O sistema visa facilitar o trabalho de peritos e investigadores, oferecendo ferramentas ágeis para visualização de logs, métricas e consolidação de dados de forma intuitiva e eficiente.

> [!IMPORTANT]
> A modelagem inicial do banco prevê quatro tabelas centrais: Usuários, Logs, Projetos_Periciais e Relatórios.

<p align="right"><a href="#topo">voltar ao topo</a></p>

---

<h2 id="telas-do-projeto">Telas do Projeto</h2>

<div align="center">
  <img src="docs/images/signup.png" alt="Cadastro Faça parte da Nexus" width="400">
  <img src="docs/images/login.png" alt="Login" width="400">
  <img src="docs/images/password_reset.png" alt="Recuperação de Senha" width="400">
  <img src="docs/images/password_reset_code.png" alt="Código de Segurança" width="400">
</div>

<br>

O sistema consistirá em pelo menos quatro telas obrigatórias:

1. **Autenticação:** Cadastro "Faça parte da Nexus", Login, Recuperação de Senha com E-mail e Inserção de Código de Segurança.
2. **Dashboard:** Tela de Métricas Forenses.
3. **Logs:** Terminal e Grid de Logs em tempo real.
4. **Relatório:** Tela de Relatório Final.

<p align="right"><a href="#topo">voltar ao topo</a></p>

---

<h2 id="tecnologias-e-arquitetura">Tecnologias e Arquitetura</h2>

A escolha da stack tecnológica foi baseada na necessidade de desempenho, segurança e facilidade de manutenção para o ecossistema pericial:

* **Frontend:** Vue.js 3 com Vite. Garantem uma interface reativa, construção rápida e excelente experiência de usuário para as visualizações de dados.
* **Backend:** Python com FastAPI. O FastAPI oferece alta performance e documentação nativa via Swagger, ideal para agilizar o desenvolvimento e o teste das rotas da API.
* **Banco de Dados:** SQL. A flexibilidade permite o uso de SQLite para ambientes de desenvolvimento e PostgreSQL para produção.

<p align="right"><a href="#topo">voltar ao topo</a></p>

---

<h2 id="equipe">Equipe</h2>

A equipe responsável pelo desenvolvimento e documentação do Projeto Nexo é composta por:

| Nome | Matrícula | Função |
|---|---|---|
| Luann Thayller | 0023194 | Gerente de Projeto, Desenvolvedor Front-End e UI/UX Designer |
| Gabriel Nonato | 0020241 | Desenvolvedor FullStack |
| Weney Anjos da Silva | 0023218 | Desenvolvedor Back-End e Data Engineer |
| Luísa Damaceno | 0016112 | Analista de Requisitos |
| Gabryel Henrique | 0022470 | Assistente Administrativo |
| Érica Beatriz de A. | 0022515 | Analista de Requisitos e UI/UX Designer |

<p align="right"><a href="#topo">voltar ao topo</a></p>

---

<h2 id="como-rodar">Como Rodar</h2>

Siga os passos abaixo para configurar e executar o projeto em seu ambiente local:

```bash
# Abra o terminal

# Clone o repositorio
git clone https://github.com/seu-usuario/projeto-nexo.git

# Navegue ate a pasta do projeto
cd projeto-nexo

# Instale as dependencias do backend
comando_de_instalacao_backend_aqui

# Instale as dependencias do frontend
comando_de_instalacao_frontend_aqui

# Inicie o servidor do backend
comando_para_iniciar_backend_aqui

# Inicie o servidor do frontend
comando_para_iniciar_frontend_aqui
```

<p align="right"><a href="#topo">voltar ao topo</a></p>
