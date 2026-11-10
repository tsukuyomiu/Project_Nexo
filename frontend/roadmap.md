# Roadmap — Telas internas do Nexo

- [x] Analisar projeto existente e referências do Figma
- [x] Camada de dados única (transactions.ts + useTransactions, localStorage temporário)
- [x] Tokens semânticos verde/vermelho em styles.css (apenas adição)
- [x] AppLayout (cabeçalho interno: Dashboard, Lançamentos, Perfil, Sair)
- [x] Componentes: SummaryCards, TransactionTable, TransactionModal (único)
- [x] Rota /dashboard (resumo, gráfico de pizza, últimos lançamentos)
- [x] Rota /lancamentos (filtros, lista, editar/excluir com confirmação)
- [x] Rota /perfil (dados, resumo, segurança com regra de honestidade da senha)
- [x] Login leva ao Dashboard após entrar (ajuste pontual em index.tsx)
- [x] Testes das regras de cálculo/ordenação/formatação + verificação build
- [x] Verificação end-to-end no navegador (fluxos principais)

## Refinamentos solicitados
- [x] Análise e relatório prévio de limitações
- [x] Obrigatórios acessíveis em Cadastro e modal
- [x] Remover novos seeds sem apagar registros salvos; aguardar carregamento
- [x] Tooltip externo e acabamento com movimento reduzido
- [x] Remover CPF, endereço inicial e notificações
- [x] Testes e relatório de verificação (RELATORIO-MELHORIAS.md)
- [ ] Persistência definitiva e e-mail verificado por conta — bloqueados: integração real de contas adiada pelo usuário

## Finalização Front-End
- [x] Perfil editável em memória, sem dados pessoais no armazenamento local
- [x] Moeda local provisória e formatador único em todas as telas
- [x] Estado vazio Dashboard/Lançamentos e preservação de registros
- [x] Revisão de autocomplete sem desativar o preenchimento legítimo
- [x] Testes, verificação visual e relatório final (RELATORIO-FINALIZACAO.md)

## Correção de início vazio
- [x] Reproduzir herança do armazenamento legado e analisar fontes
- [x] Separar armazenamento por identificação local, preservando legado
- [x] Integrar entrada, cadastro e saída sem senhas persistidas
- [x] Testar início vazio, receita, despesa, exclusão, recarga e reentrada
- [x] Documentar limites de autenticação e registros antigos (RELATORIO-INICIO-VAZIO.md)
