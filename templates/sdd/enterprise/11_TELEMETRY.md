# Telemetria, Observabilidade e Alertas (11 — TELEMETRY)

> **Propósito:** Monitoramento em tempo real da saúde da aplicação, performance e detecção antecipada de anomalias.

---

## 1. Padrão de Logs Estruturados (JSON)
Todo log deve ser emitido em formato JSON contendo contexto de rastreabilidade:
```json
{
  "timestamp": "2026-09-26T00:00:00.123Z",
  "level": "INFO",
  "service": "pedidos-service",
  "trace_id": "trc-abc-123",
  "span_id": "spn-456",
  "event": "pedido_criado",
  "pedido_id": "ped-789",
  "valor": 199.90,
  "duracao_ms": 42
}
```

---

## 2. Métricas de Serviço (Método RED)
- **Rate (Taxa de Requisições):** Quantidade de requisições por segundo (RPS) por endpoint.
- **Errors (Taxa de Erros):** Porcentagem de respostas HTTP 5xx em relação ao total.
- **Duration (Latência / Duração):** Histogramas nos percentis p50, p95 e p99.

---

## 3. Políticas de Alarme
- **Alarme Crítico (P1):** Taxa de erro 5xx > 1% por mais de 2 minutos consecutivos $ightarrow$ Notificação imediata.
- **Alarme de Degradação (P2):** Latência p95 > 1.500ms por 5 minutos $ightarrow$ Alerta para a equipe.
