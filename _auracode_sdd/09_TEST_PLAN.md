# Plano de Testes e Garantias AL3

> **Status:** APROVADO PELO USUÁRIO EM 2026-09-27  
> **Objetivo:** provar comportamentos e limites; quantidade de testes ou cobertura isolada não é selo de qualidade.

## 1. Estratégia

- Testes de domínio rápidos para invariantes.
- Testes de contrato para CLI, API, skills, OpenAPI, i18n e provedores.
- Testes de integração com SQLite, Git, PostgreSQL, e-mail local, Docker e Kubernetes de teste.
- Jornadas ponta a ponta do Studio e da aplicação de validação.
- Testes adversariais de autorização, injeção, segredo e conteúdo externo.
- Testes de recuperação, atualização e rollback em ambiente descartável.
- Testes de mutação para comprovar que a suíte detecta defeitos reais.

O agente que implementa não pode enfraquecer testes protegidos para obter aprovação. Mudança necessária de requisito primeiro altera a planta e recebe nova aprovação.

## 2. Gates do Aura Code

| Gate | Evidência mínima | Bloqueia release? |
|---|---|:---:|
| Instalação | pacote limpo em Windows e Linux + `doctor` completo | Sim |
| Skills | manifesto, arquivos, versão, permissão e testes de compatibilidade | Sim |
| Entrevista | dúvida obrigatória impede clareza/aprovação | Sim |
| Rastreabilidade | decisão → requisito → código → teste → evidência | Sim |
| Auditoria honesta | alvo vazio/inexistente/incompatível nunca passa | Sim |
| Linguagens | analisador real ou estado não executado; sem regex vendida como AST | Sim |
| Segurança | suíte adversarial e zero achado crítico aberto | Sim |
| Privacidade | canários não aparecem em prompts, logs ou suporte | Sim |
| Atualização | assinatura, backup, migração e retorno testados | Sim |
| Publicação | artefato assinado, SBOM, rollout e rollback | Sim |
| Documentação | toda promessa possui prova vigente | Sim |
| Artefatos gerados | origem, comando, entradas, hashes, auditoria e reprodução limpa; nenhuma edição manual | Sim |
| Autovalidação | SaaS reproduzido pelo fluxo público em workspace limpo, sem intervenção corretiva externa | Sim |

## 3. Matriz da aplicação de validação

| ID | Cenário | Resultado esperado |
|---|---|---|
| APP-T01 | Usuário de empresa A pede tarefa de B por ID | Negado sem revelar dados |
| APP-T02 | Cada papel tenta cada ação da matriz | Somente permissões autorizadas passam |
| APP-T03 | Convite válido/expirado/revogado/reutilizado/e-mail diferente | Apenas o válido e correspondente cria vínculo |
| APP-T04 | Duas edições da mesma versão | Uma grava; outra recebe conflito sem perder dados |
| APP-T05 | Fluxo completo de tarefa e retorno de etapa | Estados e histórico corretos |
| APP-T06 | Lixeira antes/depois de 30 dias | Restaura antes; purga depois |
| APP-T07 | Menção a participante e não participante | Notifica apenas participante autorizado |
| APP-T08 | Prazo em 24h, atraso e repetição | Notificação correta e agrupada |
| APP-T09 | Recuperação, expiração e reutilização | Link único por 30 minutos |
| APP-T10 | MFA e código de recuperação | TOTP válido entra; código usado não repete |
| APP-T11 | Sessão inativa, confiável, revogada e ação sensível | Política 12h/30d e nova confirmação respeitadas |
| APP-T12 | Exportação e exclusão | Escopo correto, desativação imediata e retenções cumpridas |
| APP-T13 | Falha/repetição do trabalhador | Efeito idempotente e novas tentativas visíveis |
| APP-T14 | Migração com versão antiga ainda ativa | Compatibilidade durante rollout |
| APP-T15 | Restauração de backup | Perda ≤15 min e retorno ≤1h em exercício controlado |

## 4. Auditoria por capacidade

Cada adaptador de linguagem declara exatamente quais regras entende e com qual método. Uma regra sem analisador válido recebe `NOT_RUN`, não aprovação. Python usa AST nativa onde aplicável. TypeScript/JavaScript, Java, Go e C# só serão anunciados quando analisadores estruturais e corpus de falsos positivos/negativos passarem seus contratos.

## 5. Clareza e acessibilidade

- A cada versão principal: 5 pessoas leigas por idioma executam instalação, entrevista, revisão, construção, leitura de falha e preparação de release sem facilitador técnico.
- Meta inicial: pelo menos 80% concluem o percurso definido.
- Bloqueios observados viram achados rastreáveis; falha da meta impede alegação de “comprovadamente claro”.
- Testes automáticos de WCAG 2.2 AA são complementados por teclado, leitor de tela, zoom, alto contraste e movimento reduzido.

## 6. Desempenho e disponibilidade

- Ensaios medem taxa de erro, latência e saturação; valores operacionais de alerta estão no caderno 11.
- Teste de carga usa dados sintéticos e inclui busca, quadro de tarefas, comentários e notificações.
- Meta de disponibilidade é 99,9%; relatório mensal distingue indisponibilidade do produto e dependências externas.

## 7. Evidência de teste

Todo resultado guarda comando, ambiente, versões, horário, escopo, saída normalizada, hash e vínculo com requisito. Resultado antigo ou executado sobre fonte diferente é marcado como obsoleto.

## 8. Protocolo de prova pelo SaaS

| ID | Ensaio | Condição de aprovação |
|---|---|---|
| DOG-001 | Construir o SaaS desde workspace vazio | Todos os arquivos e configurações surgem pelo percurso público do Aura Code |
| DOG-002 | Introduzir falha conhecida em cada etapa | Aura Code detecta e bloqueia; não segue adiante nem declara sucesso |
| DOG-003 | Encontrar defeito real do framework | Reprodução mínima, teste que falha, correção e teste que passa antes de retomar o SaaS |
| DOG-004 | Tentar conserto manual fora do percurso | Evidência é rejeitada e workspace não pode ser certificado |
| DOG-005 | Repetir construção após correção | Workspace limpo chega ao mesmo resultado verificável sem atalho |
| DOG-006 | Publicar a aplicação final | Proveniência demonstra que fonte, testes, build e release passaram pelo Aura Code corrigido |

Uma execução com intervenção manual pode ajudar no diagnóstico, mas é contaminada e nunca conta como validação, benchmark ou demonstração pública.
