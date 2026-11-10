# Nexo — relatório de melhorias

## Implementado
- Cadastro: rótulos visíveis com asteriscos nos quatro campos e no aceite já exigido, erros associados, destaque visual, foco no primeiro erro, espaços tratados como vazio e limpeza do erro quando corrigido. Mensagens específicas anteriores preservadas.
- Modal de receita/despesa: asteriscos para descrição, valor, data e categoria; acessibilidade e destaque dos erros; foco no primeiro erro; valores e erros reiniciados ao reabrir. Mantidas operações, cálculos e parsing brasileiro.
- Dashboard: removida a criação de exemplos na origem; início vazio, resumo zerado, gráfico e recentes vazios, link discreto para primeiro lançamento e espera pelo carregamento. Nenhum registro salvo foi apagado.
- Gráfico: tooltip fixo acima das fatias, categoria e valor, sem interceptar o cursor; cores e dimensões da pizza preservadas. Corrigida a largura das seções do Dashboard no celular para manter a tabela com rolagem interna.
- Perfil: CPF, endereço da apresentação inicial e notificações removidos. Endereço ilustrativo continua definido, sem exclusão de dados.
- Movimento: entrada de formulários e cards, atualização de valores, apenas nova linha por marcador transitório e animação nativa da pizza; duração de 220 ms, sem retardar dados. Dialog existente reaproveitado. Movimento reduzido desativa os novos efeitos e a animação do gráfico.

## Arquivos criados
- `src/components/FieldLabel.tsx`: padrão reutilizável de label obrigatório.
- `src/lib/signup-validation.ts`: regras existentes de cadastro isoladas para testes, com obrigatoriedade anterior às regras específicas.
- `src/test/refinements.test.ts`: 12 testes novos de obrigatoriedade e preservação do armazenamento.
- `RELATORIO-MELHORIAS.md`: este relatório.

## Arquivos existentes alterados
- `src/components/NexoLayout.tsx`: prop opcional `required` e associação dos erros no IconField; padrão antigo mantido sem a prop.
- `src/routes/cadastro.tsx`: obrigatório, foco, correção dos erros, entrada suave e metadados sociais.
- `src/components/TransactionModal.tsx`: labels e erros acessíveis, foco e Button existente nas ações.
- `src/lib/transactions.ts`: remoção exclusiva da geração inicial de seeds; leitura dos registros existentes e cálculos preservados.
- `src/hooks/useTransactions.tsx`: disponibiliza estado de carregamento e identificador transitório da nova linha, mantendo o provider atual.
- `src/components/TransactionTable.tsx`: anima somente a linha recém-adicionada.
- `src/components/SummaryCards.tsx`: entrada e atualização visual suave, sem alteração de cálculo.
- `src/routes/dashboard.tsx`: espera do carregamento, link inicial, posicionamento do tooltip, tokens das cores anteriores e suporte a movimento reduzido.
- `src/routes/lancamentos.tsx`: espera do carregamento e metadados sociais.
- `src/routes/perfil.tsx`: remoções de apresentação solicitadas e metadados sociais.
- `src/routes/index.tsx`: entrada suave do formulário e metadados sociais; fluxo de login preservado.
- `src/routes/redefinir-senha.tsx`: somente metadados sociais; fluxo preservado.
- `src/styles.css`: tokens das cores já usadas pelo gráfico e duração/easing únicos; classes de refinamento e estados de erro.
- `AGENTS.md`: decisões estruturais dos campos e estado visual compartilhado.
- `roadmap.md`: itens concluídos e bloqueados.

Não foram alterados `__root.tsx`, `lib/lovable-error-reporting.ts`, configuração, dependências, lockfiles, autenticação, banco ou infraestrutura. A única mudança funcional na origem dos dados foi interromper a geração de novos exemplos. Registro, edição, exclusão, ordenação, formato dos registros e cálculos foram preservados.

## Reutilização
IconField, Dialog, Select, Button, TransactionsProvider, SummaryCards, TransactionTable, formatBRL, parseBRValue, calcTotals, expensesByCategory, Recharts, tokens existentes e tw-animate-css. Nenhuma biblioteca instalada.

## Verificação executada
**Verificado:** 21 testes aprovados (12 novos + 9 existentes) via Vitest: cálculos, percentuais, ordenação, parsing, formatação, rota inicial, obrigatórios, validações específicas e conservação literal dos registros salvos.

**Verificado no navegador:** cadastro vazio bloqueado, confirmação vazia marcada, cinco controles obrigatórios, foco inicial e limpeza do erro de nome; login de demonstração até Dashboard; Dashboard vazio e link até Lançamentos; bloqueio de despesa incompleta; criação de despesa de 123,45, leitura na tabela, permanência após recarregar e reset do modal; removidos CPF/endereço inicial/notificações; tooltip visível com Alimentação e R$ 123,45 acima do gráfico. Desktop 1280×1800 e celular 390×844; Dashboard sem transbordamento horizontal após ajuste. Movimento reduzido resulta em `animation-name: none`. Nenhum erro de página nesses fluxos.

**Compilação verificada:** último resultado do verificador automático do projeto: `build OK`. Não foi executado um build manual.

**Não verificado:** cadastro e recuperação efetivos, alteração de senha/e-mail e envio real de mensagens, pois não existe serviço de autenticação. Fluxo completo de cadastro válido e recuperação não foi repetido nesta rodada. Edição e exclusão pela interface não foram repetidas nesta rodada; seus cálculos e conservação do armazenamento foram testados. Não foi feita auditoria de registros do navegador do usuário. Animações de modais foram reaproveitadas, não submetidas a medição visual quadro a quadro.

## Limitações e pendências
- Não existe conta autenticada, identificador de usuário, perfil persistente ou envio real de e-mails. Login, cadastro e recuperação atuais são demonstrações de interface, não serviços reais. Foram preservados conforme solicitado; nenhum novo sucesso fictício foi implementado.
- Lançamentos usam `nexo:transactions`, chave única temporária no navegador, sem separação por usuário ou sincronização entre dispositivos. Isso impede cumprir “somente dados do usuário” entre contas sem mudar a arquitetura de armazenamento.
- Moeda e marcador de boas-vindas **não foram armazenados nem implementados**: não há identificador autenticado para isolar preferências. Não foi criada uma preferência global que afetasse outras contas nem uma identidade fictícia baseada no e-mail digitado.
- Edição persistente de nome/endereço e e-mail verificado aguardam orientação sobre infraestrutura real de contas e perfil; o botão Editar mantém o aviso existente. Sem modal de edição fictício.
- Boas-vindas por conta da referência anexada ficam pendentes até existir o mecanismo individual de preferências; o link discreto de primeiro lançamento não grava conclusão de introdução.
- Versões anteriores gravavam oito exemplos (Internet, Pix - Cliente, Frete, Supermercado, Venda de produto, Aluguel, Salário, Academia). Registros salvos podem conter esses exemplos, mas não há marca que permita distingui-los com segurança de registros reais. Nenhuma limpeza automática foi feita. A remoção só deve ocorrer após identificar e autorizar registros específicos, preferencialmente pela exclusão normal na tela.
- Para concluir os itens bloqueados, é necessária orientação para habilitar contas reais e uma fonte persistente de perfil/preferências, com confirmação real de e-mail; nenhuma alteração dessa infraestrutura foi realizada.