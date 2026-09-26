# Especificação de Contratos de API (05 — API-SPEC)

> **Protocolo:** REST / JSON / OpenAPI 3.1  
> **Formato de Dados:** UTF-8 JSON estrito  

---

## 1. Padrão de Respostas da API

### Sucesso (`200 OK`, `201 Created`):
```json
{
  "status": "success",
  "data": { ... },
  "metadata": { "timestamp": "2026-09-26T00:00:00Z" }
}
```

### Erro Padronizado (`4xx`, `5xx`):
```json
{
  "status": "error",
  "error": {
    "code": "VAL_INVALID_INPUT",
    "message": "Mensagem clara e segura para o cliente",
    "details": []
  }
}
```

---

## 2. Catálogo de Endpoints

### `POST /api/v1/pedidos`
- **Descrição:** Criação de novo pedido de compra.
- **Autenticação:** Bearer Token (JWT).
- **Request Body:**
```json
{
  "cliente_id": "usr-123",
  "itens": [
    { "produto_id": "prod-456", "quantidade": 2 }
  ]
}
```
- **Respostas:**
  - `201 Created`: Pedido criado com sucesso.
  - `400 Bad Request`: Payload malformado.
  - `422 Unprocessable Entity`: Violação de regra de negócio (ex: estoque insuficiente).
