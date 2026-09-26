# Planta Teórica (07) — Nível de Garantia (AL) e Suíte de Testes

> **Status:** APROVADO PELO USUÁRIO  
> **Nível de Garantia Alvo:** AL1 (Local) / AL2 (Uso Interno) / AL3 (Comercial) / AL4 (Crítico)

---

## 1. Nível de Garantia do Aura Code (Assurance Level - AL)

- **AL1 (Ferramenta Local):** Verificação básica de AST, sem código morto ou stubs.
- **AL2 (Aplicação Interna):** Cobertura de testes unitários > 70%, auditoria de vulnerabilidades (`auracode sec`).
- **AL3 (SaaS / Comercial):** Cobertura > 85%, isolamento estrito de camadas Clean Architecture (`auracode arch`), sem vazamento de memória (`auracode leaks`).
- **AL4 (Missão Crítica / Financeiro):** Cobertura > 95%, auditoria de dependências (`auracode deps`), testes adversariais e de mutação.

---

## 2. Critérios de Aceitação para Liberação do Código
- [ ] 100% dos testes automatizados passando sem erros.
- [ ] `auracode slop .` zerado (zero stubs ou dead code).
- [ ] `auracode sec .` zerado (zero falhas de segurança AST).
- [ ] `auracode arch .` zerado (zero violações de camadas).
- [ ] Design visual aprovado com nota excelente pelo usuário.
