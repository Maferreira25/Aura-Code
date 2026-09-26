---
name: auracode-guard
description: Barreira de proteção ativa em tempo de execução via hooks contra comandos destrutivos e exfiltração de dados.
---

# Aura Code — Proteção Ativa em Tempo de Execução (`auracode-guard`)

O `auracode-guard` atua como um escudo protetor (*Fail-Closed Safety Guardrail*) interceptando chamadas de ferramentas e comandos de terminal antes do despacho ao sistema operacional.

---

## 🛡️ Regras de Proteção

1. **Anti-Destruição Operacional:** Bloqueia comandos perigosos como `rm -rf /`, `rmdir /s /q C:\`, formatação de discos, `dd` e `git reset --hard HEAD~10`.
2. **Anti-Exfiltração de Segredos:** Bloqueia tentativas de ler variáveis de ambiente sensíveis, chaves privadas SSH (`id_rsa`) ou credenciais e enviá-las para a internet via `curl`, `wget` ou `nc`.
3. **Anti-Mutação de Banco:** Bloqueia operações não autorizadas de `DROP DATABASE` ou `TRUNCATE TABLE`.

---

## 🛠️ Comandos

```bash
# Auditar comando antes de executar
auracode guard check --tool run_command --cmd "git status"

# Instalar configuração de hooks no workspace
auracode guard install .
```
