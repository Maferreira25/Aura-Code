---
name: auracode-cage
description: Configura e verifica um DevContainer com política de rede Default-Deny. Use para reduzir a superfície de exfiltração, sem tratar a configuração como prova automática de isolamento.
---

# Aura Code — Sandbox DevContainer Hermético (`auracode-cage`)

O `auracode-cage` cria arquivos para um DevContainer Linux com `iptables` em **Default-Deny**. A configuração reduz tráfego de saída não autorizado, mas só conta como proteção ativa depois que `auracode cage verify` comprovar o ambiente em execução.

---

## 🔒 Princípios de Segurança

1. **Default-Deny verificável:** A política deve negar saídas por padrão e liberar somente destinos declarados em `allowed-domains.txt`; falha de verificação interrompe o fluxo.
2. **Capacidades Mínimas:** Utiliza apenas permissões necessárias de rede (`NET_ADMIN`, `NET_RAW`) para gerenciar as regras de firewall.
3. **Autonomia ainda limitada:** O contêiner é uma camada de redução de risco, não uma garantia absoluta contra vazamento, fuga de sandbox ou configuração incorreta.

---

## 🛠️ Comandos

```bash
# Inicializar ambiente .devcontainer com firewall
auracode cage init .

# Verificar se o ambiente atual está em sandbox hermético
auracode cage verify
```
