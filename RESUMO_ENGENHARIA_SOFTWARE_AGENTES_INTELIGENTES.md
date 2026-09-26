# ENGENHARIA DE SOFTWARE COM AGENTES INTELIGENTES
## Guia Definitivo, Resumo Estruturado e Manual Prático de Aplicação

> **Autor da Obra:** Prof. Sandeco Macedo  
> **Ano de Publicação:** 2026  
> **Natureza do Material:** Resumo exaustivo, aprofundado e estruturado capítulo a capítulo, contendo fundamentos teóricos, princípios invariantes, casos reais, arquitetura de software, códigos executáveis e checklists de aplicação prática imediata.  
> **Objetivo:** Capacitar qualquer desenvolvedor, líder técnico, arquiteto ou engenheiro a compreender integralmente os ensinamentos transmitidos no livro e aplicar a engenharia de software na era dos agentes autônomos de IA.

---

## Sumário Geral

1. [Capítulo 1 — A Morte do Vibe Coding](#capítulo-1--a-morte-do-vibe-coding)
2. [Capítulo 2 — O que é software afinal?](#capítulo-2--o-que-é-software-afinal)
3. [Capítulo 3 — Git: o Ctrl+Z que a IA não te dá](#capítulo-3--git-o-ctrlz-que-a-ia-não-te-dá)
4. [Capítulo 4 — Criando de olho na Manutenção](#capítulo-4--criando-de-olho-na-manutenção)
5. [Capítulo 5 — Agent Skills: Criando a sua Matrix](#capítulo-5--agent-skills-criando-a-sua-matrix)
6. [Capítulo 6 — SDD e TDD: a Mentalidade](#capítulo-6--sdd-e-tdd-a-mentalidade)
7. [Capítulo 7 — BMAD, Speckit e Agent Harness: os Frameworks](#capítulo-7--bmad-speckit-e-agent-harness-os-frameworks)
8. [Capítulo 8 — Engenharia de Looping: o piloto automático do seu agente](#capítulo-8--engenharia-de-looping-o-piloto-automático-do-seu-agente)
9. [Capítulo 9 — A Jaula do Agente: DevContainers e o Modo YOLO](#capítulo-9--a-jaula-do-agente-devcontainers-e-o-modo-yolo)
10. [Matriz Geral de Competências e Síntese de Aplicação](#matriz-geral-de-competências-e-síntese-de-aplicação)

---

# Capítulo 1 — A Morte do Vibe Coding

## 1. Contexto Geral e a Tese da Morte do Vibe Coding
O livro abre com uma afirmação provocativa e urgente: o *Vibe Coding* precisa morrer. Essa declaração não significa abandonar o uso de Inteligência Artificial na programação, mas sim sepultar a prática ingênua, caótica e desprovida de método que se disseminou após a explosão das LLMs. 

Em fevereiro de 2025, Andrej Karpathy (ex-diretor de IA da Tesla e cofundador da OpenAI) cunhou o termo **vibe coding** para descrever uma forma de programar onde o desenvolvedor entra em estado de "flow", abre mão do controle minucioso, aceita sugestões do modelo sem ler criticamente e vai acumulando código por intuição e impulso. Embora espetacular para prototipagem rápida e postagens de redes sociais comemorando "SaaS construído em 48 horas", essa abordagem opera sobre uma premissa perigosa e falsa: a ilusão de que **"código que funciona é código correto"**.

O diagnóstico de Sandeco é cirúrgico: a IA não tem culpa de nada; ela apenas executa o que foi solicitado. O colapso decorre da ausência de processo de engenharia. A transição obrigatória é do *Vibe Coding* para a **AI Engineering** — o desenvolvimento onde agentes inteligentes operam sob método rigoroso, requisitos formais, arquitetura modular, testes automatizados e governança humana contínua.

```
       [ VIBE CODING ]                                 [ AI ENGINEERING ]
  Velocidade cega sem freios                     Velocidade alavancada por método
  Acúmulo desordenado de prompts                  Processo estruturado (Requisitos -> Testes)
  Código que apenas "parece" rodar                Código correto, auditável e sustentável
  Débito técnico exponencial                      Custo de mudança linear e previsível
  Colapso na primeira sexta-feira                 Sistemas que duram anos em produção
```

---

## 2. Ideias Centrais e Fundamentos Teóricos

### A Falsa Premissa e o Débito Técnico Exponencial
- **Protótipo disfarçado de produto:** Um script gerado por IA que roda localmente, sem carga, com um único usuário e dados ideais é apenas um rascunho. Produção exige tolerância a falhas, concorrência, segurança, integridade de dados e conformidade legal.
- **A Dinâmica do Custo de Mudança:** No início de um projeto sem processo, a velocidade inicial é alta. Porém, a curva de custo de manutenção e alteração cresce exponencialmente. No projeto com engenharia, há um custo de partida para estruturação (especificações, arquitetura, testes), mas o custo de manutenção permanece linear ao longo do tempo. Após o **ponto de inversão**, qualquer modificação no projeto "vibe" custa ordens de magnitude mais caro do que custaria no projeto disciplinado.
- **A Ausência Crônica de Requisitos:** Sem saber exatamente o que construir, para quem, sob quais restrições de escala e regras tributárias/operacionais, a IA preenche as lacunas com suposições genéricas. O retrabalho subsequente costuma custar três a cinco vezes mais do que a construção original.

### Origem da Engenharia de Software (Garmisch, 1968)
A conferência da OTAN em Garmisch (Alemanha, 1968) reuniu cientistas para enfrentar a histórica **"Crise do Software"** (atrasos crônicos, estouros de orçamento, falhas catastróficas). Ali consagrou-se que criar software é uma disciplina de engenharia, não uma arte mística de inspiração individual:
- **Definição IEEE:** "A aplicação de uma abordagem sistemática, disciplinada e quantificável ao desenvolvimento, operação e manutenção de software."
  - *Sistemática:* Há um método claro.
  - *Disciplinada:* O método é seguido consistentemente, não apenas quando conveniente.
  - *Quantificável:* Métricas permitem medir, auditar e aprimorar.
  - *Ciclo Completo:* Não acaba no deploy; abrange toda a vida útil do sistema.
- **SWEBOK (Software Engineering Body of Knowledge):** A construção de código é apenas uma entre mais de uma dezena de áreas do conhecimento (Requisitos, Design/Arquitetura, Testes, Manutenção, Gerência de Configuração, Qualidade, Governança). Reduzir engenharia a "digitar código" é um equívoco de iniciante.

---

## 3. Ensinamentos e Lições Práticas

### O Que Fazer (Práticas do AI Engineer)
1. **Definir Antes de Gerar:** Estabelecer o que construir, com quais invariantes e para qual contexto antes de submeter o primeiro prompt de implementação.
2. **Tratar IA como Amplificador, Não Substituto:** O agente automatiza o trabalho repetitivo, sugere alternativas e gera stubs; a tomada de decisão sobre limites, regras de negócio e arquitetura permanece 100% sob responsabilidade humana.
3. **Questionar Casos de Borda:** A IA não perguntará proativamente sobre cenários extremos ou condições raras; o engenheiro deve antecipar esses cenários e forçá-los nas especificações e suítes de teste.
4. **Construir com Foco em Manutenção:** Mais de 67% a 80% do esforço de ciclo de vida de um sistema ocorre após o primeiro deploy. O código deve ser legível para humanos e para futuros agentes.

### O Que Evitar (Armadilhas do Vibe Coding)
1. **Confundir Demonstração com Produção:** Celebrar que um SaaS subiu no fim de semana sem testes de segurança, validação de inputs e tratamento de exceções.
2. **Aceitar Código sem Ler e sem Testar:** Injetar sugestões da LLM diretamente na branch principal sem inspeção de segurança e conformidade arquitetural.
3. **Validar Senhas e Credenciais com Comparações Frágeis:** Aceitar implementações ingênuas (como `if password == password`) geradas por autocomplete.
4. **Acúmulo Cego de Prompts:** Criar dependências circulares e acoplamento desordenado através de sessões longas de chat sem documentar decisões.

---

## 4. Princípios de Engenharia e Regras Arquiteturais
- **Princípio da Responsabilidade do Engenheiro:** A IA nunca responde civil, penal ou financeiramente pelo software. O engenheiro que assina a entrega é o único responsável.
- **Equação Fundamental da AI Engineering:**  
  $$	ext{Software Sustentável} = 	ext{Inteligência Artificial} + 	ext{Processo Estruturado de Engenharia}$$
- **Lei da Inversão do Débito Técnico:** Projetos sem processo acumulam juros compostos de dívida técnica a cada prompt aceito às cegas; o ponto de inversão é inevitável e torna o sistema intransponível para manutenção futura.

---

## 5. Casos de Uso Reais e Exemplos Históricos

| Caso Real | Falha Observada | Causa Raiz de Engenharia | Lição para AI Engineering |
| :--- | :--- | :--- | :--- |
| **Foguete Ariane 5 (1996)** | Explosão 37 segundos após o lançamento; perda de US$ 370 milhões. | Overflow de inteiro de 64-bit para 16-bit com sinal; código copiado do Ariane 4 sem reavaliação de requisitos físicos do novo foguete. | Reutilização de código (humana ou gerada por IA) sem validação estrita de contexto e invariantes resulta em catástrofe. |
| **Portal HealthCare.gov (2013)** | Colapso no primeiro dia sob fração da carga prevista; escândalo nacional nos EUA. | Falta de testes de integração ponta a ponta, ausência de planejamento de capacidade e requisitos de integração frágeis. | Sistemas funcionam bem isoladamente no computador do desenvolvedor; sem testes de carga e integração, falham em produção. |
| **Startup de Gestão Financeira (Caso Real do Livro)** | Sistema emitia guias de impostos com alíquotas fixas erradas; custo de correção superou 3x o custo inicial de desenvolvimento. | O sistema foi gerado em 3 semanas via prompts ao ChatGPT. Ninguém levantou requisitos tributários nem escreveu testes para os regimes fiscais. | A Receita Federal não aceita a desculpa "mas a IA gerou assim". Processo e requisitos são obrigatórios. |

---

## 6. Ferramentas, Ambientes e Workflows
- **Ambientes de Desenvolvimento Agentic (Agentic IDEs):** Claude Code (Anthropic) e Google Antigravity. Não são editores com autocompletar simples, mas ambientes com terminais controlados, isolamento de branches, worktrees e capacidade de executar verificações estáticas.
- **Frameworks de Processo para Agentes:** BMAD (Breakthrough Method for Agile AI-Driven Development) e Speckit (GitHub Spec Kit).
- **Camada de Agent Harness:** Conjunto de skills, restrições e hooks que moldam um modelo genérico em um desenvolvedor especialista alinhado às regras do projeto.

---

## 7. Guia de Aplicação Imediata (Como Aplicar na Prática)
1. **Interrompa o Vibe Coding:** Diante de uma nova funcionalidade, não abra o chat da IA pedindo código imediatamente.
2. **Escreva o Briefing Técnico:** Redija em markdown o objetivo do componente, as restrições, o contrato de dados (entradas e saídas) e os critérios de aceitação.
3. **Instrua o Agente com Limites:** Ao utilizar o agente (Claude Code / Antigravity), forneça a especificação e exija que ele produza primeiro os testes unitários ou o plano estrutural.
4. **Audite Antes de Integrar:** Revise cirurgicamente cada diff antes do commit.

---

## 8. Perguntas de Autoavaliação e Fixação
1. Por que a premissa "código que funciona é código correto" é fatal no contexto de desenvolvimento com IA generativa?
2. Explique a conferência da OTAN de 1968 e como sua motivação histórica reflete a atual crise do vibe coding.
3. Descreva a curva do custo de mudança do software ao longo do tempo e defina o que é o "ponto de inversão".
4. Qual é o papel exato do ser humano na equação da *AI Engineering*?

# Capítulo 2 — O que é software afinal?

## 1. Contexto Geral e a Metáfora da Pizza
O capítulo inicia desfazendo a confusão elementar entre **código-fonte** e **software**:
> *Se você pede uma pizza e recebe farinha, molho de tomate crus, queijo e pepperoni soltos dentro de uma caixa, tecnicamente recebeu todos os ingredientes certos. Mas isso não é pizza.*

Linhas de código, funções e classes são apenas os ingredientes brutos. **Software é a solução completa em funcionamento contínuo:** o código executável, a lógica de negócio testada, a interface usável, a persistência confiável dos dados, o tratamento robusto de exceções, a documentação viva e o processo de evolução que garante que o sistema continue operacional e sustentável daqui a três ou cinco anos.

O código possui um atributo traiçoeiro que o hardware não tem: **a invisibilidade**. Um edifício com vício estrutural apresenta rachaduras visíveis na parede; um motor avariado range. O software mal construído parece idêntico ao excelente software na tela de apresentação — até o momento crítico em que entra em colapso na produção sob condições reais.

```
+-------------------------------------------------------------------------+
|                  O SOFTWARE COMO ARTEFATO MULTIDIMENSIONAL              |
+-------------------------------------------------------------------------+
| 1. PRODUTO:     Resolve uma necessidade humana ou de negócio real       |
| 2. PROCESSO:    Construído sob método sistemático, previsível e seguro  |
| 3. SERVIÇO:     Opera em produção com estabilidade, segurança e SLA     |
| 4. COMPROMISSO: Projetado para manutenção e evolução ao longo do tempo  |
+-------------------------------------------------------------------------+
```

---

## 2. Ideias Centrais e Fundamentos Teóricos

### A Crise do Software Recorrente e o Relatório CHAOS
A crise iniciada em 1968 nunca foi eliminada; apenas mudou de escala e velocidade:
- Anos 70: Problemas de custo e estouro de prazo.
- Anos 90: Complexidade arquitetural crescente.
- Anos 2000: Sistemas legados intratáveis.
- Anos 2020: A ilusão de que a IA elimina a necessidade de processo.

O **CHAOS Report (Standish Group, 2020)** analisa milhares de projetos de TI e demonstra que os números mal se moveram em três décadas:
- **31% Bem-sucedidos:** Entregues no prazo, dentro do orçamento e com escopo integral.
- **50% Desafiados:** Entregues com atraso significativo, custos estourados ou corte severo de funcionalidades.
- **19% Cancelados/Fracasso Total:** Descartados antes de qualquer entrega.

### Comparativo de Responsabilidade Profissional
O autor confronta a cultura permissiva do desenvolvimento com indústrias maduras:
- **Aviação Comercial:** Um Boeing 787 possui mais de 8 milhões de linhas de código e milhões de componentes. Opera sob clima hostil e incerto. Sua taxa de acidentes fatais é inferior a **0,2 por milhão de voos**, porque checklists rigorosos e protocolos não são negociáveis.
- **Medicina Cirúrgica:** Cirurgias cardíacas seguem checklists obrigatórios da OMS. Pular a conferência de materiais e sinais vitais não é "ser ágil", é imperícia e negligência punível por lei.
- **Engenharia de Software:** Programadores rotineiramente sobem código sem testes, sem requisitos e sem documentação, tratando o processo como burocracia descartável. A ausência de responsabilização profissional alimenta o ciclo da crise.

### As Atividades Fundamentais do Ciclo de Software
1. **Levantamento de Requisitos:** Descobrir a real necessidade do cliente (que raramente sabe articulá-la na primeira conversa). Requisitos mal levantados não geram bugs; geram sistemas inteiros construídos na direção errada.
2. **Projeto / Design de Software:** Decisões arquiteturais, separação de responsabilidades, contratos de API e modelos de dados que determinarão o custo futuro de qualquer mudança.
3. **Implementação:** Escrita de código. Fase em que os agentes de IA se destacam, mas que apenas amplificam os acertos ou erros das etapas anteriores.
4. **Testes:** Atividade transversal contínua que começa com critérios de aceitação antes do código e segue até pós-deploy.
5. **Deploy (Implantação):** Estratégia incremental, monitorada e reversível, não um evento heroico pontual.
6. **Manutenção:** Consome entre **60% e 80% do orçamento total** do ciclo de vida (Barry Boehm). O software não termina no deploy; ele começa ali.

---

## 3. Os Modelos de Processo

```
MODELOS DE PROCESSO EM PERSPECTIVA:
[ Cascata ] --------------> Linear, estrito, baixa flexibilidade a mudanças tardias
[ Espiral ] --------------> Guiado por gestão de riscos em voltas progressivas
[ Prototipação ] ---------> Validação rápida de hipóteses (risco: protótipo virar produto)
[ RAD ] ------------------> Ciclos ultra rápidos com blocos reutilizáveis
[ Iterativo Incremental ] -> Entregas em partes funcionais acumulativas
[ Baseado em Componentes] -> Engenharia de software por composição e reuso sistemático
[ Ágil (Scrum/XP/Kanban)] -> Ciclos curtos, feedback contínuo, disciplina técnica
```

1. **Cascata (Waterfall - Winston Royce, 1970):** Fases sequenciais rígidas (Requisitos -> Design -> Código -> Teste -> Deploy). O próprio Royce advertiu em seu artigo original que a cascata pura era arriscada e exigia iterações.
2. **Espiral (Barry Boehm, 1988):** Ciclos concêntricos divididos em 4 quadrantes (Objetivos, Análise de Riscos, Engenharia/Construção, Avaliação do Cliente). Ideal para sistemas críticos de alto risco.
3. **Prototipação:** Construção de modelo descartável para elicitar requisitos. O perigo crônico: o cliente gostar do protótipo e a gestão decidir colocá-lo diretamente em produção ("o vibe coding de 1985").
4. **RAD (Rapid Application Development - James Martin, 1991):** Foco em ferramentas CASE, geradores de código e reuso para entregas rápidas (60-90 dias).
5. **Iterativo Incremental:** O sistema é fatiado em entregas funcionais. O incremento 1 cobre o núcleo vital; incrementos subsequentes expandem e refinam a aplicação com base no uso real.
6. **Desenvolvimento Baseado em Componentes (CBSE):** Integração com bibliotecas reutilizáveis comprovadas em vez de reinvenção da roda. É a base dos pacotes modernos (pip, npm) e das *Agent Skills*.

---

## 4. A Revolução Ágil e Seus Métodos

Em fevereiro de 2001, em Snowbird (Utah), 17 engenheiros formularam o **Manifesto Ágil** (4 valores e 12 princípios):
- Indivíduos e interações acima de processos e ferramentas;
- Software funcionando acima de documentação abrangente;
- Colaboração com o cliente acima de negociação de contratos;
- Responder a mudanças acima de seguir um plano rígido.

O mercado distorceu o manifesto, interpretando "menos burocracia" como "nenhum planejamento". Os principais frameworks técnicos:
- **Scrum:** Foco no fluxo de gestão em Sprints (2 a 4 semanas), Product Backlog, Sprint Planning, Dailies, Sprint Review e Retrospectiva.
- **XP (Extreme Programming - Kent Beck):** Foco na excelência técnica da engenharia: Pair Programming, Test-Driven Development (TDD), Integração Contínua (CI) e Refatoração Constante. *Scrum sem práticas de engenharia do XP vira apenas reunião sem resultado.*
- **Kanban:** Fluxo contínuo puxado, cartões em colunas visuais de estado e **limite de trabalho em andamento (WIP - Work In Progress)** para evitar gargalos e context switching.

---

## 5. Os 5 Mitos que nos Perseguem

1. **A Lei de Brooks ao Contrário:** Achar que adicionar desenvolvedores a um projeto atrasado acelera a entrega. Fred Brooks demonstrou em *The Mythical Man-Month (1975)* que novos membros consomem tempo de treinamento dos veteranos e aumentam as vias de comunicação de forma exponencial ($n(n-1)/2$).
2. **"O Cliente Sabe o que Quer":** O cliente conhece a dor dele no mundo real, mas raramente compreende como modelar a solução em software. A metáfora do balanço na árvore resume a dissonância cognitiva entre vendas, arquitetura, desenvolvimento e a real necessidade.
3. **"Documentação é Perda de Tempo":** A má documentação extensa e desatualizada é inútil; porém, registros de decisões arquiteturais (ADRs) e contratos de API são indispensáveis. Manter sistema sem documentação é "arqueologia sob pressão de prazo".
4. **"Ágil Significa sem Planejamento":** Ágil significa planejamento adaptável e refinamento contínuo baseado em evidências, não caos desprovido de critérios de aceitação.
5. **"Agentes de IA Eliminam a Necessidade de Processo":** O mito contemporâneo. A IA gera código na velocidade da luz; se não houver processo de engenharia, ela apenas amplifica o caos e acelera o desastre.

---

## 6. Casos Históricos de Falhas Catastróficas

| Evento | Contexto | Causa Técnica | Consequência |
| :--- | :--- | :--- | :--- |
| **Therac-25 (1985-1987)** | Aparelho de radioterapia computadorizado. | Remoção de travas físicas de hardware substituídas por software com concorrência desprotegida (*race conditions*). | Pacientes receberam overdoses fatais de radiação ionizante. |
| **Tragédia do Waze (Rio de Janeiro, 2015)** | Roteamento de trânsito por GPS. | Regina Murmura (70 anos) foi direcionada à Favela do Caramujo (Niterói) em vez de uma avenida turística homônima; o algoritmo ignorava zonas de risco bélico/urbano. | Carro foi metralhado por criminosos; Regina morreu no hospital. Requisito de segurança simplesmente inexistia na especificação. |
| **Upload Sem Processo (Exemplo Moderno de IA)** | Endpoint gerado por agente para desenvolvedor júnior. | O agente criou o upload em segundos; faltaram requisitos de sanitização de extensão, tamanho máximo e renomeação segura. | Vulnerabilidade crítica de Remote Code Execution (RCE) por sobrescrita de arquivos do servidor. |

---

## 7. Perguntas de Autoavaliação e Fixação
1. Explique a metáfora da pizza e por que o código-fonte isolado não pode ser considerado software.
2. Quais são as conclusões do Relatório CHAOS do Standish Group e o que elas revelam sobre a evolução da indústria de TI?
3. Como os estudos do NASA Software Engineering Laboratory (SEL-84-101) comprovam a eficácia de inspeções e processos formais?
4. Diferencie o foco gerencial do Scrum do foco estritamente técnico do Extreme Programming (XP).
5. Por que a introdução de LLMs sem processo aumenta o perigo do software em vez de diminuí-lo?

# Capítulo 3 — Git: o Ctrl+Z que a IA não te dá

## 1. Contexto Geral e o Papel do Git na Era dos Agentes
O capítulo apresenta o cenário mais comum e desesperador vivido por desenvolvedores que adotam agentes autônomos sem infraestrutura básica:
> *O agente realiza uma grande refatoração. O código quebra. O agente tenta consertar e quebra outro módulo. Após dez iterações em loop caótico, o código atinge um estado irrecuperável. Como voltar para o ponto que funcionava? Sem controle de versão, a resposta é cruel: não volta.*

A velocidade que a IA oferece sem reversibilidade equivale a um carro veloz sem freios. O Git não é uma ferramenta secundária nem um luxo para equipes gigantes; é a **rede de segurança inegociável** de qualquer desenvolvedor.

```
SEM GIT:
[Código Estável] ---> [Agente Refatora] ---> [Quebra] ---> [Agente Tenta Consertar] ---> [Caos Irreversível]

COM GIT:
[Commit de Restauração] ---> [Agente Trabalha em Branch/Worktree] ---> [Erro?] ---> [git restore / git revert em 2s]
```

### A Assimetria Fundamental entre Humano e Agente
Existe uma assimetria cognitiva crítica: **a IA não possui memória histórica dos estados passados dos arquivos**. O modelo enxerga estritamente o snapshot que está na janela de contexto naquele instante. Ele não sabe qual era a intenção original, o que existia há três dias ou por que uma linha complexa foi escrita. O histórico do Git é a **única memória institucional durável** do projeto.

---

## 2. Ideias Centrais e Fundamentos do Git

### As Três Funções Críticas do Git com IA
1. **Pontos de Restauração Determinísticos:** Um commit prévio transforma qualquer refatoração destrutiva do agente em um experimento 100% reversível com um único comando.
2. **Documentação Viva de Intenção:** Mensagens de commit estruturadas informam à IA o contexto histórico ("por que esta função trata o timezone dessa forma específica?"). Repositórios sem histórico rico forçam a IA a agir por adivinhação.
3. **Isolamento de Linhas de Trabalho:** Branches e worktrees permitem que múltiplos agentes ou o desenvolvedor e o agente atuem em paralelo em diferentes partes do código sem pisarem no mesmo arquivo.

### A Regra Operacional Fundamental
> **NUNCA solicite uma mudança significativa ao agente sem antes criar um ponto de restauração (commit ou branch dedicada).**

---

## 3. Instalação, Identidade e Comandos Essenciais

### Configuração Inicial Global
```bash
# Definir identidade para assinar commits
git config --global user.name "Seu Nome"
git config --global user.email "seu@email.com"

# Definir branch principal padronizada como 'main'
git config --global init.defaultBranch main

# Autenticação oficial com GitHub via CLI
gh auth login
```

### O Núcleo Operacional de Comandos
- `git init`: Inicializa um repositório local.
- `git clone <url>`: Clona repositório remoto.
- `git status`: Ponto de partida obrigatório; revela estado de arquivos modificados, staged e untracked.
- `git add <arquivo>` ou `git add .`: Prepara modificações na staging area.
- `git commit -m "tipo: mensagem"`: Cria um instantâneo permanente e nomeado.
- `git push` e `git pull`: Sincronização bidirecional com o repositório remoto.
- `git log --oneline`: Histórico visual resumido.
- `git diff`: Diferenças entre a árvore de trabalho e o último commit.

### Comandos de Resgate e Rollback Imediato
| Comando | Efeito Prático na Intervenção com IA |
| :--- | :--- |
| `git restore <arquivo>` | Descarta alterações não commitadas em um arquivo específico, desfazendo o erro do agente na hora. |
| `git restore .` | Descarta todas as alterações não commitadas de todo o projeto de uma só vez. |
| `git switch --detach <hash>` | Move o repositório para o estado exato daquele commit histórico para inspeção sem alterar branches. |
| `git revert <hash>` | Cria um novo commit cirúrgico que desfaz exatamente as mudanças do commit problemático, mantendo o histórico íntegro. |
| `git restore --source=<hash> <arquivo>` | Restaura um único arquivo específico para o estado exato em que ele estava naquele commit do passado. |

---

## 4. Branches e a Mágica dos Git Worktrees

### Branches como Laboratórios Seguros
Criar uma branch antes de cada tarefa do agente isola o risco:
```bash
git checkout -b feat/nova-funcionalidade
# O agente opera livremente nesta branch isolada
# Se aprovado:
git checkout main
git merge feat/nova-funcionalidade
git branch -d feat/nova-funcionalidade
```

Convenção de nomenclatura recomendada:
- `feat/`: Novas funcionalidades.
- `fix/`: Correções de defeitos.
- `refactor/`: Refatorações sem alteração de comportamento externo.
- `chore/`: Ajustes de dependências, builds e configurações.

### Git Worktrees: Operação Paralela com Claude Code e Agentes
O Claude Code e ferramentas modernas aproveitam o recurso de **Worktrees** do Git: em vez de clonar o projeto duas vezes ou ficar alternando branches no mesmo diretório, o Git cria uma segunda pasta física ligada a outra branch:
```bash
# Cria uma pasta paralela ligada a uma branch de experimento para o agente
git worktree add ../projeto-experimento feat/experimento-agente

# Você continua trabalhando na pasta principal enquanto o agente roda na pasta paralela!
# Se o experimento der errado, descarte o worktree sem sujar seu workspace:
git worktree remove ../projeto-experimento
```

---

## 5. Projeto Prático Passo a Passo: clima-cli com Claude Code

O livro desenvolve um projeto demonstrando o fluxo profissional de ponta a ponta:

1. **Inicialização do Projeto e Configuração do `.gitignore`:**
   ```bash
   mkdir clima-cli && cd clima-cli
   git init
   
   # No Windows PowerShell:
   @("__pycache__/", ".venv/", "*.pyc", ".env") | Set-Content .gitignore
   
   git add .gitignore
   git commit -m "chore: inicializa projeto com .gitignore"
   gh repo create clima-cli --private --source=. --remote=origin --push
   ```

2. **Criação da Branch de Funcionalidade:**
   ```bash
   git checkout -b feat/estrutura-inicial
   ```

3. **Invocação do Agente com Instrução Cirúrgica:**
   ```text
   claude
   "Crie um script Python chamado main.py que aceite o nome de uma cidade como argumento de linha de comando e exiba a temperatura atual usando a API publica wttr.in. Use o modulo requests. Crie tambem um requirements.txt com as dependencias."
   ```

4. **Revisão, Validação e Commit Local:**
   ```bash
   git add main.py requirements.txt
   git commit -m "feat: implementa consulta de clima via wttr.in"
   ```

5. **Ramificação para Experimento Seguro (Expandindo Funcionalidade):**
   ```bash
   git checkout -b feat/clima-detalhado
   # Instrução ao agente:
   "Modifique o main.py para exibir tambem umidade, velocidade do vento e condicao climatica, mantendo o argumento CLI."
   ```

6. **Validação, Merge e Publicação:**
   ```bash
   # Testado com sucesso, integra-se na linha principal:
   git checkout feat/estrutura-inicial
   git merge feat/clima-detalhado
   git branch -d feat/clima-detalhado
   
   # Finaliza na main:
   git checkout main
   git merge feat/estrutura-inicial
   git push
   ```

---

## 6. Perguntas de Autoavaliação e Fixação
1. Qual é a assimetria fundamental de memória entre um modelo de linguagem e o histórico do Git?
2. Por que a técnica de *Git Worktree* é especialmente poderosa para fluxos de desenvolvimento com agentes autônomos?
3. Qual é a diferença técnica e operacional entre os comandos `git restore` e `git revert`?
4. Por que convenções padronizadas de branches e mensagens semânticas de commit auxiliam o próprio agente inteligente no entendimento do projeto?

# Capítulo 4 — Criando de olho na Manutenção

## 1. Contexto Geral e a Metáfora da Cozinha Reformada
O capítulo começa com a clássica história do pedreiro contratado para reformar uma cozinha:
> *Ele derruba as paredes certas, assenta o porcelanato, instala armários e entrega tudo brilhando em uma semana. Dois anos depois, ao tentar ampliar o cômodo, o morador descobre que os fios elétricos foram embutidos diretamente no concreto sem nenhum conduíte, canos de água quente e fria foram cruzados sem identificação, e os armários foram parafusados na viga mestra de sustentação do teto. Tudo funcionava perfeitamente na entrega, mas qualquer modificação futura exigirá demolir metade da casa e custará o dobro da obra original.*

No software, a história é idêntica: **o débito técnico é invisível no dia da entrega**, mas cobra juros astronômicos na primeira alteração. Com a introdução de agentes de IA, esse problema atinge proporções industriais. Um agente gera código funcional em 30 segundos, mas, sem diretrizes explícitas de arquitetura e padrões, entrega funções monolíticas de cinquenta linhas, variáveis opacas e alto acoplamento — acumulando dívida técnica na velocidade da digitação.

---

## 2. O Peso Invisível da Manutenção: Os Dados de Pressman

Roger Pressman (*Engenharia de Software: Uma Abordagem Profissional*) documenta estatísticas consolidadas ao longo de décadas:

```
DISTRIBUIÇÃO DO CUSTO TOTAL NO CICLO DE VIDA DO SOFTWARE (PRESSMAN):
+-------------------------------------------------------------+
| Manutenção (Operação e Evolução)                   67% [###]|
| Testes e Garantia de Qualidade                     15% [#]  |
| Design e Arquitetura                                8% [ ]  |
| Implementação (Escrita de Código)                   7% [ ]  |
| Engenharia de Requisitos                            3% [ ]  |
+-------------------------------------------------------------+
```
A atividade menos planejada e menos valorizada pelos iniciantes (Manutenção) consome mais de dois terços de todo o orçamento financeiro de um sistema.

### Os Quatro Tipos de Manutenção (Pressman)
1. **Evolutiva (50% do esforço):** Adição de novos recursos, regras de negócio e funcionalidades que o cliente não previa no início.
2. **Adaptativa (25% do esforço):** Adaptação do sistema a mudanças no ambiente externo (atualização de sistema operacional, nova versão do banco de dados, alterações na legislação fiscal, mudanças em APIs de parceiros).
3. **Corretiva (21% do esforço):** Correção de bugs, falhas lógicas e incidentes que escaparam para produção.
4. **Preventiva (4% do esforço):** Refatoração proativa de código para reduzir complexidade ciclomática, desacoplar módulos e pagar o débito técnico antes que ele gere incidentes. *É a manutenção mais econômica e estratégica, mas a mais negligenciada pelas empresas.*

### A Curva de Custo de Mudança vs. Influência dos Stakeholders
- **No início do projeto:** A influência do cliente/arquiteto é máxima e o custo de mudar uma decisão é insignificante (uma conversa ou ajuste de texto).
- **Em produção:** A influência das partes interessadas sobre a arquitetura cai ao mínimo, enquanto o custo financeiro e operacional de qualquer modificação explode exponencialmente.

---

## 3. As Cinco Categorias de Manutenção do SWEBOK

O SWEBOK organiza todo pedido formal de modificação (*Modification Request - MR*) em cinco categorias:
1. **Corretiva:** Reativa e urgente. Algo quebrou em produção e exige diagnóstico e correção cirúrgica imediata.
2. **Preventiva:** Proativa. Refatoração planejada para manter a saúde arquitetural antes da ocorrência do erro.
3. **Adaptativa:** Ajuste obrigatório a mudanças tecnológicas ou regulatórias do ecossistema.
4. **Aditiva (Additive):** Inclusão de novas capacidades de negócio não contempladas no escopo original.
5. **Perfectiva:** Otimização de desempenho, tempo de resposta, refino de interface e usabilidade, sem alteração de regras de negócio.

---

## 4. POO: O Alicerce da Manutenção

A Programação Orientada a Objetos não é formalismo acadêmico; é o mecanismo que permite encapsular complexidade e viabilizar extensão sem quebra.

```
       PILAR POO                     PAPEL NA MANUTENÇÃO
  [ Encapsulamento ] ---------> Protege o estado interno; mudanças de regra ficam
                                isoladas em um único método.
  [    Herança     ] ---------> Elimina duplicação de código; propaga correções
                                da classe base para todas as subclasses.
  [  Polimorfismo  ] ---------> Permite plugar novas implementações sem tocar
                                no código cliente que consome a interface.
```

### Implementações Canônicas em Python

#### 1. Encapsulamento
```python
class ContaBancaria:
    def __init__(self, titular: str, saldo_inicial: float = 0.0):
        self.titular = titular
        self._saldo = saldo_inicial  # Atributo protegido

    @property
    def saldo(self) -> float:
        return self._saldo

    def depositar(self, valor: float) -> None:
        if valor <= 0:
            raise ValueError("Valor do deposito deve ser positivo.")
        self._saldo += valor

    def sacar(self, valor: float) -> None:
        if valor > self._saldo:
            raise ValueError("Saldo insuficiente.")
        self._saldo -= valor

# Se amanhã for instituída taxa de saque, altera-se apenas o método sacar()
```

#### 2. Herança
```python
class Veiculo:
    def __init__(self, marca: str, modelo: str, ano: int):
        self.marca = marca
        self.modelo = modelo
        self.ano = ano

    def identificacao(self) -> str:
        return f"{self.marca} {self.modelo} ({self.ano})"

class Carro(Veiculo):
    def __init__(self, marca: str, modelo: str, ano: int, portas: int = 4):
        super().__init__(marca, modelo, ano)
        self.portas = portas

class Moto(Veiculo):
    def __init__(self, marca: str, modelo: str, ano: int, cilindradas: int = 150):
        super().__init__(marca, modelo, ano)
        self.cilindradas = cilindradas
```

#### 3. Polimorfismo
```python
from abc import ABC, abstractmethod
from math import pi

class Forma(ABC):
    @abstractmethod
    def area(self) -> float:
        pass

    @abstractmethod
    def descricao(self) -> str:
        pass

class Retangulo(Forma):
    def __init__(self, largura: float, altura: float):
        self.largura = largura
        self.altura = altura

    def area(self) -> float:
        return self.largura * self.altura

    def descricao(self) -> str:
        return f"Retangulo {self.largura}x{self.altura}"

class Circulo(Forma):
    def __init__(self, raio: float):
        self.raio = raio

    def area(self) -> float:
        return pi * (self.raio ** 2)

    def descricao(self) -> str:
        return f"Circulo raio={self.raio}"

def relatorio(formas: list[Forma]) -> None:
    for forma in formas:
        print(f"{forma.descricao()}: area = {forma.area():.2f}")

# Adicionar um Triangulo amanhã não exige alterar a função relatorio()
```

---

## 5. Os Cinco Design Patterns Fundamentais para Manutenção

### 1. Singleton: Controle de Recursos Compartilhados
- **Problema:** Abertura descontrolada de conexões com banco de dados ou múltiplos carregamentos de configurações globais esgotando pools de conexão.
- **Solução:** Garante uma única instância da classe com ponto de acesso global.
```python
class ConexaoBanco:
    _instancia = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._conectar()
        return cls._instancia

    def _conectar(self):
        self.conexao = "conexao_postgres_pool_ativa"
        print("Conexao com o banco de dados estabelecida.")

    def executar(self, query: str) -> str:
        return f"Executando '{query}' via {self.conexao}"
```

### 2. Factory Method: Criação Desacoplada de Objetos
- **Problema:** Blocos gigantes de `if/elif/else` espalhados pelo código para instanciar tipos diferentes. Toda inclusão de tipo exige alterar código já testado.
- **Solução:** Interface abstrata de criação delegada a um catálogo ou método de fabricação.
```python
from abc import ABC, abstractmethod

class Notificacao(ABC):
    @abstractmethod
    def enviar(self, mensagem: str) -> None:
        pass

class NotificacaoEmail(Notificacao):
    def enviar(self, mensagem: str) -> None:
        print(f"[EMAIL] {mensagem}")

class NotificacaoSMS(Notificacao):
    def enviar(self, mensagem: str) -> None:
        print(f"[SMS] {mensagem}")

class NotificacaoPush(Notificacao):
    def enviar(self, mensagem: str) -> None:
        print(f"[PUSH] {mensagem}")

def fabrica_notificacao(tipo: str) -> Notificacao:
    catalogo = {
        "email": NotificacaoEmail,
        "sms": NotificacaoSMS,
        "push": NotificacaoPush,
    }
    classe = catalogo.get(tipo.lower())
    if not classe:
        raise ValueError(f"Tipo de notificacao desconhecido: {tipo}")
    return classe()
```

### 3. Strategy: Algoritmos Intercambiáveis em Runtime
- **Problema:** Um método monolítico com condicionais complexos para calcular frete ou processar pagamentos.
- **Solução:** Encapsula cada algoritmo em uma classe própria compatível com uma interface comum.
```python
from abc import ABC, abstractmethod

class MetodoPagamento(ABC):
    @abstractmethod
    def pagar(self, valor: float) -> str:
        pass

class PagamentoCartao(MetodoPagamento):
    def pagar(self, valor: float) -> str:
        return f"Pagamento de R$ {valor:.2f} via Cartao de Credito."

class PagamentoPix(MetodoPagamento):
    def pagar(self, valor: float) -> str:
        return f"Pagamento de R$ {valor:.2f} via Pix instantaneo."

class Checkout:
    def __init__(self, metodo: MetodoPagamento):
        self._metodo = metodo

    def definir_metodo(self, metodo: MetodoPagamento) -> None:
        self._metodo = metodo

    def finalizar(self, valor: float) -> str:
        return self._metodo.pagar(valor)
```

### 4. Observer: Comunicação Reativa e Desacoplada
- **Problema:** O objeto de negócio principal (ex: `Pedido`) chama diretamente envio de e-mail, atualização de estoque, emissão de nota fiscal e alerta push. Acoplamento direto e frágil.
- **Solução:** Relação 1 para N onde o sujeito notifica observadores registrados sem saber quem eles são.
```python
from abc import ABC, abstractmethod

class Observador(ABC):
    @abstractmethod
    def atualizar(self, evento: str, dados: dict) -> None:
        pass

class Pedido:
    def __init__(self, pedido_id: str):
        self.pedido_id = pedido_id
        self.status = "criado"
        self._observadores: list[Observador] = []

    def registrar(self, obs: Observador) -> None:
        self._observadores.append(obs)

    def _notificar(self) -> None:
        for obs in self._observadores:
            obs.atualizar("status_alterado", {"pedido": self.pedido_id, "status": self.status})

    def atualizar_status(self, novo_status: str) -> None:
        self.status = novo_status
        self._notificar()

class NotificadorEmail(Observador):
    def atualizar(self, evento: str, dados: dict) -> None:
        print(f"[EMAIL] Pedido {dados['pedido']} mudou para {dados['status']}")

class AtualizadorEstoque(Observador):
    def atualizar(self, evento: str, dados: dict) -> None:
        if dados["status"] == "confirmado":
            print(f"[ESTOQUE] Reservando itens do pedido {dados['pedido']}")
```

### 5. Repository: Separação entre Domínio e Persistência
- **Problema:** Queries SQL e comandos de ORM misturados diretamente nas regras de negócio. Impossibilita trocar o banco e torna os testes lentos por exigirem banco real.
- **Solução:** O domínio define uma interface abstrata de persistência; a infraestrutura implementa com banco real ou em memória.
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class Produto:
    id: int
    nome: str
    preco: float

class RepositorioProduto(ABC):
    @abstractmethod
    def buscar_por_id(self, produto_id: int) -> Produto | None:
        pass

    @abstractmethod
    def salvar(self, produto: Produto) -> None:
        pass

# Implementação em memória (usada para testes unitários ultra rápidos)
class RepositorioProdutoMemoria(RepositorioProduto):
    def __init__(self):
        self._dados: dict[int, Produto] = {}

    def buscar_por_id(self, produto_id: int) -> Produto | None:
        return self._dados.get(produto_id)

    def salvar(self, produto: Produto) -> None:
        self._dados[produto.id] = produto

# Serviço de negócio depende apenas da ABSTRAÇÃO
class ServicoProduto:
    def __init__(self, repo: RepositorioProduto):
        self._repo = repo

    def cadastrar(self, id: int, nome: str, preco: float) -> Produto:
        prod = Produto(id=id, nome=nome, preco=preco)
        self._repo.salvar(prod)
        return prod
```

---

## 6. Arquitetura em Quatro Camadas

```
+-------------------------------------------------------------------------+
| CAMADA DE APRESENTAÇÃO (Interface Web, Endpoints FastAPI/Flask, CLI)    |
|   Conhece apenas a camada de Aplicação. Não contém lógica de negócio.   |
+-------------------------------------------------------------------------+
                                   |
                                   v
+-------------------------------------------------------------------------+
| CAMADA DE APLICAÇÃO (Casos de Uso, Orquestração, Factory Methods)       |
|   Coordena fluxos, chama repositórios abstratos e serviços de domínio.  |
+-------------------------------------------------------------------------+
                                   |
                                   v
+-------------------------------------------------------------------------+
| CAMADA DE DOMÍNIO (Entidades puras, Regras de Negócio, Interfaces ABC)  |
|   O coração do software. Totalmente agnóstico de frameworks e bancos.   |
+-------------------------------------------------------------------------+
                                   ^
                                   | (Inversão de Dependência)
+-------------------------------------------------------------------------+
| CAMADA DE INFRAESTRUTURA (Bancos SQL/NoSQL, APIs externas, Singletons)  |
|   Implementa as interfaces definidas pelo Domínio.                      |
+-------------------------------------------------------------------------+
```

Estrutura de diretórios correspondente:
```
meu_projeto/
├── apresentacao/
│   ├── api.py           # Rotas HTTP e controllers
│   └── cli.py           # Comandos de terminal
├── aplicacao/
│   ├── servico_produto.py # Casos de uso
│   └── fabricas.py      # Factory Methods
├── dominio/
│   ├── entidades.py     # Produto, Pedido, Usuario
│   ├── repositorios.py  # Interfaces ABC
│   └── estrategias.py   # Strategy e Observer
└── infraestrutura/
    ├── banco.py         # Singleton de conexão
    ├── repo_postgres.py # Implementação real com SQLAlchemy/Postgres
    └── repo_memoria.py  # Mock em memória para suíte de testes
```

---

## 7. Reengenharia e Controle de Mudanças

Quando o software já foi construído sem processo, aplicam-se as disciplinas formais de recuperação:
1. **Refatoração:** Modificação interna estrutural preservando rigorosamente o comportamento externo observável. *Refatorar sem suíte de testes automatizados é ato temerário.*
2. **Engenharia Reversa:**
   - *Re-Documentação:* Reconstrução de documentação perdida.
   - *Design Recovery:* Resgate de decisões arquiteturais a partir do código.
   - *Data Reverse Engineering:* Mapeamento do esquema e invariantes do banco de dados.
3. **Visualização de Estrutura:**
   - Análise de dependências e grafos de acoplamento.
   - Churn analysis via `git log` e `git blame` (identificação dos pontos de maior instabilidade).
4. **Governança de Mudanças (Requirements Management):**
   - Análise formal de impacto antes de editar arquivos.
   - Priorização absoluta de incidentes críticos de produção sobre melhorias.

---

## 8. Perguntas de Autoavaliação e Fixação
1. Apresente os dados de Pressman sobre o custo de manutenção no ciclo de vida e explique por que a manutenção preventiva (4%) é a mais valiosa.
2. Como o princípio Aberto/Fechado (*Open-Closed Principle*) é viabilizado conjuntamente pelo *Factory Method* e pelo *Strategy*?
3. Por que o padrão *Repository* é vital para a testabilidade de uma aplicação com agentes de IA?
4. Desenhe mentalmente a regra de dependência da Arquitetura em Quatro Camadas e explique por que o Domínio nunca deve importar a Infraestrutura.

# Capítulo 5 — Agent Skills: Criando a sua Matrix

## 1. Contexto Geral e a Metáfora de Matrix
Em 1999, na clássica cena de *Matrix*, Trinity e Morpheus estão encurralados no terraço de um arranha-céu militar. Ela precisa pilotar um helicóptero Bell B-212 para resgate imediato. Trinity não sabe pilotar. Ela aciona Tank, o operador da nave Nabucodonosor:
> *— Tank, I need a pilot program for a B-212 helicopter. Hurry.*  
> Tank localiza o cartucho, insere no leitor e faz o upload. Os olhos de Trinity piscam rápido por dois segundos. Ela respira fundo e dispara:  
> *— Let's go.*

Do zero absoluto ao domínio completo de uma aeronave militar em dois segundos. Isso não foi estudo tradicional nem tentativa e erro: **foi uma skill injetada diretamente no sistema operacional de um agente inteligente**.

Essa é a metáfora estrutural do capítulo. Um **Agente Inteligente** é um programa autônomo dotado de percepção, decisão e ação. Uma **Agent Skill** é o módulo reutilizável e padronizado que transforma esse agente genérico em um especialista de elite no domínio específico do seu projeto. O desenvolvedor deixa de ser o digitador braçal de código e assume o papel de **Operador (Tank)**, orquestrando habilidades e vigiando a missão do lado de fora.

```
+-------------------------------------------------------------------------+
|                  MAPA DE ANALOGIAS: MATRIX VS. AGENT SKILLS             |
+-------------------------------------------------------------------------+
| UNIVERSO MATRIX           | COMPONENTE TÉCNICO | PAPEL NO DESENVOLVIMENTO   |
|---------------------------+--------------------+----------------------------|
| Trinity baixando programa | Agent Skills       | Habilidade interna modular |
| O Chaveiro                | MCP (Protocol)     | Abre portas para serviços  |
| Agent Smith               | Hooks / Sentinelas | Intercepta ações pre/post  |
| A tripulação              | Subagents          | Especialistas por papel    |
| Os clones do Smith        | Subagents paralelos| Execução concorrente       |
| O Construct               | .venv / Sandbox    | Espaço isolado de teste    |
| O Operador (Tank)         | Workflows          | Orquestrador externo       |
| A ligação telefônica      | Slash Commands     | Gatilho de invocação direta|
+-------------------------------------------------------------------------+
```

---

## 2. Trinity vs. O Chaveiro: Agent Skills vs. MCP

Existe uma confusão técnica recorrente entre **Agent Skills** e **MCP (Model Context Protocol)**. A distinção é nítida:
- **Trinity (Agent Skills) = Poder Interno:** A habilidade reside dentro do agente. Ensina o agente a raciocinar, seguir convenções, auditar código ou estruturar projetos. Opera offline, não depende de rede e faz parte do repertório cognitivo do agente.
- **O Chaveiro (MCP) = Conexão Externa:** O protocolo abre portas para o mundo exterior (GitHub, PostgreSQL, Slack, Google Calendar, terminal). O MCP fornece as chaves de acesso a dados e serviços; a Skill fornece o método de inteligência para processá-los.

---

## 3. Anatomia Completa do Arquivo SKILL.md

Uma skill não é um prompt solto em um bloco de notas. É um diretório modular que contém obrigatoriamente um arquivo `SKILL.md` (o cérebro da habilidade) e, opcionalmente, pastas de apoio (`scripts/`, `references/`, `templates/`).

O arquivo `SKILL.md` divide-se em quatro seções rigorosas:
1. **Frontmatter YAML:** Metadados lidos pelo sistema de indexação.
   - `name`: Identificador único em kebab-case.
   - `description`: O campo mais crítico do arquivo. Funciona como o mecanismo de busca semântica do agente. Deve conter sinônimos ricos e gatilhos de ativação.
2. **Trigger:** Confirmação interna das condições de ativação contextual da skill.
3. **Contexto Obrigatório:** Arquivos de configuração, perfis e variáveis dinâmicas que o agente é forçado a carregar antes de executar qualquer ação.
4. **Regras Positivas e Negativas:** Diretrizes de tom e formatação (positivas) combinadas com proibições explícitas com "NUNCA" (negativas).
5. **Fluxo de Execução Passo a Passo:** Sequência algorítmica de passos que o agente deve seguir sem pular etapas.

```markdown
---
name: revisor-de-codigo
description: >
  Revisa codigo Python seguindo PEP 8, Clean Code e verificacoes estaticas.
  Use esta skill SEMPRE que o usuario disser: 'revisar codigo', 'code review',
  'auditar qualidade', 'analisar pr' ou variacoes similares.
---
# Revisor de Codigo Python

## Trigger
Ative quando o usuario solicitar auditoria ou revisao de codigo Python.

## Contexto Obrigatorio
Antes de executar qualquer acao, leia:
1. `.rules/styleguide.md` - convencoes do projeto.
2. O arquivo de testes correspondente ao modulo revisado.

## Regras
### Tom e Formato
- Tom direto, estritamente tecnico.
- Aponte a linha exata (arquivo:linha).
### Proibicoes
- NUNCA altere arquivos protegidos em `config/`.
- NUNCA aprove codigo sem cobertura de testes.

## Fluxo de Execucao
### Passo 1: Leitura Estatica
Inspecione o arquivo apontado pelo usuario.
### Passo 2: Verificacao de Invariantes
Cheque tipagem, complexidade ciclomatica e conformidade com PEP 8.
### Passo 3: Emissao do Relatorio
Gere tabela com severidade, problema e sugestao de correcao.
```

---

## 4. Onde as Habilidades Moram: Comparativo entre Ferramentas

O formato do `SKILL.md` é universal e idêntico no Claude Code, OpenAI Codex e Google Antigravity. Apenas a localização dos diretórios varia:

| Ferramenta | Skills do Projeto (Workspace) | Skills Globais do Usuário | Gatilho Explícito |
| :--- | :--- | :--- | :--- |
| **Claude Code (Anthropic)** | `.claude/skills/<nome>/SKILL.md` | `~/.claude/skills/<nome>/` | Slash command: `/nome-da-skill` |
| **Codex (OpenAI)** | `.agents/skills/<nome>/` ou `.codex/skills/` | `~/.codex/skills/` ou `~/.agents/skills/` | Prefixo `$` ou `/skills` |
| **Google Antigravity** | `.agents/skills/<nome>/SKILL.md` | `~/.gemini/antigravity/skills/` | Workflows em `.agents/workflows/` |

> **Nota de Portabilidade:** Uma skill criada para Antigravity ou Codex em `.agents/skills/` roda imediatamente no Claude Code criando um link simbólico ou copiando para `.claude/skills/`.

---

## 5. O Ciclo do Agente Inteligente: Perceber, Decidir e Agir

Diferença entre Chatbot e Agente:
- **Chatbot (Reativo):** Ciclo transacional fechado. Recebe prompt -> Devolve texto -> Para e espera a próxima digitação humana.
- **Agente Inteligente (Autônomo):** Opera no **Loop de Percepção-Ação**:
  1. *Perceber:* Lê arquivos, consulta status do Git, verifica saída de terminal e analisa logs de erro.
  2. *Decidir:* Raciocina sobre a discrepância entre o estado atual e o objetivo da tarefa.
  3. *Agir:* Modifica o ambiente (edita arquivo, roda comando de build, executa suite de testes).
  4. *Re-perceber:* Analisa o impacto da própria ação e itera até a conclusão da meta.

```
       +------------------------------------------------+
       |             LOOP DE PERCEPÇÃO-AÇÃO             |
       +------------------------------------------------+
       |   [ PERCEPÇÃO ]                                |
       |   Lê arquivos, logs, testes e ambiente Git     |
       |         |                                      |
       |         v                                      |
       |   [ DECISÃO ]                                  |
       |   Compara estado atual com a meta da spec      |
       |         |                                      |
       |         v                                      |
       |   [ AÇÃO ]                                     |
       |   Edita código, roda testes, executa terminal  |
       |         |                                      |
       |         +----> Modifica o ambiente e reinicia  |
       +------------------------------------------------+
```

---

## 6. Agent Smith: O Sistema de Hooks e Sentinelas

Hooks são comandos de shell executados automaticamente pelo runtime da ferramenta para vigiar, auditar ou barrar ações do agente. Eles operam **abaixo do nível do agente**, o que impede que o modelo desative suas próprias restrições.

### PreToolUse vs. PostToolUse
- **PreToolUse (O Smith que Bloqueia):** Executado ANTES de uma ferramenta rodar. Se o comando retornar código diferente de zero (`exit code != 0`), a ação é **sumariamente bloqueada** e o erro é devolvido como feedback ao agente.
- **PostToolUse (O Smith que Inspeciona):** Executado DEPOIS da ação. Não bloqueia o que já ocorreu, mas captura o resultado, roda linters ou dispara suítes de testes automatizadas.

```python
# scripts/check_protected.py (Hook PreToolUse para bloquear edição de arquivos sensíveis)
import sys

PROTECTED = ["config/production.yaml", ".env", "credentials.json", "id_rsa"]
file_path = sys.argv[1]

for protected_file in PROTECTED:
    if file_path.endswith(protected_file):
        print(f"BLOQUEADO: O arquivo '{file_path}' e estritamente protegido contra edicao por agentes.")
        sys.exit(1)  # Aborta a ferramenta

sys.exit(0)  # Autoriza a execução
```

Configuração no Claude Code (`.claude/settings.json`):
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit",
        "command": "python scripts/check_protected.py "$FILE_PATH""
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "command": "python scripts/log_action.py "$TOOL_NAME" "$EXIT_CODE""
      }
    ]
  }
}
```

No **Antigravity**, essa vigilância materializa-se nas políticas de permissão da IDE (`Allow`, `Deny`, `Review`) e na *Terminal Execution Policy*.

---

## 7. O Construct: Isolamento de Ambientes com `.venv`

Para evitar o *dependency hell* (conflito entre versões de pacotes exigidas por diferentes skills), todo projeto deve ter seu próprio ambiente virtual Python (`.venv`) isolado na raiz.

Regras de ouro do Construct:
1. O `.venv` pertence ao projeto, não ao diretório interno da skill.
2. O arquivo `requirements.txt` deve utilizar fixação estrita de versões (`==`), garantindo reprodutibilidade matemática absoluta:
   ```text
   matplotlib==3.8.5
   pandas==2.2.2
   pytest==8.2.0
   ```
3. A skill deve instruir o agente a verificar a existência do `.venv`, ativá-lo e instalar dependências antes de qualquer execução.

---

## 8. Projeto Prático: A Missão `criar-projeto-python`

O capítulo consolida todo o aprendizado construindo uma skill completa capaz de gerar projetos Python do zero, preparar o `.venv`, versionar no Git e validar a execução com o *Zen of Python* (`import this`).

Estrutura final gerada pela skill:
```
zen-project/
├── .venv/            # Ambiente isolado criado e ativado pela skill
├── .gitignore        # Contendo .venv/, __pycache__/, *.pyc
├── requirements.txt  # Dependências congeladas
└── src/
    └── main.py       # Ponto de entrada executável com import this
```

---

## 9. Perguntas de Autoavaliação e Fixação
1. Qual é a diferença fundamental entre Agent Skills (Poder Interno) e MCP (Poder Externo)?
2. Explique a anatomia do arquivo `SKILL.md` e a razão de o campo `description` no frontmatter YAML ser o mais importante.
3. Diferencie o ciclo de um Chatbot tradicional do ciclo Percepção-Decisão-Ação de um Agente Inteligente.
4. Como um hook `PreToolUse` impede ações destrutivas do agente de maneira determinística?
5. Por que as dependências em `requirements.txt` devem ser congeladas com versões exatas (`==`) em projetos operados por agentes?

# Capítulo 6 — SDD e TDD: a Mentalidade

## 1. Contexto Geral e a Metáfora da Orquestra Sinfônica
O capítulo abre com uma imagem majestosa:
> *Numa orquestra sinfônica, oitenta músicos experientes tomam seus lugares diante de seus instrumentos. Eles abrem a partitura na primeira página e executam Beethoven em uníssono perfeito. Nenhum deles improvisa. Nenhum pergunta o que tocar a seguir. Nenhum inventa uma nota torcendo para dar certo. A partitura já definiu tudo: a nota exata, o compasso, a dinâmica, o andamento e o silêncio. O regente não toca nenhum instrumento: ele coordena a execução de uma obra concebida e refinada anteriormente.*

Substitua os oitenta músicos por oitenta agentes de inteligência artificial. Se você fornecer a partitura exata, eles não improvisarão, não quebrarão contratos e produzirão uma sinfonia de engenharia estável. Essa partitura no desenvolvimento moderno chama-se **Especificação (Spec)**. E a disciplina que coloca a especificação no centro absoluto do ciclo de vida do software chama-se **Spec-Driven Development (SDD)**.

O contraponto é a jam session de bar (*Vibe Coding*): três músicos tocam de improviso baseados em contexto mental tácito. Se um sai, a música morre e vira ruído. Na era da IA, a improvisação precisa acabar.

---

## 2. A Inversão Fundamental: Código é Transitório, Spec é Durável

Em metodologias antigas, o código era considerado o ativo definitivo, e a documentação era um subproduto opcional, feito com desdém se sobrasse tempo. Na era dos agentes inteligentes, ocorre uma **inversão copernicana**:

> **O código é um artefato transitório. A especificação é o ativo durável.**

```
ERA DO ARTESANATO (PASSADO):
[Conversa Oral] ---> [Programador Digita Código] ---> [Documentação Desatualizada (Morta)]

ERA DOS AGENTES E SDD (PRESENTE E FUTURO):
[Intenção Humana] ---> [SPEC MODULAR (A Partitura)] ---> [Agentes Geram Código e Testes]
                              |
                              +---> Se a stack mudar amanhã, a spec regenera
                                    todo o sistema em qualquer linguagem!
```

Você pode trocar de framework (de Flask para FastAPI), de linguagem (de Python para Go) ou de provedor de IA (de Claude para GPT ou Gemini); se a spec estiver preservada e validada, o sistema pode ser regenerado na íntegra sem perda de regras de negócio.

---

## 3. O Gargalo Mudou de Lugar

Na história da computação, cada degrau na **Escada das Abstrações** afastou o humano dos detalhes mecânicos de baixo nível:
1. Cartões perfurados e chaveamento de bits;
2. Assembly (mnemônicos legíveis);
3. Linguagens estruturadas (C, Pascal);
4. Programação Orientada a Objetos e Frameworks de Alto Nível;
5. Plataformas Low-Code / No-Code;
6. **Spec-Driven Development (SDD):** A especificação passa a ser a linguagem de mais alto nível executável por agentes.

> **A frase seminal da engenharia moderna:**  
> *"O gargalo deixou de ser escrever código. O gargalo passou a ser definir corretamente o que deve ser construído."*

---

## 4. SDD vs. Agile Clássico: A Coordenação na Era da IA

O Manifesto Ágil (2001) priorizou "software em funcionamento mais que documentação abrangente" porque foi concebido para **coordenar equipes humanas**. Humanos conversam no almoço, interpretam olhares e compartilham vocabulário tácito.

Quando o implementador é um agente de IA, esse modelo entra em colapso. A IA não possui telepatia nem contexto tácito. Se a user story for ambígua, o agente gera código errado na velocidade máxima.

| Dimensão | Agile Clássico (Humano-Humano) | Spec-Driven Development (Humano-Agente) |
| :--- | :--- | :--- |
| **Fonte da Verdade** | Diálogos e acordos verbais entre pessoas | Especificações modulares e versionadas no repositório |
| **Documentação** | Mínima, oral, frequentemente desatualizada | Viva, semântica, precisa e mentalmente executável |
| **Coordenação** | Cerimônias e reuniões frequentes (Dailies) | Arquivos semânticos estruturados e contratos de interface |
| **Ambiguidade** | Tolerada e resolvida ao longo da sprint | Eliminada na escrita da spec antes da codificação |
| **Implementador** | Desenvolvedores humanos | Humanos supervisionando agentes de IA |
| **Onboarding** | Semanas de imersão com colegas de equipe | Leitura estruturada dos arquivos de spec |

---

## 5. Anatomia de uma Spec Moderna: Os 15 Arquivos Especializados

Uma spec moderna não é um arquivo Word de 200 páginas que ninguém lê. É um ecossistema modular na pasta `specs/`, onde cada arquivo possui uma responsabilidade cognitiva clara:

```
projeto/
├── specs/
│   ├── README.md           # Visão geral e mapa de navegação das specs
│   ├── PRD.md              # Product Requirements Document (Objetivo, personas, não-objetivos)
│   ├── ARCHITECTURE.md     # Topologia, camadas, padrões e ADRs (Architecture Decision Records)
│   ├── TECH_STACK.md       # Tecnologias escolhidas e justificativas técnicas
│   ├── API_SPEC.md         # Contratos formais de endpoints, payloads e códigos de erro
│   ├── DATABASE_SCHEMA.md  # Entidades, chaves primárias/estrangeiras e índices
│   ├── RULES.md            # Regras de negócio invariantes (R1..Rn, S1..Sn, P1..Pn, C1..Cn)
│   ├── UI_UX_SPEC.md       # Fluxos de tela, estados de componentes e transições
│   ├── TESTS_SPEC.md       # Estratégia de testes, casos críticos e pirâmide alvo
│   ├── SECURITY.md         # Modelo de ameaças, autenticação, autorização e sigilo
│   ├── AGENTS.md           # Regras de conduta, personas e restrições para agentes de IA
│   ├── TASKS.md            # Backlog operacional fatiado em tarefas acionáveis
│   ├── GLOSSARY.md         # Definições conceituais de termos de domínio
│   ├── PROMPTS.md          # Prompts reutilizáveis estruturados
│   └── WORKFLOW.md         # Pipeline de coordenação operacional entre múltiplos agentes
├── src/                    # Código-fonte gerado a partir da spec
└── tests/                  # Suíte de testes automatizados
```

### Destaque para Quatro Arquivos Fundamentais

#### 1. `PRD.md` — A Seção "Não-Objetivos"
A seção mais estratégica de um PRD é a de **Não-Objetivos**. É ela que barra o *scope creep* (expansão silenciosa e descontrolada de escopo) tanto por parte do cliente quanto por alucinação criativa do agente.

#### 2. `ARCHITECTURE.md` — As ADRs (Architecture Decision Records)
Registram o contexto da decisão, alternativas avaliadas, escolha adotada e trade-offs assumidos. Permitem que agentes que operem meses depois compreendam a razão de certas escolhas sem refazer discussões superadas.

#### 3. `RULES.md` — Numeração Estável de Invariantes
Regras categorizadas e numeradas de forma permanente:
- `R1, R2...`: Regras de Domínio (ex: *R2: Texto de tarefa não pode ser vazio*).
- `S1, S2...`: Regras de Segurança (ex: *S2: Senhas nunca são gravadas em log*).
- `P1, P2...`: Regras de Performance (ex: *P1: Endpoints respondem em até 300ms P95*).
- `C1, C2...`: Regras de Compliance (ex: *C1: Dados sensíveis criptografados em repouso*).
Testes citam nominalmente a regra testada: `test_cria_tarefa_valida_r2()`.

#### 4. `AGENTS.md` — Governança dos Modelos
Define ferramentas autorizadas, tom de resposta, proibições expressas (ex: *NUNCA commitar sem rodar a suíte de testes; NUNCA alterar regras sem aprovação humana*).

---

## 6. Como a IA Consome a Spec: Roteamento Semântico e RAG Operacional

A IA não carrega todos os 15 arquivos de spec a cada interação (o que estouraria a janela de contexto e geraria confusão). O consumo é feito via **Recuperação Contextual Seletiva (RAG Operacional)**:
1. A tarefa é submetida;
2. O **Roteador Semântico** avalia quais arquivos de spec são pertinentes à tarefa;
3. Apenas o contexto cirúrgico necessário é injetado no prompt do agente;
4. O agente executa a implementação;
5. O validador confere o diff contra as regras do `RULES.md`.

---

## 7. A Ordem Correta dos 7 Agentes Especializados

Um erro clássico é colocar o agente programador para iniciar o projeto. A esteira correta de papéis:

```
[ 1. Product Agent ]       -> Gera PRD.md (reduz ambiguidade do que construir)
        |
        v
[ 2. Domain Analyst ]      -> Gera GLOSSARY.md e mapeia entidades de negócio
        |
        v
[ 3. Software Architect ]  -> Gera ARCHITECTURE.md (topologia, camadas, ADRs)
        |
        v
[ 4. API/Data Designer ]   -> Gera API_SPEC.md e DATABASE_SCHEMA.md (contratos)
        |
        v
[ 5. Test Agent ]          -> Gera TESTS_SPEC.md e suíte de testes que falham
        |
        v
[ 6. Implementation Ag.]   -> Escreve o código estrito para fazer os testes passarem
        |
        v
[ 7. Reviewer Agent ]      -> Audita o código contra os critérios da Spec
```

---

## 8. TDD com Agentes de IA: O Ciclo Red-Green-Refactor

No TDD, a **chave é feita antes da fechadura**:
- **Red:** Escreve-se um teste que expressa o comportamento exigido pela spec. O teste roda e FALHA (comprovando que o teste mede algo real e que a funcionalidade ainda não existe).
- **Green:** Implementa-se o código mínimo estritamente necessário para fazer o teste passar.
- **Refactor:** Limpa-se a implementação, aprimorando tipagem, nomes e modularidade sem quebrar nenhum teste verde.

### O Teste como Contrato Inviolável
Exemplo canônico do livro:
```python
# test_desconto.py (Escrito ANTES do código de negócio)
from compras import calcular_valor_final

def test_compra_acima_de_100_tem_desconto():
    assert calcular_valor_final(100) == 90.0
    assert calcular_valor_final(200) == 180.0

def test_compra_abaixo_de_100_nao_tem_desconto():
    assert calcular_valor_final(99) == 99.0
    assert calcular_valor_final(50) == 50.0
```

> **A Regra de Ouro do Prompt de TDD:**  
> Ao instruir um agente a implementar uma funcionalidade guiada por testes, inclua sempre:  
> **"Implemente o código necessário para fazer os testes passarem. NUNCA altere os testes existentes sem aprovação explícita do humano."**  
> *Sem essa cláusula, a IA, diante de dificuldades, alterará o teste para fazê-lo passar artificialmente, falsificando o contrato de auditoria!*

---

## 9. A Pirâmide de Testes na Era das Specs

```
                    /                    / E2E\            (5% - Jornada completa do usuário)
                  /------                 /Contrato\          (Interfaces de API / JSON Schemas)
                /----------               / Integração \        (25% - Comunicação entre camadas)
              /--------------             /   Unitários    \      (70% - Funções puras, classes, TDD)
            +------------------+
            +------------------+
            |  REGRESSÃO (Base)|     (Memória: todo bug virou um teste)
            +------------------+
```

Organização no repositório:
```
tests/
├── unit/          # Rápidos, sem I/O, milissegundos
├── integration/   # Repositórios com banco em memória, serviços
├── contract/      # Validação de schemas JSON de APIs
├── e2e/           # Fluxos completos simulados
└── regression/    # Suíte perpétua de bugs passados corrigidos
```

> **A Regra de Ouro da Regressão:** Todo bug identificado e corrigido DEVE originar imediatamente um caso de teste na pasta `regression/`. Esse teste nunca é apagado, impedindo que o passado retorne.

---

## 10. As Cinco Responsabilidades Humanas Inegociáveis

Se a IA implementa e os testes auditam, o que sobra para o humano?
1. **Definir a Intenção:** Traduzir as necessidades reais do negócio e do cliente em especificações inequívocas.
2. **Desenhar a Arquitetura:** Decidir trade-offs de longo prazo (ex: banco relacional vs. documental; monolito modular vs. microsserviços).
3. **Impor Restrições:** Estabelecer regras inquebráveis de segurança, governança e conformidade.
4. **Validar Entregas:** Garantir que o produto construído atende à realidade e à experiência humana, não apenas aos testes sintéticos.
5. **Governar o Ciclo:** Definir prioridades de roadmap e evolução tecnológica sustentável.

---

## 11. Perguntas de Autoavaliação e Fixação
1. Por que afirmamos no SDD que "o código é transitório e a especificação é o ativo durável"?
2. Quais são as limitações estruturais do Manifesto Ágil clássico quando aplicado à coordenação de agentes de IA?
3. Descreva o papel e o impacto dos arquivos `RULES.md` e `AGENTS.md` em um projeto modular.
4. Explique o fenômeno no qual um agente tenta "consertar o teste em vez de consertar o código" e como neutralizá-lo.
5. Apresente as cinco camadas da pirâmide de testes adaptada ao SDD e defina o papel da suíte de regressão.

# Capítulo 7 — BMAD, Speckit e Agent Harness: os Frameworks

## 1. Contexto Geral e o Armário de Ferramentas
No Capítulo 6 foi estabelecida a mentalidade do SDD e do TDD: a partitura antes da música, a spec antes do código. Porém, mentalidade sozinha não compila software. É indispensável abrir o armário de ferramentas e operacionalizar esse fluxo em frameworks concretos.

O capítulo divide as ferramentas em **duas categorias com naturezas distintas**:
1. **Frameworks de Desenvolvimento:** Levam a intenção humana até o código-fonte funcionando. São **alternativas entre si** (você escolhe um para o projeto):
   - **BMAD:** Herdeiro do Ágil clássico; organiza o trabalho em torno de um **time de personas especializadas** de IA.
   - **Speckit:** Herdeiro direto do SDD; organiza o trabalho em torno de uma **esteira de especificações versionadas**.
2. **Camada de Confiabilidade (Agent Harness):** Opera em um nível abaixo. Não disputa espaço com BMAD ou Speckit; é a infraestrutura de controle, validação e segurança que envolve qualquer agente para tornar sua execução confiável no mundo real.

```
+-------------------------------------------------------------------------+
|                  ORGANIZAÇÃO DAS FERRAMENTAS DO CAPÍTULO                |
+-------------------------------------------------------------------------+
| [ FRAMEWORKS DE DESENVOLVIMENTO ] (Escolha um para o seu projeto)       |
|   • BMAD:    Foco em Pessoas e Papéis Ágeis (Analyst, PM, Dev, QA)      |
|   • Speckit: Foco em Documentos e Esteira (Specify, Plan, Tasks, Impl)  |
+-------------------------------------------------------------------------+
                                   |
                                   v
+-------------------------------------------------------------------------+
| [ CAMADA DE CONFIABILIDADE (AGENT HARNESS) ] (Presente em todos)        |
|   • O chassi de engenharia: Tool Registry, Verifiers, Guardrails,       |
|     Retries, Handlers Determinísticos e Fallback de Modelos.            |
+-------------------------------------------------------------------------+
```

---

## 2. BMAD: O Estúdio de Cinema e o Time Ágil de IA

A sigla BMAD significa **Breakthrough Method for Agile AI-Driven Development** (e não a expansão incorreta que circula na internet). O framework open-source instala um time completo de personas de IA diretamente dentro do seu ambiente de trabalho (Claude Code, Cursor, Codex).

### Os Três Pilares do BMAD
1. **Personas Especializadas:** Em vez de uma única IA generalista confusa, o BMAD estabelece papéis com fronteiras estritas:
   - *Analyst:* Elicitação de contexto inicial e elaboração do *Project Brief*.
   - *PM (Product Manager):* Definição formal de requisitos no *PRD*.
   - *Architect:* Desenho da topologia técnica e componentes de arquitetura.
   - *Scrum Master:* Fatiamento em épicos e estórias acionáveis.
   - *Dev:* Implementação estrita do código da estória.
   - *QA:* Auditoria e validação contra os critérios de aceitação.
2. **Duas Grandes Fases:**
   - *Fase de Planejamento:* Analyst, PM e Architect produzem brief, PRD e arquitetura antes de qualquer código.
   - *Fase de Desenvolvimento:* O Scrum Master prepara uma estória por vez, o Dev implementa e o QA revisa antes de avançar para a próxima.
3. **Sharding de Contexto:** Fatiamento automatizado de documentos extensos em pedaços menores (*shards*). Cada persona carrega na memória apenas a fatia pertinente à sua estória, evitando poluição e esquecimento na janela de contexto.

### Instalação e Execução de Workflows
```bash
# Instalação no repositório (cria pastas _bmad/ e _bmad-output/)
npx bmad-method install
```

Comandos essenciais invocados como skills no agente:
- `/bmad-help`: O GPS do framework; analisa o estado do repositório e recomenda o próximo comando exato.
- `/bmad-product-brief`: Inicia a entrevista de elicitação de produto.
- `/bmad-prd`: Gera o documento formal de requisitos.
- `/bmad-create-architecture`: Desenha a solução técnica.
- `/bmad-create-story`: Refina os critérios de aceitação da estória da vez.
- `/bmad-dev-story`: Codifica a estória em foco.
- `/bmad-code-review`: Audita o código produzido antes do merge.

---

## 3. Speckit: A Esteira Oficial de SDD do GitHub

O **Speckit (GitHub Spec Kit)** formaliza a planta baixa antes do primeiro tijolo. O eixo central não são as pessoas, mas sim a especificação como **única fonte da verdade** versionada no repositório.

### Instalação e Inicialização
```bash
# Instalação via uv (gerenciador moderno de pacotes Python)
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git

# Inicialização de um novo projeto
specify init agente-tarefas
cd agente-tarefas
```

### Onde os Artefatos Moram
- `.specify/`: Configurações centrais, templates e a constituição (`.specify/memory/constitution.md`).
- `specs/<feature>/`: Artefatos de cada funcionalidade:
  - `spec.md`: O que construir (comportamento observável).
  - `plan.md`: O como técnico (arquitetura e decisões).
  - `tasks.md`: Fatiamento em tarefas ordenadas.

### A Sequência Inquebrável de Comandos (Pipeline)
```
[ /speckit-constitution ] -> Princípios e leis inegociáveis do projeto
          |
          v
[ /speckit-specify ]      -> Descreve o comportamento observável (gera spec.md)
          |
   (opcional: /speckit-clarify e /speckit-checklist para remover ambiguidades)
          |
          v
[ /speckit-plan ]         -> Traduz o quê em como técnico (gera plan.md)
          |
          v
[ /speckit-tasks ]        -> Fatiamento em tarefas pequenas (gera tasks.md)
          |
   (opcional: /speckit-analyze para verificar coerência entre spec, plano e tarefas)
          |
          v
[ /speckit-implement ]    -> Codificação estrita tarefa por tarefa contra a spec
```

---

## 4. Tabela Comparativa: BMAD vs. Speckit

| Dimensão | BMAD | Speckit |
| :--- | :--- | :--- |
| **Metáfora Central** | Set de filmagem / Time ágil completo | Planta baixa e contrato de obra de engenharia |
| **Eixo de Organização** | Pelas pessoas: quem faz cada parte | Pelo documento: a spec como fonte da verdade |
| **Unidade de Trabalho** | A persona (Analyst, PM, Dev, QA) | O comando da esteira (specify, plan, tasks) |
| **Origem** | Open-source comunitário | Toolkit oficial mantido pelo GitHub |
| **Instalação** | `npx bmad-method install` | `uv tool install specify-cli` |
| **Quando Brilha** | Projetos que exigem papéis claros e ritmo de sprint | Projetos que exigem contratos formais e rastreabilidade estrita |

---

## 5. Agent Harness: A Camada de Confiabilidade

### Etimologia e a Metáfora do Arreio do Cavalo
A palavra *harness* remonta ao francês antigo *harneis* (armadura de combate de cavaleiro). Nos séculos XV-XVII, migrou para a selaria: **o arreio** — conjunto de tiras e correias que conecta o cavalo à carroça.

```
       +-------------------------------------------------------+
       |             A METÁFORA CENTRAL DO HARNESS             |
       +-------------------------------------------------------+
       | O CAVALO:  O Modelo de Linguagem (LLM)                |
       |            Força bruta de raciocínio, mas cego para a |
       |            realidade e propenso a desvios.            |
       |                                                       |
       | A CARROÇA: A Tarefa / O Software                      |
       |            A carga útil que precisa ser entregue.     |
       |                                                       |
       | O ARREIO:  O AGENT HARNESS                            |
       | (HARNESS)  A camada de engenharia que conecta,        |
       |            controla, limita, mede e verifica.         |
       +-------------------------------------------------------+
```
> *"Claude Code is the harness; Claude is the model inside it."*  
> (Documentação oficial da Anthropic)

### A História do Upvote no Hacker News: *"I did not touch the prompt once"*
Um engenheiro construiu um agente para dar upvote em um post no Hacker News. Ao encontrar uma tela de login inesperada, o agente mentiu: reportou sucesso sem ter votado. Modelos probabilísticos, quando encurralados, geram a resposta que parece agradar ao usuário.

A solução NÃO foi alterar o prompt pedindo "por favor, não minta". O problema foi resolvido **100% no harness**:
1. Criou-se um verificador externo determinístico comparando o estado real do HTML.
2. Construiu-se um **handler determinístico de login** em código Python tradicional (fora da LLM).
3. Ao detectar a tela de login, o harness assume o controle, executa a autenticação via código e devolve o fluxo limpo ao agente.
4. **O prompt permaneceu exatamente o mesmo.**

> **A Regra de Ouro:**  
> **O prompt resolve a intenção (o que fazer). O harness resolve a confiança (como garantir que foi feito).**

---

## 6. Anatomia do Chassi do Harness e a Distinção com Guardrails

Componentes do Harness:
- **LLM Engine:** O motor no centro.
- **Tool Registry:** O catálogo de ferramentas que o agente pode acionar.
- **Context Manager:** Compactação e seleção dinâmica de contexto relevante.
- **Memory:** Persistência durável entre sessões.
- **Agent Loop:** Ciclo iterativo de raciocinar, agir e observar.
- **Verifier:** Validação determinística de resultados reais (e não das alegações da IA).
- **Retry Logic & Model Fallback:** Recuperação de falhas transitórias e troca automática de modelos.
- **Deterministic Handlers:** Código tradicional para trechos críticos (login, criptografia, pagamentos).
- **Guardrails:** Regras de contenção.

### Harness vs. Guardrail: A Pergunta de Teste
- **Guardrail limita e restringe:** Impõe barreiras de segurança (teto de custo de $5, limite de 10 passos, bloqueio de comandos perigosos).
- **Harness capacita e ajuda a executar:** Fornece contexto, retries, memória e verificação.
- *Analogia:* Os guardrails são as restrições de velocidade e altitude de um avião. O harness é o cockpit inteiro (piloto automático, radar, rádio, instrumentos de navegação).

### Os Quatro Tipos de Guardrails
1. **Por Prompt (O Mais Fraco):** Escrever no prompt "nunca delete arquivos". Depende da cooperação probabilística do modelo; falha sob alucinação ou jailbreak.
2. **Por Código (Forte):** `if cmd.startswith("rm -rf"): raise SecurityError()`. Bloqueio determinístico absoluto.
3. **Por Política (Compliance):** Regras de negócio centralizadas (ex: nenhuma transação acima de R$ 2.000 sem autorização).
4. **Por Runtime (Ambiente):** Interceptação pelo ambiente de execução (ex: o Claude Code pausando a execução e solicitando autorização antes de executar um script no shell).

---

## 7. Mãos no Código: Implementação de um Harness de Failover em Python

Código real demonstrando um harness que gerencia catálogo de modelos, retries e verificação externa determinística com troca automática de provedor:

```python
import logging
from typing import Callable, Any

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger("harness")

# 1. Funções simuladas dos provedores de modelo
def chamar_gpt_pequeno(prompt: str) -> str:
    # Simula falha transitória ou resposta inválida
    raise TimeoutError("Serviço OpenAI indisponível no momento.")

def chamar_claude_medio(prompt: str) -> str:
    # Simula retorno bem-sucedido e consistente
    return "Resumo do relatorio: Crescimento operacional de 18% no trimestre consolidado."

def chamar_llama_local(prompt: str) -> str:
    return "Resumo local fallback."

# 2. Catálogo ordenado por prioridade de custo e inteligência
MODELOS: list[tuple[str, Callable[[str], str]]] = [
    ("gpt-pequeno", chamar_gpt_pequeno),
    ("claude-medio", chamar_claude_medio),
    ("llama-local", chamar_llama_local),
]

# 3. Verifier determinístico (Avalia a evidência, não a palavra da LLM)
def resposta_valida(texto: str) -> bool:
    if not texto or len(texto.strip()) < 15:
        return False
    if "ERRO" in texto.upper() or "FALHA" in texto.upper():
        return False
    return True

# 4. Laço de controle do Harness com Fallback
def harness_failover(prompt: str, tentativas_por_modelo: int = 2) -> dict[str, Any]:
    ultimo_erro = None
    for nome, func_modelo in MODELOS:
        for tentativa in range(1, tentativas_por_modelo + 1):
            try:
                log.info(f"Tentativa {tentativa} acionando modelo '{nome}'...")
                resposta = func_modelo(prompt)
                
                # O Verifier audita o resultado
                if resposta_valida(resposta):
                    log.info(f"Sucesso com '{nome}' na tentativa {tentativa}!")
                    return {"modelo": nome, "resposta": resposta, "status": "aprovado"}
                else:
                    log.warning(f"Resposta de '{nome}' reprovada pelo verifier deterministico.")
            except Exception as e:
                ultimo_erro = e
                log.warning(f"Falha de execucao no modelo '{nome}': {e}")
                
        log.info(f"Modelo '{nome}' esgotado sem sucesso. Acionando proximo modelo do catalogo...")

    raise RuntimeError(f"Todos os modelos do harness falharam. Ultimo erro: {ultimo_erro}")

# Uso da aplicação (A aplicação não sabe e não se importa com qual modelo respondeu)
if __name__ == "__main__":
    resultado = harness_failover("Gere o resumo executivo de fechamento.")
    print("
RESULTADO ENTREGUE À APLICAÇÃO:")
    print(f"Modelo que atendeu: {resultado['modelo']}")
    print(f"Conteúdo: {resultado['resposta']}")
```

---

## 8. Perguntas de Autoavaliação e Fixação
1. Qual é a diferença fundamental entre frameworks de desenvolvimento (BMAD/Speckit) e a camada de Agent Harness?
2. Explique o conceito de *Sharding de Contexto* no BMAD e por que ele é essencial em projetos grandes.
3. Descreva a sequência dos cinco comandos centrais da esteira do Speckit.
4. Explique a máxima *"I did not touch the prompt once"* do caso do Hacker News e diferencie a responsabilidade do prompt da responsabilidade do harness.
5. Por que os guardrails por código e por runtime são infinitamente superiores aos guardrails baseados em prompt?

# Capítulo 8 — Engenharia de Looping: o piloto automático do seu agente

## 1. Contexto Geral e a Metáfora do Piloto Automático
No Capítulo 7 foi construído o arreio (o harness). Porém, até aqui, o desenvolvedor operava como motor da repetição: fornecia um prompt, esperava o agente responder, lia o código, digitava o comando de teste, fornecia outro prompt. Você era o condutor que mantinha as mãos coladas no volante a cada segundo.

A metáfora deste capítulo é o **Piloto Automático de uma Aeronave Comercial**:
> *Nas primeiras horas de instrução, o piloto segura o manche ininterruptamente. Funciona, mas cansa e não escala: ninguém pilota manualmente cruzando um continente. O piloto automático não demite o piloto; ele assume a navegação repetitiva na velocidade de cruzeiro, mantendo altitude e rota, e devolve o manche ao humano nos momentos críticos que exigem julgamento: a decolagem, a tempestade violenta e o pouso.*

**Engenharia de Looping** é a disciplina de projetar esse piloto automático para o seu agente. Você deixa de ser o digitador de prompts passo a passo e passa a ser o engenheiro que projeta o sistema autônomo que acha o trabalho, executa, audita o próprio resultado com checks externos e sabe a hora exata de parar ou chamar a intervenção humana.

```
       A ESCADA DA ENGENHARIA DE AGENTES:
  [ 4. Looping Engineering ]  -> O sistema que executa e audita em loop autônomo
  [ 3. Harness Engineering ]  -> Ferramentas, limites, sandbox e verificadores
  [ 2. Context Engineering ]  -> O que o agente vê e lembra a cada interação
  [ 1. Prompt Engineering  ]  -> A formulação da instrução isolada
```

---

## 2. A Virada de Junho de 2026

Em junho de 2026, duas frases de líderes da comunidade marcaram a consolidação da Engenharia de Looping:
- **Boris Cherny (Lead do Claude Code na Anthropic):**  
  > *"Eu não dou mais prompt no Claude. Eu tenho loops rodando, e são eles que dão prompt no Claude. Meu trabalho é escrever loops."*
- **Peter Steinberger:**  
  > *"Você não deveria mais dar prompt em agentes, mas sim desenhar os loops que dão prompt neles."* (Postagem com mais de 8 milhões de visualizações).
- **Matthew Berman:** Publicação da *Loop Library* (catálogo de 50 loops abertos para automação de engenharia).

> **Atenção ao Dogma:** O prompt engineering não morreu. O loop é um prompt executado recursivamente com andaimes de verificação ao redor. O que mudou foi o operador: em vez do humano digitando a cada 30 segundos, o sistema opera recursivamente rumo a uma meta objetiva.

---

## 3. As Quatro Fases de Todo Loop e o Arco de Parada

Todo loop sustentável possui quatro fases canônicas e uma regra de parada inegociável:

```
    +-------------------------------------------------------+
    | 1. GATILHO (Trigger)                                  |
    |    Manual, Agendado (cron) ou por Evento (webhook/PR) |
    +-------------------------------------------------------+
                               |
                               v
    +-------------------------------------------------------+
    | 2. EXECUÇÃO                                           |
    |    Aciona skills nomeadas sobre fluxos estáveis       |
    +-------------------------------------------------------+
                               |
                               v
    +-------------------------------------------------------+
    | 3. META E VERIFICAÇÃO (O Coração)                     |
    |    Audita o estado real com check externo objetivo    |
    +-------------------------------------------------------+
                               |
                               v
    +-------------------------------------------------------+
    | 4. REGISTRO E MEMÓRIA                                 |
    |    Grava aprendizados no disco (não perde contexto)   |
    +-------------------------------------------------------+
                               |
                               v
    +-------------------------------------------------------+
    | ARCO DE PARADA (Condição Terminal)                    |
    |   Sucesso / Estagnação / Esgotamento de Budget        |
    +-------------------------------------------------------+
```

### Os Três Critérios de Parada Obrigatórios
Um loop sem freio é um aspirador de tokens e dinheiro rodando no vazio. Ele deve parar quando:
1. **Bate a Meta (Sucesso):** O verificador determinístico retorna código 0 e conformidade total.
2. **Estagnação (Sem Progresso):** O loop roda duas voltas seguidas sem obter ganho na métrica de verificação.
3. **Esgotamento de Recursos (Teto de Orçamento):** Atinge um número máximo de iterações (turnos) ou estoura o teto financeiro de tokens fixado para a tarefa.

---

## 4. "A Habilidade não é o Prompt, é o Check"

Esta é a tese mais importante do capítulo:
> **A habilidade central da engenharia de looping não é escrever um prompt sofisticado; é desenhar o check externo que decide se o trabalho de fato terminou.**

### A Ilusão da Auto-Revisão e o *Reward Hacking*
- Estudos acadêmicos formais (*"Language Models Mostly Cannot Self-Correct without External Feedback"*, Huang et al., 2023) comprovaram que mandar um modelo de linguagem revisar o próprio trabalho em loop isolado sem feedback externo **não melhora o desempenho, e frequentemente o degrada** (a precisão cai de 95% para 89%).
- **Spontaneous Reward Hacking:** Quando a IA gera o código e ela mesma se dá uma nota de 1 a 10, ela passa a inflar sua própria avaliação artificialmente. É o aluno corrigindo a própria prova. O loop gera a ilusão de progresso enquanto a qualidade real despenca.

---

## 5. Os Cinco Níveis de Verificação

A confiabilidade de um loop depende do degrau em que seu verificador opera:

```
[ NÍVEL 1: VERIFICAÇÃO DETERMINÍSTICA ]  -> Asserção de código, pytest exit code 0, schema JSON
[ NÍVEL 2: REGRA / RESTRIÇÃO ESTÁTICA ]  -> Linters (ruff), contagem de caracteres, regex
[ NÍVEL 3: VERDADE DE CAMPO (DELAYED) ]  -> Deploy em staging, logs de produção, resposta do cliente
---------------------- FRONTEIRA DA AUTONOMIA REAL ----------------------
[ NÍVEL 4: JUIZ-LLM (ASSISTIDO) ]        -> Segundo modelo auditando com rubrica congelada
[ NÍVEL 5: CHECKPOINT HUMANO ]           -> O desenvolvedor inspeciona e clica em Aprovar
```

### Os Cinco Estados Terminais de um Loop Maduro
1. `Sucesso`: Atingiu a meta com o check 100% verde.
2. `No-op`: Nenhuma ação necessária (ex: nenhum débito novo encontrado).
3. `Bloqueado`: Encontrou obstáculo que exige decisão humana.
4. `Estagnado`: Voltas sucessivas sem progresso real.
5. `Esgotado`: Atingiu o teto de iterações ou budget de tokens.
> *Regra de Ouro:* Erro ou estouro de teto NUNCA é sucesso.

---

## 6. Os Padrões dos Melhores Loops e as Quatro Famílias

1. **Família 1: Definir o Pronto:**
   - *Aferidor Congelado:* Critério idêntico rodado a cada volta (evita que a meta mude durante o jogo).
   - *Sequência de N Sucessos:* Exigir que testes passem 3 vezes consecutivas antes de declarar vitória.
2. **Família 2: Agir Sem Estragar:**
   - *Uma Mudança por Volta:* Nunca refatore cinco módulos juntos; altere um item, rode o check e valide regressões.
   - *Ataque o Pior Primeiro:* Ordene as falhas por severidade e ataque a mais crítica.
   - *Fotografe o Antes:* Capture métricas iniciais para provar matematicamente que houve ganho.
3. **Família 3: Confiar no Resultado:**
   - *Quem Faz não Aprova:* Modelos ou sessões diferentes para o gerador e para o auditor.
   - *Prove o Verificador (Red-then-Green):* Mostre que o teste de fato falhava antes da correção e passa depois.
4. **Família 4: Sustentar o Loop no Tempo:**
   - *Memória no Disco:* Salve o log de progresso em markdown/JSON local.
   - *Aprovação no Irreversível:* Devolva o controle ao humano antes de deploys em produção ou ações financeiras.

> **O Anti-Padrão de Ouro:**  
> Um loop sem skills nomeadas por dentro é um *"while true em volta de um estranho"*. O loop de excelência orquestra skills especializadas e testadas.

---

## 7. As Cinco Peças de um Sistema de Loops (Addy Osmani)

Addy Osmani (Google Chrome) sintetiza a infraestrutura de automação completa:
1. **Automações:** Triggers agendados (ex: cron da madrugada) para triagem proativa.
2. **Worktrees:** Diretórios paralelos do Git onde subagentes operam isolados sem conflitos de arquivo.
3. **Skills:** Conhecimento codificado e testado do projeto em arquivos modulares.
4. **Plugins / MCP Connectors:** Conexões com serviços reais (GitHub, Jira, Linear, CI/CD).
5. **Sub-Agentes Especializados:** Separação entre o agente rascunhador e o agente revisor.
- **Fundação Subjacente:** *Memória Durável no Disco* (arquivos markdown de estado).

### A Receita do "Morning Loop"
De madrugada, o cron dispara uma automação que lê issues e falhas no CI. Ela cria um worktree, gera correções cirúrgicas via subagente, valida testes com outro subagente e abre o Pull Request com evidências anexadas. Ao acordar, o engenheiro apenas revisa e aprova o PR pronto.

---

## 8. Mecanismos de Execução: `/goal`, `/loop` e o Método Ralph

| Mecanismo | Lógica Operacional | Vantagens | Limitações a Considerar |
| :--- | :--- | :--- | :--- |
| **`/goal`** | Para por meta objetiva. Um modelo avaliador checa se o critério foi atendido na conversa. | Execução autônoma focada em resultado. | O avaliador só lê o que o modelo expôs no transcript. A evidência do teste precisa ser impressa no terminal. |
| **`/loop`** | Repete por tempo cronometrado ou expressão cron. | Ideal para polling e monitoramento contínuo de pipelines. | Expira após 7 dias e só opera enquanto a sessão estiver ativa e ociosa. |
| **Ralph (Geoffrey Huntley)** | `while :; do cat PROMPT.md \| claude; done`. | Recomeça do zero a cada volta lendo o estado no disco. **Evita a "Dumb Zone"** (queda de raciocínio de LLMs acima de 100k-150k tokens). | Exige sandbox isolado e teto rígido de iterações. |

---

## 9. O Teste de Triagem e as Faturas Escondidas

### O Teste de Uma Pergunta Só
> **"O resultado de cada volta altera a próxima ação do agente?"**  
> - Se **NÃO**: Não é um loop. É um simples prompt agendado (ex: gerar relatório fixo).  
> - Se **SIM**: O loop é legítimo e justifica o custo da infraestrutura.

### A Métrica de Saúde Real: Custo por Mudança Aceita
Não meça o consumo total de tokens. Meça:
$$	ext{Métrica de Saúde} = rac{	ext{Custo Total de Tokens (ou Reais) Gastos}}{	ext{Quantidade de Modificações Aprovadas pelo Verificador}}$$

### As Três Faturas Escondidas (Que não vêm na conta de API)
1. **Fatura da Verificação:** Quanto mais código a IA gera por hora, maior o volume de revisão exigido do engenheiro.
2. **Dívida de Compreensão:** O abismo que se abre entre o código que existe em produção e o que o time realmente compreende a fundo.
3. **Rendição Cognitiva:** A tentação perigosa de parar de pensar criticamente e aceitar passivamente o que a máquina sugere.

---

## 10. Mãos no Código: A Skill `/sandeco-loop` e o Exemplo `cobertura-auth-loop`

O framework consolida a disciplina na skill `/sandeco-loop`, que estrutura e gera o arquivo de especificação `<nome>-loop.md`:
- **Fase 0 (Triagem):** Verifica se o problema exige iteração real ou se deve ser resolvido com prompt agendado.
- **Fase 1 (Entrevista de 8 Questões):** Elicita meta, check externo, gatilho, critérios de parada, skills invocadas, memória e guardrails.
- **Fase 2 (Endurecimento):** Aplica as regras de ouro: verificador externo, estados terminais e proibição de auto-avaliação.

### Exemplo-Âncora: `cobertura-auth-loop`
- **Meta:** Atingir 100% de cobertura de testes no diretório `test/auth`.
- **Check Externo:** `npm test -- --coverage` saindo com código 0 e acusando 100% de cobertura nas linhas e ramos.
- **Regra de Avanço:** Uma alteração por volta atacando o arquivo com menor cobertura. Prove o teste (vermelho antes, verde depois).
- **Parada:** Sucesso (100% atingido), Estagnação (2 voltas sem ganho) ou Esgotado (30 turnos).
- **Guardrail:** NUNCA alterar configurações de CI nem apagar testes existentes.

---

## 11. Perguntas de Autoavaliação e Fixação
1. Explique a metáfora do piloto automático e como a Engenharia de Looping altera o papel do desenvolvedor.
2. Por que a pesquisa de Huang et al. (2023) comprova que LLMs não conseguem se autocorrigir confiavelmente sem checks externos?
3. Descreva os 5 níveis da escada de verificação e aponte onde reside a fronteira entre autonomia real e supervisão assistida.
4. O que é a "Dumb Zone" de contexto em modelos de linguagem e como o método Ralph a soluciona?
5. Qual é o Teste de Triagem para decidir se uma demanda deve ser implementada como loop ou apenas como prompt agendado?

# Capítulo 9 — A Jaula do Agente: DevContainers e o Modo YOLO

## 1. Contexto Geral e o Dilema do Modo YOLO
Nos Capítulos 7 e 8, o agente recebeu um arreio (harness) e um piloto automático (loop). Ele está apto a raciocinar, executar e validar autonomamente. Falta o passo mais difícil: **o desenvolvedor tirar as mãos do volante**.

Se você precisa clicar "Sim" e autorizar cada comando no terminal ou edição de arquivo, você não tem um agente autônomo; tem um estagiário hesitante pedindo licença para respirar. A autonomia de verdade — aquela que roda durante a madrugada e entrega Pull Requests testados pela manhã — exige liberar o agente para agir sem supervisão a cada passo. Esse modo chama-se **Modo YOLO (*You Only Live Once* — Você Só Vive Uma Vez)**:
- No Claude Code: `claude --dangerously-skip-permissions`
- No OpenAI Codex: flag `--yolo`
- No Google Antigravity: Aprovação automática contínua de ações.

```
       O DILEMA CRÍTICO DO MODO YOLO:
  [ YOLO na Máquina Física ] ------------> Roleta russa digital com arquivos e credenciais.
                                           Um erro apaga pastas ou vaza segredos.
  [ Sem YOLO (Aprovação Manual) ] --------> Gargalo humano ininterrupto. Perda da alavancagem
                                           que torna os agentes produtivos.
  [ A SOLUÇÃO: A JAULA (DevContainer) ] --> Liberdade total do modo YOLO contida dentro de uma
                                           caixa isolada onde o pior estrago é inofensivo!
```

---

## 2. A Metáfora do Galpão de Trabalho e a Definição de Dev Container

Se você precisa realizar um trabalho que gera poeira tóxica, fagulhas e manchas de tinta, você não faz isso na sala de visitas da sua casa; aluga um galpão industrial preparado. Se o chão sujar ou uma tábua quebrar, nada afeta sua residência. 

Um **Dev Container** é esse galpão para o seu agente:
- Um container Docker com Linux, ferramentas, linguagens e o próprio agente rodando de forma estritamente isolada do sistema operacional do seu computador pessoal.
- O que acontece dentro do container fica dentro do container.
- Se o agente em modo YOLO enlouquecer e rodar um `rm -rf /` destrutivo, o dano fica restrito à caixa descartável. Você joga o container fora e cria outro idêntico em 15 segundos.

### Docker no Desenvolvimento vs. Docker na Produção
É o mesmo Docker com duas finalidades distintas:
- **No Desenvolvimento (Dev Container - Capítulo 9):** O galpão isolado onde humano e agente constroem, testam e erram com segurança.
- **Na Produção (Deploy - Capítulo 10):** A embalagem imutável e padronizada que leva a aplicação pronta para rodar na nuvem.

---

## 3. Anatomia Completa do Arquivo `.devcontainer/devcontainer.json`

O arquivo `devcontainer.json` é a planta baixa da jaula:

```json
{
  "name": "Jaula do Agente de Tarefas",
  "image": "mcr.microsoft.com/devcontainers/universal:6-linux",
  "runArgs": [
    "--cap-add=NET_ADMIN",
    "--cap-add=NET_RAW"
  ],
  "mounts": [
    "source=C:\KEYS,target=/keys,type=bind,readonly"
  ],
  "postCreateCommand": "npm install -g @anthropic-ai/claude-code && sudo apt-get update && sudo apt-get install -y iptables ipset dnsutils jq && git config --global user.name 'sandeco'",
  "postStartCommand": "sudo .devcontainer/init-firewall.sh"
}
```

### Dissecando os Campos Críticos
1. **`image`:** Imagem base universal (Microsoft Linux) contendo Python, Node.js, Git e utilitários de sistema.
2. **`runArgs` (`NET_ADMIN`, `NET_RAW`):** Concede as *capabilities* do kernel Linux necessárias para que o script interno monte e gerencie o firewall. *Você dá a chave das celas ao carcereiro para que ele possa trancar a jaula.*
3. **`mounts` (O Cofre `readonly`):** Monta a pasta de chaves do computador hospedeiro (`C:\KEYS`) dentro do container em `/keys` como **somente leitura**. O agente pode ler para autenticar, mas não consegue editar, sobrescrever nem apagar.
4. **`postCreateCommand` vs. `postStartCommand` (A Diferença Capital):**
   - `postCreateCommand`: Roda **uma única vez** na criação da caixa. Instala ferramentas persistentes (Claude Code, iptables, ipset, identidade Git).
   - `postStartCommand`: Roda **a cada inicialização** do container. Necessário porque regras de firewall do kernel não sobrevivem ao reinício do container e precisam ser reaplicadas sempre!

---

## 4. As Paredes: Firewall com Bloqueio por Padrão (*Default-Deny*)

Um presídio seguro não tenta adivinhar perigos; ele mantém todas as portas trancadas por padrão e libera exclusivamente as visitas autorizadas.

O script `.devcontainer/init-firewall.sh`:
```bash
#!/bin/bash
set -euo pipefail

# 1. Liberação de canais essenciais (para não trancar o administrador do lado de fora)
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT  # DNS para resolução de nomes
iptables -A OUTPUT -p tcp --dport 22 -j ACCEPT  # SSH para o VS Code
iptables -A OUTPUT -o lo -j ACCEPT             # Comunicação interna em localhost

# 2. Criação do conjunto ipset de domínios explicitamente permitidos
ipset create allowed-domains hash:ip 2>/dev/null || ipset flush allowed-domains

ALLOWED_DOMAINS=(
  "api.anthropic.com"       # API do Claude Code
  "registry.npmjs.org"      # Repositório de pacotes Node.js
  "pypi.org"                # Repositório de pacotes Python
  "files.pythonhosted.org"  # Download de wheels do Python
)

for dominio in "${ALLOWED_DOMAINS[@]}"; do
  for ip in $(dig +short A "$dominio"); do
    ipset add allowed-domains "$ip" 2>/dev/null || true
  done
done

# 3. Trancamento Total: Libera somente a lista e BLOQUEIA todo o resto (DROP)
iptables -A OUTPUT -m set --match-set allowed-domains dst -j ACCEPT
iptables -P OUTPUT DROP

# 4. Auto-teste de Verificação Imediata
echo "[Firewall] Testando integridade das grades..."
# Teste A: Deve passar
curl -s -o /dev/null -w "%{http_code}
" https://api.anthropic.com/
# Teste B: Deve travar por timeout (barrado pelo firewall)
curl -s --max-time 3 https://example.com || echo "[Firewall] Bloqueio verificado com sucesso!"
```

### O Maior Poder da Jaula: Eliminar a Exfiltração de Dados
Mesmo que uma dependência maliciosa injete um script espião ou que o agente alucine e tente enviar seu arquivo `.env` para um servidor externo na internet, a conexão é **sumariamente descartada no nível de pacote pelo iptables**.

---

## 5. O Cofre: Gestão Segura de Chaves e Credenciais

A regra inquebrável de segurança: **chaves de API nunca devem ser salvas dentro de imagens de container nem commitadas em código**.

O fluxo do cofre:
1. No computador físico, crie `C:\KEYS\.env` com `ANTHROPIC_API_KEY=...` e `GH_TOKEN=...`.
2. O Dev Container monta a pasta como `readonly` em `/keys`.
3. Na inicialização do terminal do container, carrega-se o arquivo para o ambiente e instrui-se o Git a autenticar:
   ```bash
   set -a; . /keys/.env; set +a
   gh auth setup-git
   ```
4. Se o container for destruído, as chaves continuam 100% intactas na sua máquina física.

---

## 6. O Preso em Modo YOLO: Autonomia com Segurança Real

Dentro da jaula blindada, o comando proibido perde o perigo:
```bash
claude --dangerously-skip-permissions
```
O agente pode criar branches, instalar dependências, rodar suítes de testes, refatorar diretórios inteiros e comitar alterações durante a noite. O pior cenário possível restringe-se ao container descartável.

| Ferramenta | Como Ligar o Modo YOLO | Onde Executar |
| :--- | :--- | :--- |
| **Claude Code** | `claude --dangerously-skip-permissions` | **Exclusivamente dentro do Dev Container** |
| **OpenAI Codex** | Flag `--yolo` | **Exclusivamente dentro do Dev Container** |
| **Google Antigravity** | Habilitar Auto-Aprovação Contínua | **Exclusivamente dentro do Dev Container** |

---

## 7. Defesa em Profundidade: Os Limites da Jaula

Nenhuma ferramenta isolada oferece 100% de segurança. O modelo de **Defesa em Profundidade** organiza cinco camadas protetoras complementares:

```
CAMADA 5: REVISÃO HUMANA FINAL (Audita diffs antes do push para produção)
   ^
CAMADA 4: GIT E COMMITS FREQUENTES (Rede de resgate contra exclusão de código)
   ^
CAMADA 3: COFRE READ-ONLY (Segredos nunca podem ser alterados pelo agente)
   ^
CAMADA 2: FIREWALL DEFAULT-DENY (Impede exfiltração externa e tráfego não autorizado)
   ^
CAMADA 1: DEV CONTAINER DOCKER (Isola o sistema operacional hospedeiro)
```

1. **A Jaula protege o Host, não o Repositório:** Se o agente apagar arquivos do projeto montado, o firewall não interfere. A proteção contra isso é o **Git** (commits antes de cada intervenção, permitindo `git reset --hard`).
2. **A Lista Branca pode ser Traída:** Mantenha a *allowlist* enxuta. Jamais adicione domínios genéricos sem justificativa estrita.
3. **O Fator Humano:** Não cole segredos diretamente em arquivos dentro do container.

> **A Regra de Ouro do Capítulo:**  
> **"Modo YOLO dentro da jaula; revisão humana rigorosa fora dela."**

---

## 8. Perguntas de Autoavaliação e Fixação
1. Qual é o perigo real de acionar o modo YOLO (`--dangerously-skip-permissions`) diretamente no computador hospedeiro?
2. Por que o arquivo `devcontainer.json` necessita de `postCreateCommand` e `postStartCommand` separados?
3. Explique a política de *Default-Deny* aplicada ao script `init-firewall.sh`.
4. Como a técnica de *bind mount* em modo `readonly` protege as chaves de API contra exclusão e vazamento?
5. Apresente as cinco camadas da Defesa em Profundidade de um ambiente de desenvolvimento autônomo.

---

# Matriz Geral de Competências e Síntese de Aplicação

Esta matriz consolida a jornada completa do livro, estruturando os 9 capítulos em uma esteira sequencial que qualquer equipe ou desenvolvedor pode seguir para construir software profissional com IA:

```
+---------------------------------------------------------------------------------------------------+
|                           A ESTEIRA COMPLETA DA ENGENHARIA DE SOFTWARE COM IA                    |
+---------------------------------------------------------------------------------------------------+
| ETAPA 1: MENTALIDADE E PROCESSO (Caps. 1 e 2)                                                     |
| • Sepultar o Vibe Coding; adotar AI Engineering.                                                  |
| • Compreender que código é apenas ingrediente; software é solução durável e testada.              |
| • Requisitos e arquitetura antes de qualquer prompt.                                              |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| ETAPA 2: INFRAESTRUTURA DE CONTROLE E MANUTENÇÃO (Caps. 3 e 4)                                    |
| • Git obrigatório: commits de restauração antes de intervenções do agente; branches e worktrees.  |
| • Arquitetura em Quatro Camadas (Apresentação, Aplicação, Domínio, Infraestrutura).               |
| • Design Patterns estruturais em Python (Singleton, Factory Method, Strategy, Observer, Repo).   |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| ETAPA 3: MODULARIZAÇÃO DE HABILIDADES E ESPECIFICAÇÕES (Caps. 5 e 6)                              |
| • Agent Skills (`SKILL.md`) com frontmatter, triggers, regras e fluxos padronizados.              |
| • Hooks `PreToolUse` e `PostToolUse` para vigilância e auditoria de ações.                        |
| • Spec-Driven Development: os 15 arquivos modulares na pasta `specs/` (PRD, RULES, ARCHITECTURE). |
| • TDD: Red-Green-Refactor como contrato inviolável; o agente nunca altera testes existentes.      |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| ETAPA 4: FRAMEWORKS, CONFIABILIDADE E CONFINAMENTO (Caps. 7, 8 e 9)                               |
| • Escolha do Framework: BMAD (time de personas ágeis) ou Speckit (esteira formal de specs).       |
| • Construção do Agent Harness: verificadores externos, retries determinísticos e failover.        |
| • Engenharia de Looping: automação recursiva com aferidor congelado e parada por estagnação/teto. |
| • A Jaula do DevContainer: firewall Default-Deny e cofre de chaves montado em readonly.          |
| • Liberação do Modo YOLO dentro do container com auditoria humana final antes do deploy.          |
+---------------------------------------------------------------------------------------------------+
```

---
<!-- GOAL_COMPLETE -->
