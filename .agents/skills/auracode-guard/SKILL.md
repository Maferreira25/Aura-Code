---
name: auracode-guard
description: Barreira de proteção ativa em tempo de execução via hooks contra comandos destrutivos e exfiltração de dados.
---

# Aura Code — Proteção Ativa em Tempo de Execução (`auracode-guard`)

O `auracode-guard` avalia chamadas de ferramentas e comandos antes do despacho quando o hook foi instalado e a superfície de execução respeita esse hook. Sem essa integração ativa, não declare que o comando foi interceptado.

---

## 🛡️ Regras de Proteção

1. **Anti-Destruição Operacional:** Bloqueia comandos perigosos como `rm -rf /`, `rmdir /s /q C:\`, formatação de discos, `dd` e `git reset --hard HEAD~10`.
2. **Anti-Exfiltração de Segredos:** Bloqueia tentativas de ler variáveis de ambiente sensíveis, chaves privadas SSH (`id_rsa`) ou credenciais e enviá-las para a internet via `curl`, `wget` ou `nc`.
3. **Anti-Mutação de Banco:** Bloqueia operações não autorizadas de `DROP DATABASE` ou `TRUNCATE TABLE`.

Padrões não reconhecidos ou superfícies que não chamam o hook permanecem fora da garantia. Use `auracode guard check` e confirme a instalação antes de confiar na barreira.

---

## 🛠️ Comandos

```bash
# Auditar comando antes de executar (forma direta)
auracode guard check "git status"

# Auditar comando com identificador de ferramenta (usado por hooks)
auracode guard check --tool run_command --cmd "git status"

# Instalar configuração de hooks no workspace
auracode guard install .
```
