# Mapeamento Exaustivo de Casos de Borda (07 — EDGE-CASES)

> **Princípio:** "O código que trata apenas o caminho feliz é um código pronto para falhar em produção."

---

## 1. Matriz de Cenários Adversariais e Casos de Borda

| ID | Cenário de Borda | Risco Associado | Tratamento Determinístico Obrigatório |
| :--- | :--- | :--- | :--- |
| **EC-01** | Concorrência: Dois usuários compram o último item em estoque simultaneamente. | Venda de estoque negativo (*race condition*). | Uso de transação com *pessimistic lock* ou verificação atômica `UPDATE ... WHERE estoque >= qty`. |
| **EC-02** | Timeout de rede durante a requisição ao gateway de pagamento. | Cobrança efetuada sem registro do pedido. | Chave de Idempotência (*Idempotency-Key*) enviada em todas as requisições de pagamento. |
| **EC-03** | Arquivo corrompido ou payload truncado enviado na API. | Falha não tratada com vazamento de stacktrace. | Validação estrita de schema com captura *fail-closed* e retorno 400 amigável. |
| **EC-04** | Banco de dados temporariamente inacessível. | Aplicação trava e consome 100% de CPU. | Circuit Breaker com fallback para resposta 503 e retry exponencial com jitter. |
