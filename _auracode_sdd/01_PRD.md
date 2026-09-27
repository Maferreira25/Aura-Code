# Especificação de Requisitos do Produto — Aura Code Profissional

> **Status:** APROVADO PELO USUÁRIO EM 2026-09-27  
> **Versão da planta:** 1.0.0  
> **Nível de garantia:** AL3 — uso comercial  
> **Data da consolidação:** 2026-09-27

## 1. Visão do produto

O Aura Code será um construtor assistido por IA que conduz uma pessoa sem experiência em programação desde a explicação da ideia até uma aplicação publicável, sem depender de Cursor, Antigravity ou VS Code. A experiência principal será o **Aura Studio**, aberto no navegador local pela CLI. O terminal continuará disponível para automação e para usuários técnicos.

O produto não promete que a IA substitui responsabilidade humana, aconselhamento jurídico ou especialistas de sistemas regulados. Ele entrega um percurso completo e comprovável para uma pilha certificada; outras tecnologias serão extensões experimentais até passarem pela mesma certificação.

## 2. Dois entregáveis separados

### 2.1 Núcleo Aura Code

É o construtor: entrevista sem jargões, registro de decisões, planta teórica, construção, auditoria, provas, prévia e publicação. Inclui CLI, Aura Studio, skills, verificadores, proteção ativa e empacotamento.

### 2.2 Aplicação oficial de validação

É um SaaS de gerenciamento de projetos para pequenas equipes. Funciona como o “prédio-modelo” que comprova o construtor de ponta a ponta. Não é dependência do núcleo, não define a marca dos aplicativos gerados e não implica que o Aura Code constrói apenas gerenciadores de projetos.

## 3. Público e responsabilidades

| Pessoa | Necessidade | Responsabilidade |
|---|---|---|
| Construtor leigo | Criar software por uma jornada explicada | Decidir regras de negócio e aprovar ações sensíveis |
| Responsável pela publicação | Entender riscos e provas | Dar a autorização final de produção |
| Engenheiro/auditor | Inspecionar detalhes e estender o sistema | Revisar evidências, integrações e exceções |
| Especialista de domínio regulado | Validar regras externas ao framework | Aprovar requisitos jurídicos, médicos, financeiros ou equivalentes |

## 4. Jornada funcional do Aura Studio

1. Criar ou abrir um projeto.
2. Entrevistar o usuário em português ou inglês, com comparações cotidianas.
3. Registrar decisões, dúvidas, mudanças e autorizações.
4. Montar e revisar os 15 cadernos da planta.
5. Construir em etapas pequenas e reversíveis.
6. Mostrar o que mudou e quais testes sustentam a mudança.
7. Auditar por garantia, sem nota geral enganosa.
8. Executar a aplicação em prévia local.
9. Preparar a publicação gradual.
10. Exigir aprovação humana identificada e guardar a prova da publicação.

Telas obrigatórias: Projetos, Entrevista, Decisões, Planta, Construção, Auditoria e Evidências, Prévia e Publicação.

## 5. Escopo funcional confirmado

| ID | Recurso | Comportamento obrigatório |
|---|---|---|
| AC-F01 | Entrevista adaptativa | Não declara clareza enquanto existirem decisões obrigatórias sem resposta |
| AC-F02 | Planta versionada | Produz 15 cadernos enterprise e mantém ligação entre decisão, requisito e teste |
| AC-F03 | Construtor certificado | Gera a pilha FastAPI + Next.js + PostgreSQL + Docker + Kubernetes |
| AC-F04 | Provedor de IA substituível | Núcleo neutro; primeiro adaptador usa protocolo compatível com APIs OpenAI |
| AC-F05 | Auditoria honesta | Estados Aprovado, Reprovado, Não executado e Não aplicável, sempre com prova |
| AC-F06 | Proteção de dados enviados à IA | Prévia do envio, redução ao mínimo, bloqueio de segredos e registro local |
| AC-F07 | Empacotamento completo | CLI, Studio, skills, modelos e verificadores chegam juntos e são conferidos por `auracode doctor` |
| AC-F08 | Operação bilíngue | Português padrão e inglês equivalente, prontos para novos idiomas |
| AC-F09 | Atualização segura | Versão assinada, autorização explícita, backup, migração e retorno à versão anterior |
| AC-F10 | Recuperação | Checkpoints Git e cópias locais versionadas do estado antes de operações importantes |
| AC-F11 | Integrações opcionais | Editores são portas adicionais; nenhum editor é obrigatório |
| AC-F12 | Prova de promessas | Afirmações públicas apontam para evidência reproduzível ou limitação conhecida |
| AC-F13 | Autovalidação sem atalhos | O SaaS de validação só pode ser produzido pelo fluxo real do Aura Code; falha do framework interrompe a prova até ser corrigida e retestada |

## 6. Aplicação oficial de validação

