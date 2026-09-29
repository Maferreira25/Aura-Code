---
name: auracode-agents-help
description: Catálogo explicativo dos agentes do Aura Code com analogias didáticas para pessoas leigas.
---

# Aura Code — Catálogo de Agentes Especiais (`auracode-agents-help`)

O **Aura Code** organiza seu trabalho utilizando um "time de especialistas virtuais". Cada agente possui responsabilidade e limites declarados; nenhum deles substitui as provas exigidas pelo fluxo.

---

## 👥 Conheça o Time Virtual do Aura Code

1. **`auracode` (O Maestro / Orquestrador Geral)**:
   - *Analogia*: É como o maestro da orquestra ou o gerente geral da obra que recebe você e indica qual especialista deve cuidar de cada etapa.
   - *Função*: Apresenta os comandos disponíveis e direciona para o fluxo seguro correto.

2. **`auracode-new` (O Arquiteto de Projetos)**:
   - *Analogia*: É o arquiteto principal que entrevista você sobre suas necessidades e desenha a Planta Teórica Completa em `_auracode_sdd/`.
   - *Função*: Conduz o briefing sem jargões e cria a especificação completa de telas, regras e dados antes de qualquer código existir.

3. **`auracode-clarify` (O Entrevistador Didático)**:
   - *Analogia*: É o desenhista detalhista que senta com você para esclarecer cada detalhe da casa usando perguntas simples e comparações do cotidiano.
   - *Função*: Elimina ambiguidades e preenche lacunas com perguntas de múltipla escolha e comparações didáticas.

4. **`auracode-brainstorm` (O Mestre de Ideias)**:
   - *Analogia*: É o consultor de novos negócios que ajuda você a rabiscar ideias e colocar as intenções no papel antes de fechar o projeto.
   - *Função*: Transforma vontades abstratas em uma lista organizada de funcionalidades sem tomar decisões sozinho.

5. **`auracode-forward` (O Construtor Fiel à Planta)**:
   - *Analogia*: É o construtor experiente que levanta as paredes seguindo rigorosamente a planta aprovada, sem inventar nada por conta própria.
   - *Função*: Constrói a aplicação em Clean Architecture a partir de `_auracode_sdd/`, cumprindo todas as garantias estáticas de qualidade.

6. **`auracode-audit` (O Fiscal e Perito da Obra)**:
   - *Analogia*: É o fiscal da Defesa Civil e o perito técnico com equipamentos de raio-X que inspecionam as paredes, vigas e encanamentos.
   - *Função*: Executa as garantias aplicáveis (slop, leaks, sec, types, arch, tests) e relata evidências explícitas (`PASS`, `FAIL`, etc.) sem notas inventadas.

7. **`auracode-debugger` (O Técnico Especialista de Diagnóstico)**:
   - *Analogia*: É o encanador/eletricista chamado para encontrar a causa exata de uma infiltração, reproduzindo a falha com teste antes de consertar.
   - *Função*: Identifica defeitos, cria testes automatizados que reproduzem o erro e aplica correções cirúrgicas sem efeitos colaterais.

8. **`auracode-refactor` (O Restaurador de Estrutura)**:
   - *Analogia*: É o restaurador que moderniza a fiação e o encanamento sem alterar a posição de nenhuma lâmpada ou tomada da casa.
   - *Função*: Melhora arquitetura, tipagem e organização preservando rigorosamente o comportamento coberto por testes.

9. **`auracode-guard` (O Segurança de Portaria)**:
   - *Analogia*: É a guarita com cancela automática que checa a autorização e proíbe a entrada de caminhões com carga perigosa no condomínio.
   - *Função*: Intercepta comandos de terminal e ferramentas via hooks para bloquear comandos destrutivos e tentativas de vazamento em tempo de execução.

10. **`auracode-worktree` (A Sala de Ensaios Isolada)**:
    - *Analogia*: É um ateliê temporário separado onde o artista faz os protótipos e testes para não sujar a sala de estar principal.
    - *Função*: Cria pastas de trabalho físicas isoladas via Git Worktree para que experimentos dos agentes nunca poluam a branch ativa do usuário.

11. **`auracode-cage` (A Cabine de Vidro Blindada)**:
    - *Analogia*: É uma cabine de biossegurança hermética onde cientistas manuseiam amostras perigosas com fluxo de ar 100% controlado.
    - *Função*: Configura e audita DevContainers herméticos com firewall Default-Deny (bloqueio total de rede externa) para neutralizar exfiltrações.

12. **`auracode-loop` (O Ciclo Autônomo com Freio de Emergência)**:
    - *Analogia*: É uma linha de produção automatizada com sensores a cada metro e botão de parada de emergência caso uma peça saia torta.
    - *Função*: Executa iterações autônomas sob a Arquitetura Ralph (anti-dumb-zone e anti-reward-hacking) com verificação contínua de garantias AST.

13. **`auracode-debate` (A Mesa Redonda de Especialistas)**:
    - *Analogia*: É uma reunião fechada entre consultores de áreas diferentes em uma sala acústica para chegarem à melhor recomendação sem cansar o cliente.
    - *Função*: Realiza discussões multi-agente em subagentes isolados para refinar arquiteturas sem poluir o contexto principal.

14. **`auracode-adversary` (O Advogado do Diabo / Auditor Contestador)**:
    - *Analogia*: É o perito contratado especificamente para tentar encontrar qualquer brecha, defeito oculto ou falso teste na casa antes da compra.
    - *Função*: Desafia propostas de arquitetura buscando ativamente falhas de segurança, vazamentos, stubs e oráculos de teste viciados.
