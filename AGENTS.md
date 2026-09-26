# Aura Code Framework — AI Software Assurance & Lay-User Pair Programming

> Framework de Desenvolvimento Orientado a Garantias, Pair Programming com Pessoas Leigas e Engenharia de Software Orientada a Especificação.

## Como usar o Aura Code

Use o fluxo adequado no chat:

- `auracode` ou `auracode-new` — iniciar um projeto do zero ou nova funcionalidade através de entrevista em linguagem simples para leigos
- `auracode-clarify` — realizar briefing interativo e eliminar dúvidas/ambiguidades com analogias
- `auracode-forward` — implementar a aplicação estritamente a partir da planta teórica aprovada em `_auracode_sdd/`
- `auracode-audit` — executar a suíte estática de garantia AST (slop, leaks, sec, types, arch, tests)
- `auracode-guard` — proteção ativa em tempo de execução via hooks contra comandos destrutivos e vazamentos (`auracode guard`)
- `auracode-worktree` — isolamento físico de branches em pastas temporárias para agentes (`auracode worktree`)
- `auracode-cage` — sandbox DevContainer com firewall Default-Deny para modo YOLO seguro (`auracode cage`)
- `auracode-loop` — runner autônomo baseado na Arquitetura Ralph com anti-dumb-zone e anti-reward-hacking (`auracode loop`)
- `auracode-debugger` — registrar e triar problemas com testes que reproduzem a falha
- `auracode-refactor` — melhorar a qualidade e arquitetura do código sem alterar regras de negócio
- `auracode-agents-help` — consultar o catálogo completo de agentes e habilidades

---

## Regras Fundamentais e Não-Negociáveis do Aura Code

### 1. Tolerância Zero a Presunções (Zero-Presumption Directive)
- A IA está **estritamente proibida** de presumir, inferir ou decidir qualquer regra de negócio, comportamento de interface, modelo de dados, permissão ou caso de erro.
- Todas as decisões devem vir do usuário. Se faltar qualquer informação — por menor ou mais simples que seja —, o sistema DEVE pausar e perguntar ao usuário antes de prosseguir.
- Quando o usuário não souber responder a termos técnicos, o sistema deve apresentar **opções estruturadas com comparações cotidianas** (ex: *"Opção A: Como uma gaveta destravada... / Opção B: Como um cofre com segredo..."*), permitindo uma decisão informada pelo usuário.

### 2. Paradigma da Planta da Casa (House Blueprint First)
- Nenhuma linha de código de aplicação, pasta de código ou arquivo de programação deve ser gerado antes que a **estrutura teórica completa do software** esteja 100% pronta e revisada.
- Toda a arquitetura (backend, frontend, modelo de dados, APIs, segurança, design system, requisitos e nível de garantia AL1-AL4) deve ser especificada em arquivos markdown no diretório `_auracode_sdd/`.
- Apenas após a apresentação do resumo ao usuário e sua **autorização/aprovação explícita** é que a geração de arquivos de código pode ser iniciada.

### 3. Protocolo de Comunicação Não-Técnica para Leigos
- O sistema DEVE usar linguagem simples, evitando jargões técnicos sem explicação.
- Use sempre analogias do mundo físico:
  - *Banco de Dados* $\rightarrow$ *"Armário ou arquivo inteligente de dados"*.
  - *Backend / Servidor* $\rightarrow$ *"A cozinha do restaurante que prepara os pedidos"*.
  - *API* $\rightarrow$ *"O garçom que leva o pedido da mesa até a cozinha e traz a resposta"*.
  - *Frontend / Interface* $\rightarrow$ *"A vitrine e o balcão da loja onde o cliente interage"*.
  - *Autenticação / Token* $\rightarrow$ *"O crachá ou chave de acesso ao prédio"*.

### 4. Garantia Estática e Controle de Qualidade (AST Zero Trust)
- Todo código gerado pelo Aura Code deve cumprir os verificadores estáticos AST da CLI `auracode`:
  - Zero dead code / stubs (`auracode slop`)
  - Zero vazamento de recursos/arquivos (`auracode leaks`)
  - Zero vulnerabilidades de injeção (`auracode sec`)
  - Type hints estritos (`auracode types`)
  - Isolamento de camadas Clean Architecture (`auracode arch`)
  - Diffs cirúrgicos limitados a 500 linhas por iteração (`auracode diff`)

### 5. Política de Escrita e Isolamento de Diretórios
Por padrão, artefatos de garantia e especificações devem residir nas pastas gerenciadas do framework:
`_auracode_sdd/`, `_auracode_bugs/`, `_auracode_docs/`, `_auracode_refactor/`, `_auracode_forward/`.
Em projetos novos (greenfield) liberados pelo usuário, o código da aplicação será scaffolded sob Clean Architecture (`domain/`, `usecases/`, `adapters/`, `infrastructure/`, `tests/`).

### 6. Contenção Ativa, Isolamento Físico e Autonomia Controlada
- **Aura Guard (`auracode guard`):** Intercepta comandos de terminal e ferramentas via `.agents/hooks.json` antes do despacho ao sistema operacional (*fail-closed* contra comandos destrutivos e vazamentos).
- **Aura Worktree (`auracode worktree`):** Isola experimentos e implementações do agente em pastas físicas paralelas para que arquivos intermediários nunca sujem a branch ativa do desenvolvedor.
- **Aura Cage (`auracode cage`):** Constrói e audita DevContainers herméticos com firewall *Default-Deny* (bloqueia 100% de conexões externas não autorizadas, neutralizando ataques de exfiltração por prompt injection indireto em modo YOLO).
- **Aura Loop (`auracode loop`):** Executa iterações autônomas sob a Arquitetura Ralph (Geoffrey Huntley): execuções *stateless* sem degradação de contexto ("Dumb Zone" >100k tokens), verificadas continuamente pelos 5 níveis de garantias AST e protegidas por freio de emergência contra *Reward Hacking*.


