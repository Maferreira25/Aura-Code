# Planta Teórica (03) — Modelo de Dados e Armazenamento

> **Status:** APROVADO PELO USUÁRIO  
> **Analogia:** O Armário de Fichas e Arquivos Inteligentes do Sistema

---

## 1. Visão Conceitual (Linguagem Simples)
*Explicação para o usuário de como as informações ficam guardadas em "gavetas virtuais".*

- **Gaveta 1 (`usuarios`):** Guarda nome, e-mail, senha protegida e foto de perfil.
- **Gaveta 2 (`pedidos`):** Guarda o histórico de compras, data, valor total e cliente associado.

---

## 2. Eschema Técnico do Banco de Dados

### Tabela: `usuarios`
| Campo | Tipo | Obrigatório | Chave | Descrição |
| :--- | :--- | :--- | :--- | :--- |
| `id` | UUID / INT | SIM | PK | Identificador único da ficha |
| `nome` | VARCHAR(255) | SIM | - | Nome completo |
| `email` | VARCHAR(255) | SIM | UNIQUE | E-mail de acesso |
| `senha_hash` | VARCHAR(512) | SIM | - | Senha criptografada |

---

## 3. Políticas de Armazenamento e Limpeza
- **Retenção de Dados:** [Definido com o usuário na fase de briefing]
- **Backup:** [Definido com o usuário na fase de briefing]
