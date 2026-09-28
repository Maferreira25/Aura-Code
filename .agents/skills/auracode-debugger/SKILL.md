---
name: auracode-debugger
description: Registrador e corretor de bugs do Aura Code. Triagem de falhas, criação de teste de reprodução e aplicação de correção cirúrgica.
---

# Aura Code — Tratamento de Bugs (`auracode-debugger`)

O `auracode-debugger` gerencia defeitos e comportamentos inesperados no sistema.

---

## 🛠️ Regra da Reprodução Obrigatória

1. **Entrada do Defeito**: Registra o problema relatado pelo usuário no diretório `_auracode_bugs/<id_bug>/bug.md`.
2. **Teste Quebrando Primeiro**: Escreve um teste automatizado que reproduz a falha exatamente como relatada. O teste DEVE falhar antes de qualquer alteração no código.
3. **Correção Cirúrgica**: Aplica o menor ajuste necessário no código da aplicação até o teste passar.
4. **Validação AST**: Roda `auracode audit` e os testes afetados para procurar regressões no escopo suportado. Resultado limpo não prova ausência universal de defeitos.

---

## 🛠️ Comandos da CLI

```bash
# Registrar defeito e gerar teste automatizado de reprodução
auracode debug bug_001 --desc "Token JWT não valida expiração" --create-test

# Verificar se o teste de reprodução está falhando conforme o esperado
auracode debug bug_001 --verify-repro

# Verificar se a correção fez o teste passar e causou zero regressões
auracode debug bug_001 --verify-fix
```

