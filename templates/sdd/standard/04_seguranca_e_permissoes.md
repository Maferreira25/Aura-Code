# Planta Teórica (04) — Segurança, Autenticação e Permissões

> **Status:** APROVADO PELO USUÁRIO  
> **Analogia:** O Sistema de Crachás e Chaves de Acesso às Salas do Prédio

---

## 1. Perfis de Usuário e Níveis de Acesso

| Perfil / Papel | Descrição Simples | Salas Acessíveis (Permissões) |
| :--- | :--- | :--- |
| **Cliente / Usuário Comum** | Pessoas que usam o produto | Ver seus próprios dados, fazer pedidos |
| **Administrador** | Gestores do sistema | Ver todos os relatórios, alterar configurações |

---

## 2. Proteção de Dados e Criptografia
- **Senhas:** Nunca salvas em texto puro. Criptografadas com algoritmos seguros.
- **Transmissão de Dados:** Criptografada ponta a ponta (HTTPS/TLS).

---

## 3. Prevenção de Ataques Automáticos
- Controle de tentativas de login inválidas.
- Proteção contra injeção de comandos (`auracode sec`).
