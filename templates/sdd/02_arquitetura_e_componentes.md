# Planta Teórica (02) — Arquitetura e Estrutura de Módulos

> **Status:** APROVADO PELO USUÁRIO  
> **Estilo de Arquitetura:** Clean Architecture (Domain, UseCases, Adapters, Infrastructure)

---

## 1. Explicação Analógica da Arquitetura (Para Leigos)

- **Vitrine e Recepção (Frontend/UI):** Responsável por exibir as informações de forma bonita e amigável.
- **Garçom de Mensagens (API Controller):** Transmite os pedidos das telas para o processador central.
- **Cérebro de Negócios (Domain & UseCases):** Onde ficam guardadas as regras de cálculo e regras da empresa.
- **Armário de Arquivos (Banco de Dados / Persistência):** Onde as informações são armazenadas em segurança.

---

## 2. Divisão Teórica de Módulos e Pacotes

```text
app/
├── domain/            # Regras puras e modelos principais
├── usecases/          # Fluxos de execução e tarefas do sistema
├── adapters/          # Conversores e apresentadores de dados
├── infrastructure/    # Banco de dados, servidor web e interface de usuário
└── tests/             # Suíte de testes automatizados de garantia
```

---

## 3. Isolamento de Dependências
- O `domain` NÃO conhece e NÃO importa nenhuma biblioteca externa de banco de dados ou tela.
