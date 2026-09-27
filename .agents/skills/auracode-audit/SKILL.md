---
name: auracode-audit
description: Executor da auditoria baseada em evidências do Aura Code. Relata cada garantia como PASS, FAIL, NOT_RUN, NOT_APPLICABLE ou ERROR, sem nota geral.
---

# Aura Code — Auditoria e Garantia de Qualidade (`auracode-audit`)

O `auracode-audit` executa `auracode audit` e apresenta somente garantias realmente verificadas. Um alvo ausente, vazio ou sem contrato necessário nunca recebe aprovação.

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

Ao término, apresente uma matriz acessível para o usuário leigo:

- **PASS:** a garantia foi executada e não encontrou violação dentro do escopo declarado.
- **FAIL:** a garantia encontrou uma violação.
- **NOT_RUN:** faltou alvo, ferramenta, contrato ou evidência para executar.
- **NOT_APPLICABLE:** a garantia não se aplica ao alvo e a justificativa está registrada.
- **ERROR:** a execução falhou e não pode ser tratada como aprovação.

Nunca gere média ou pontuação geral. Mostre método, escopo, quantidade de arquivos e achados de cada garantia.
