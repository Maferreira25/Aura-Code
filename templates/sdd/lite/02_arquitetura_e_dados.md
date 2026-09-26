# Caderno 02 — Arquitetura Limpa e Modelo de Dados (Perfil Lite — AL2)

> **Perfil Lite:** Define a separação de responsabilidades (Clean Architecture) e a organização dos dados para MVPs e microsserviços.

---

## 1. Organização das Camadas (Clean Architecture Simplificada)

O código deve respeitar a hierarquia clássica de camadas isoladas:

- **`domain/` (O Coração do Negócio):**
  - Entidades de dados fundamentais e regras imutáveis.
  - *Invariante:* Proibido importar frameworks, bibliotecas externas, banco de dados ou HTTP.
- **`usecases/` (Os Fluxos de Execução):**
  - Orquestra os passos de cada ação solicitada pelo usuário.
  - Depende apenas de `domain/` e de interfaces/protocolos abstratos.
- **`adapters/` (Os Tradutores):**
  - Conversores de entrada/saída (controladores REST, presenters, adaptadores de repositório).
- **`infrastructure/` (O Mundo Externo):**
  - Banco de dados SQLite/PostgreSQL, clientes HTTP externos, leitura de arquivos e variáveis de ambiente.

---

## 2. Modelo de Dados e Armazenamento (O "Armário Inteligente")

Descreva as entidades centrais e seus campos:

### Entidade: `[Nome da Entidade 1]`
- `id`: Identificador único (UUID ou Inteiro autoincremental).
- `nome`: Nome descritivo (Texto obrigatório).
- `status`: Estado atual (`ativo`, `inativo`, `pendente`).
- `criado_em`: Data e hora de criação automática.

### Entidade: `[Nome da Entidade 2]`
- `id`: Identificador único.
- `referencia_id`: Chave que conecta com a Entidade 1.
- `valor`: Dado numérico ou textual.

---

## 3. Interfaces e Portas Externas (APIs)

| Rota / Endpoint | Método | Quem pode chamar | O que faz em linguagem simples |
| :--- | :--- | :--- | :--- |
| `/api/itens` | `GET` | Visitante, Membro | Lista todos os itens ativos da vitrine |
| `/api/itens` | `POST` | Membro, Admin | Adiciona um novo item no armário |
| `/api/itens/{id}` | `DELETE`| Admin | Remove o item selecionado do sistema |

---

## 4. Regras de Isolamento e Segurança de Dados

- **Proteção de Segredos:** Nenhuma senha ou chave de API deve ser colocada no código fonte. Devem vir de variáveis de ambiente (`.env`).
- **Conexões com Context Managers:** Todas as conexões e arquivos abertos devem usar `with` para evitar vazamentos de memória (auditado por `auracode leaks`).
- **Prevenção de Injeção de SQL:** Proibido concatenar strings em consultas. Usar sempre parâmetros tipados (`?` ou `:param`).