O SaaS permite criar empresas, convidar pessoas, criar e arquivar projetos, manter tarefas no fluxo **A fazer → Em andamento → Em revisão → Concluída**, usar prioridades, responsáveis, prazos e etiquetas, comentar, mencionar pessoas, receber notificações internas e recuperar itens da lixeira durante 30 dias.

Papéis: proprietário, administrador, membro e visitante. Não haverá cobrança, anexos, SMS, aplicativo móvel nativo nem busca em comentários na primeira versão.

O SaaS não será escrito paralelamente à mão para compensar limitações do construtor. Cada arquivo, migração, teste, configuração e artefato necessário deve nascer ou ser alterado por uma função válida do Aura Code, com o mesmo percurso disponível ao usuário final. Quando o percurso revelar uma falha do framework, a construção do SaaS pausa, a falha é reproduzida, o Aura Code é corrigido, recebe teste de regressão e a etapa é repetida em workspace limpo. Somente então o resultado conta como prova.

## 7. Critérios de sucesso autorizados

| Medida | Meta |
|---|---|
| Clareza real | Pelo menos 80% de conclusão do percurso por 5 pessoas leigas em cada idioma, sem ajuda técnica, por versão principal |
| Disponibilidade do SaaS | 99,9% por mês |
| Perda máxima de dados após desastre | 15 minutos |
| Tempo máximo para restaurar o serviço | 1 hora |
| Publicação | Gradual, com verificações de saúde e retorno automático |
| Acessibilidade | WCAG 2.2 AA comprovada |
| Privacidade | Telemetria desativada por padrão; nenhuma fonte, prompt ou segredo em diagnóstico |
| Portabilidade | Desenvolvimento local com Docker e produção Kubernetes independente de nuvem |

## 8. Limites explícitos

- Garantia integral somente para a pilha certificada inicial.
- Windows e Linux no lançamento inicial; macOS depois.
- Instalação local e usuário único no Aura Studio inicial.
- Cobrança, anexos, aplicativos móveis nativos e permissões personalizadas ficam fora da aplicação de validação inicial.
- “Pronto para produção” significa que os critérios AL3 e ambientais foram satisfeitos com provas; não significa certificação legal automática nem adequação universal.
- Nenhuma nota, selo ou texto poderá afirmar “nível sênior”, “seguro” ou “pronto” quando uma verificação necessária estiver ausente.

## 9. Rastreabilidade das 74 decisões

| Decisões | Tema | Escolha aprovada |
|---|---|---|
| D001–D003 | Pilha, interface e garantia | FastAPI/Next.js/PostgreSQL/Docker; Studio + CLI; AL3 |
| D004–D006 | IA, produção e Studio | Núcleo neutro/OpenAI compatível; Kubernetes; local e individual |
| D007–D009 | Uso, privacidade e CI | Navegador local; envio mínimo; GitHub Actions com motor neutro |
| D010–D012 | Estado, segredos e licença | Markdown/JSON/SQLite; cofre do SO; MIT |
| D013–D015 | Sistemas, autonomia e prova | Windows/Linux; autonomia por risco; SaaS de projetos |
| D016–D021 | Acesso e colaboração | Senha/recuperação/2FA; quatro papéis; notificações internas; tarefas; comentários; lixeira de 30 dias |
| D022–D027 | Studio, idiomas e manutenção | Jornada completa; PT/EN; três temas; backup; atualização reversível; diagnóstico opcional |
| D028–D033 | Operação e garantia | RPO/RTO; 99,9%; rollout gradual; isolamento; e-mail substituível; pilha certificada |
| D034–D039 | Independência e auditoria | Editores opcionais; gates; evidência; alvo inválido falha; sem nota geral; exceção controlada |
| D040–D045 | Pacote e governança | Pacote único; skills contratadas; i18n testado; teste com leigos; duas camadas; aprovação humana |
| D046–D051 | Arquitetura e SaaS | Monólito modular; REST/OpenAPI; fila PostgreSQL; permissões; convites; sem cobrança |
| D052–D057 | Privacidade e cadeia | Apoio à LGPD; exclusão; auditoria anual; rede restrita; conteúdo não confiável; cadeia verificável |
| D058–D063 | Operação e dados | Observabilidade aberta; incidentes; migrações seguras; projeto essencial; dados mínimos; busca filtrada |
| D064–D069 | Tarefas e autenticação | Campos essenciais; colaboração; exclusão administrativa; notificações; senha/2FA; sessões controláveis |
| D070–D072 | Experiência visual | Web responsiva; WCAG 2.2 AA; identidades sóbrias separadas |
| D073 | Rigor da autovalidação | Nenhuma falha do Aura Code pode ser ignorada ou contornada; o SaaS final só existe se o framework executar corretamente suas próprias funções |
| D074 | Artefatos determinísticos gerados | O limite de 500 linhas permanece absoluto para código e configuração escritos; lockfiles e saídas compiladas reproduzíveis usam gate separado com origem, comando, hashes, auditoria, proibição de edição manual e reprodução comprovada |
