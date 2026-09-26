---
name: auracode-audit
description: Executor da suíte de auditoria de qualidade e segurança AST do Aura Code. Avalia o projeto em 12 dimensões determinísticas.
---

# Aura Code — Auditoria e Garantia de Qualidade (`auracode-audit`)

O `auracode-audit` executa a verificação estática determinística no código do sistema usando a suíte nativa `auracode`.

---

## 🔍 Comandos Executados na Auditoria

Ao ser invocado, executa as seguintes verificações na raiz da aplicação:

```bash
auracode ambiguity .   # Mede ambiguidades restantes nas especificações
auracode slop .        # Caça stubs, código morto e exceções engolidas
auracode leaks .       # Caça vazamentos de arquivos e sockets sem fechar
auracode types .       # Verifica tipagem estrita e proíbe uso descontrolado de Any
auracode tests .       # Audit a integridade dos testes e detecta testes vazios
auracode sec .         # Detecta vetores de injeção (eval/exec, SQLi, shell=True)
auracode arch .        # Valida fronteiras Clean Architecture (Domain isolado)
auracode deps .        # Verifica dependências no PyPI contra pacotes alucinados
auracode diff .        # Garante que as mudanças foram cirúrgicas (< 500 linhas)
```

---

## 📊 Relatório Final em Linguagem Simples

Ao término da verificação, o `auracode-audit` gera um resumo acessível para o usuário leigo:
- **Pontuação de Saúde do Projeto (0 a 100)**
- **Lista de Aprovações (O que está perfeito)**
- **Pontos de Atenção (O que precisa de correção antes da entrega)**
