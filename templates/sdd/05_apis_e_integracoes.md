# Planta Teórica (05) — APIs e Integrações

> **Status:** APROVADO PELO USUÁRIO  
> **Analogia:** O Garçom que Transmite os Pedidos do Balcão para a Cozinha

---

## 1. Contratos de Comunicação das Telas com o Servidor

### Endpoint: `POST /api/v1/auth/login`
- **Descrição Simples:** Envia e-mail e senha para receber o crachá de acesso.
- **Entrada (Pedido enviado):**
  ```json
  {
    "email": "usuario@exemplo.com",
    "senha": "senha_digitada"
  }
  ```
- **Saída Sucesso (Resposta 200 OK):**
  ```json
  {
    "sucesso": true,
    "token_acesso": "token_criptografado",
    "usuario": { "id": "123", "nome": "Maria" }
  }
  ```

---

## 2. Tratamento Didático de Erros (Zero Erro Cíptico)
- Todos os erros retornados pela API devem conter mensagens amigáveis em linguagem simples para o usuário final.
