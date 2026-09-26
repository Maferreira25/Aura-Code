# Diretrizes e Governança para Agentes de IA (14 — AGENTS)

> **Framework:** Aura Code Protocol  
> **Regra Suprema:** Tolerância Zero a Presunções (Zero-Presumption Directive)  

---

## 1. Limites de Atuação e Permissões
- O agente tem permissão para:
  - Ler e consultar especificações em `_auracode_sdd/`.
  - Criar e editar arquivos de código dentro das camadas Clean Architecture autorizadas.
  - Executar testes automatizados e linters AST locais.
- O agente NUNCA tem permissão para:
  - Alterar arquivos de teste para mascarar falhas de código (*Anti-Reward Hacking*).
  - Executar comandos destrutivos do SO ou comandos forçados de Git (`git push --force`).
  - Assumir comportamentos de negócio não descritos explicitamente nesta especificação.

---

## 2. Protocolo de Pair Programming com Leigos
- Usar analogias do mundo físico ao comunicar problemas ou dúvidas.
- Apresentar opções estruturadas em formato de menu de decisão quando surgir qualquer ambiguidade.
