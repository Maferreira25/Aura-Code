# Fluxos de Trabalho e Diagramas de Sequência (06 — WORKFLOWS)

> **Propósito:** Mapear passo a passo como as interações acontecem no tempo entre atores e sistemas.

---

## 1. Fluxo Principal: Criação e Liquidação de Pedido
```mermaid
sequenceDiagram
    autonumber
    actor Cliente
    participant UI as Interface Web
    participant API as Backend (API)
    participant UC as Caso de Uso (Pedido)
    participant DB as Banco de Dados
    participant Gateway as Gateway de Pagamento

    Cliente->>UI: Clica em "Finalizar Compra"
    UI->>API: POST /api/v1/pedidos
    API->>UC: Executar CriacaoPedido(dados)
    UC->>DB: Validar Estoque & Invariantes
    UC->>Gateway: Solicitar Token de Cobrança
    Gateway-->>UC: Cobrança Aprovada
    UC->>DB: Salvar Pedido com Status PAGO
    UC-->>API: Retornar Pedido Criado
    API-->>UI: 201 Created (comprovante)
    UI-->>Cliente: Exibe tela de confirmação
```

---

## 2. Fluxos Alternativos e Compensatórios
- **Falha no Gateway de Pagamento:** Pedido é marcado como `PENDENTE_PAGAMENTO` e cancelado automaticamente após 15 minutos de inatividade.
