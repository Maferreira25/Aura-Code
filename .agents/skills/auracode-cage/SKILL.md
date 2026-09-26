---
name: auracode-cage
description: Sandbox DevContainer hermético com firewall Default-Deny para modo YOLO seguro e proteção contra injeção de prompt indireta.
---

# Aura Code — Sandbox DevContainer Hermético (`auracode-cage`)

O `auracode-cage` cria e valida ambientes DevContainer Linux com `iptables` configurado em **Default-Deny**, bloqueando todo tráfego de saída não autorizado e neutralizando ataques de exfiltração de dados por injeção de prompt indireta.

---

## 🔒 Princípios de Segurança

1. **Default-Deny:** Nenhuma conexão externa sai do contêiner, exceto se o domínio estiver explicitamente em `allowed-domains.txt`.
2. **Capacidades Mínimas:** Utiliza apenas permissões necessárias de rede (`NET_ADMIN`, `NET_RAW`) para gerenciar as regras de firewall.
3. **Modo YOLO Seguro:** Permite que agentes executem ferramentas de forma autônoma sem risco de vazamento de código proprietário ou credenciais.

---

## 🛠️ Comandos

```bash
# Inicializar ambiente .devcontainer com firewall
auracode cage init .

# Verificar se o ambiente atual está em sandbox hermético
auracode cage verify
```
