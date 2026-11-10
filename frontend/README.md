# Nexo - Front-End

Interface web do **Projeto Nexo**, construída com foco em alta performance, reatividade e experiência do usuário (UI/UX).

## 🚀 Tecnologias Utilizadas

- **Framework:** React 19 + TypeScript
- **Roteamento:** TanStack Router / TanStack Start (roteamento baseado em arquivos em `src/routes/`)
- **Estilização:** Tailwind CSS v4 + tw-animate-css
- **Componentes de UI:** Radix UI primitives + Lucide Icons + Recharts + Sonner
- **Formulários e Validação:** React Hook Form + Zod
- **Build & Dev:** Vite
- **Testes:** Vitest + Testing Library

---

## 📁 Estrutura de Diretórios

```
frontend/
├── public/                # Arquivos estáticos (favicons, imagens, logos, robots.txt)
│   └── imagens/           # Logos da aplicação
├── src/
│   ├── assets/            # Assets e metadados de imagem
│   ├── components/        # Componentes compartilhados
│   │   ├── ui/            # Primitivas shadcn/radix (botões, modais, inputs, tabelas...)
│   │   ├── AppLayout.tsx  # Layout autenticado das telas internas
│   │   ├── NexoLayout.tsx # Layout padrão das telas de autenticação
│   │   └── ...
│   ├── hooks/             # Custom hooks (ex: useTransactions, useMobile)
│   ├── lib/               # Regras de negócio, adaptadores e utilitários
│   │   ├── transactions.ts      # Camada de transações financeiras
│   │   ├── profile.ts           # Gerenciamento de perfil
│   │   ├── preferences.ts       # Preferências do usuário (moeda, tema...)
│   │   └── ...
│   ├── routes/            # Rotas da aplicação (TanStack Router)
│   │   ├── __root.tsx           # Shell e layout raiz
│   │   ├── index.tsx            # Login (/)
│   │   ├── cadastro.tsx         # Cadastro (/cadastro)
│   │   ├── dashboard.tsx        # Dashboard de métricas (/dashboard)
│   │   ├── lancamentos.tsx      # Lançamentos e extrato (/lancamentos)
│   │   ├── perfil.tsx           # Perfil e configurações (/perfil)
│   │   └── redefinir-senha.tsx  # Recuperação de senha (/redefinir-senha)
│   ├── test/              # Testes unitários e de integração
│   ├── start.ts           # Inicialização TanStack Start
│   ├── server.ts          # Configuração SSR
│   ├── router.tsx         # Instância do roteador
│   └── styles.css         # Estilos globais e tokens semânticos
├── .env.example           # Variáveis de ambiente de exemplo
├── package.json           # Dependências e scripts
├── tsconfig.json          # Configuração do TypeScript
├── vite.config.ts         # Configuração do Vite
└── vitest.config.ts       # Configuração do Vitest
```

---

## 🛠️ Como Executar

### 1. Pré-requisitos
- Node.js 18+ (recomendado Node.js 20+)
- npm ou bun

### 2. Instalação das dependências
```bash
npm install
```

### 3. Rodar em ambiente de desenvolvimento
```bash
npm run dev
```
Acesse em: `http://localhost:5173` ou `http://localhost:3000` conforme indicado no terminal.

### 4. Rodar a suíte de testes
```bash
npm test
```

### 5. Gerar build de produção
```bash
npm run build
```

### 6. Pré-visualizar o build localmente
```bash
npm run preview
```
