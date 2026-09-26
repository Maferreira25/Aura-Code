# Modelagem de Ameaças e Segurança (08 — SECURITY)

> **Metodologia:** STRIDE / OWASP Top 10 / NIST SSDF  
> **Nível de Confiança:** Zero Trust  

---

## 1. Matriz de Ameaças STRIDE
- **Spoofing (Falsificação):** Tokens JWT assinados com algoritmo assimétrico (RS256) e expiração curta (15 minutos).
- **Tampering (Adulteração):** Validação de integridade de payload com schemas rígidos; zero `eval()` ou `exec()`.
- **Repudiation (Repúdio):** Trilha de auditoria criptograficamente encadeada para todas as mutações financeiras.
- **Information Disclosure (Vazamento):** Mascaramento de dados sensíveis (PII) em logs; zero credenciais em código.
- **Denial of Service (Negação de Serviço):** Rate limiting por IP/Token (máximo 100 requisições por minuto por rota).
- **Elevation of Privilege (Elevação de Privilégio):** Controle de acesso baseado em papéis (RBAC) com validação no backend.

---

## 2. Política de Sanitização e Proteção contra Injeção
- Toda entrada do usuário deve ser validada por schema de tipos estritos antes do processamento.
- Consultas a banco de dados devem utilizar exclusivamente consultas parametrizadas (*prepared statements*).
