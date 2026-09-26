# Plano de Testes e Estratégia TDD (09 — TEST-PLAN)

> **Metodologia:** Test-Driven Development (TDD) — Ciclo Red-Green-Refactor  
> **Regra de Ouro:** O agente que desenvolve código NUNCA tem permissão para alterar arquivos de teste.  

---

## 1. Pirâmide de Testes e Metas de Cobertura
```mermaid
graph BT
    E2E[Testes Ponta a Ponta: 10%]
    Integration[Testes de Integração: 20%]
    Unit[Testes Unitários: 70%]
```

- **Cobertura Mínima de Linhas:** 90% no Domínio e Casos de Uso.
- **Integridade dos Testes:** Zero testes vácuos (todo teste DEVE conter asserções explícitas `assert` / `self.assert*`).

---

## 2. Matriz de Testes Obrigatórios
| ID | Alvo | Cenário Testado | Tipo | Resultado Esperado |
| :--- | :--- | :--- | :--- | :--- |
| **T01** | `Pedido.calcular_total()` | Lista de itens válidos com desconto | Unitário | Valor total correto com precisão decimal |
| **T02** | `Pedido.calcular_total()` | Lista vazia de itens | Borda | Lança exceção `ValidationError` |
| **T03** | `CriacaoPedidoUseCase` | Saldo insuficiente no pagamento | Integração | Pedido rejeitado, estoque não alterado |
