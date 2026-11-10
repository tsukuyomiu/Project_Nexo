# Correção do início vazio — Nexo

## Origem reproduzida
Não havia geração ativa de novos exemplos: ela já tinha sido removida. O problema restante era a chave única `nexo:transactions`, lida em qualquer entrada, sem identificação do usuário. Exemplos gravados em versões anteriores e registros de outra entrada no mesmo navegador eram herdados por novos acessos.

Antes da correção, foi gravado um registro legado de teste e realizada entrada com uma identificação nova: o Dashboard mostrou uma linha antiga. Depois da correção, o mesmo cenário iniciou vazio.

## Alterações
- `src/lib/local-identity.ts` (novo): valida e normaliza o e-mail, deriva um identificador local com SHA-256 e mantém apenas o identificador ativo em sessionStorage. Não armazena senha ou e-mail em texto puro.
- `src/lib/transactions.ts`: adaptadores recebem escopo explícito no app. Cada identificação lê/grava uma chave distinta; sem identificação não lê o legado. Nenhum fallback demonstrativo ou cópia automática de dados antigos.
- `src/hooks/useTransactions.tsx`: restaura o espaço ativo na recarga, troca a coleção ao entrar e limpa somente o estado da sessão ao sair. Registros persistidos permanecem no seu espaço local.
- `src/routes/index.tsx`: aguarda a abertura do espaço local antes de navegar, impede duplo envio e informa o resultado sem alegar autenticação real.
- `src/routes/cadastro.tsx`: validação existente preservada; um cadastro encerra a identificação anterior, sem apagar seus registros ou copiar movimentações.
- `src/components/AppLayout.tsx`: Sair encerra a identificação local, preservando seus lançamentos.
- `src/test/local-transactions.test.ts` (novo): sete testes de vazio, isolamento, legado, persistência, exclusão, validação e identificação.
- `AGENTS.md` e `roadmap.md`: decisões e conclusão documentadas.

Dashboard, gráfico, tabelas, filtros, formulários de lançamentos, cálculos, cores e layout não foram reconstruídos. Nenhuma dependência, configuração ou integração de Back-End foi adicionada.

## Verificações executadas
**47 testes aprovados:** sete novos e 40 existentes, com testes de cálculos e conservação de armazenamento mantidos.

**Navegador, 1280×1800, fluxo completo:**
1. Cadastro de interface novo seguido de entrada: Dashboard com três valores R$ 0,00, sem linhas herdadas e com estado vazio.
2. Lançamentos vazio.
3. Recarga continua vazia.
4. Receita de 500 cadastrada pela interface: somente registro próprio exibido.
5. Despesa de 125 cadastrada: entrada 500, saída 125, saldo 375 e gráfico de despesa real.
6. Exclusão dos dois registros pela interface: Dashboard volta a vazio e permanece assim após recarga.
7. Saída e reentrada antes da exclusão: ambos os registros próprios reaparecem.

Também foi testada uma segunda identificação no mesmo navegador: começou vazia e não recebeu os registros da primeira. Retornar à primeira restaurou seus registros. O valor legado de teste foi comparado literalmente antes/depois, sem alterações. Nenhum erro de página foi registrado. Captura do Dashboard vazio inspecionada.

**Compilação:** verificador automático do projeto indicou `build OK`; não foi executado build manual.

## Limitações e conservação dos registros antigos
- Esta solução separa espaços locais por e-mail digitado; **não é autenticação, conta real ou garantia de acesso exclusivo**. Conhecer o mesmo e-mail abre o mesmo espaço neste navegador; o hash não é uma proteção de acesso. Segurança real por usuário e sincronização exigem Back-End, fora do escopo solicitado.
- A chave antiga `nexo:transactions` permanece intacta, mas não é carregada automaticamente por nenhuma identificação nova. Seus registros podem incluir exemplos e dados legítimos, sem marca de origem ou proprietário. Não é seguro atribuí-los a uma conta ou apagá-los automaticamente.
- Registros legítimos anteriores continuam preservados no armazenamento antigo, porém não aparecem no novo espaço até uma recuperação/atribuição explícita dos registros escolhidos e do destinatário. Essa recuperação não foi implementada sem identificação do proprietário.
- Persistência local atual: registros criados nos novos espaços sobrevivem à recarga e à saída/reentrada com o mesmo e-mail no mesmo navegador. Não sincronizam entre dispositivos. O cadastro continua sendo um formulário de interface, não cria conta no servidor.
- Preferência de moeda continua provisória por navegador e perfil continua temporário em memória, sem alterações nesta correção.