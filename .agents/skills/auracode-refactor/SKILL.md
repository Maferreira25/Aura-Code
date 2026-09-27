---
name: auracode-refactor
description: Melhora arquitetura, tipagem e estrutura dentro de um escopo aprovado, preservando o comportamento coberto por contratos e testes executados.
---

# Aura Code — Refatoração e Melhoria de Código (`auracode-refactor`)

O `auracode-refactor` limpa e melhora o código da aplicação sem alterar como o sistema funciona para o usuário.

---

## 🎯 Foco de Atuação

- **Eliminação de Slop**: Remove funções que não estão sendo chamadas ou códigos esquecidos.
- **Tipagem Estrita**: Adiciona type hints em funções que estavam genéricas.
- **Isolamento de Camadas**: Verifica pelo contrato de arquitetura que regras do negócio não dependam diretamente de bibliotecas visuais ou de banco de dados.
- **ROI Real**: Foca a refatoração onde realmente traz ganho de segurança ou desempenho, sem refatorar código que já funciona perfeitamente.
