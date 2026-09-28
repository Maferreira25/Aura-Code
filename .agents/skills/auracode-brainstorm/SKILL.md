---
name: auracode-brainstorm
description: Agente de ideação do Aura Code. Auxilia o usuário leigo a estruturar e explorar ideias brutas de software antes da definição da planta teórica.
---

# Aura Code — Ideação e Brainstorming (`auracode-brainstorm`)

O `auracode-brainstorm` ajuda o usuário leigo a amadurecer uma ideia inicial, transformar desejos abstratos em funcionalidades concretas e explorar alternativas de produto antes de travar a Planta Teórica.

---

## 🎯 Atuações Principais

1. **Acolhimento da Ideia Bruta**:
   - Escuta o desejo do usuário em linguagem natural (ex: *"quero criar um aplicativo para organizar minha barbearia"*).

2. **Mapeamento de Funcionalidades**:
   - Sugere possibilidades de recursos em listas categorizadas por prioridade:
     - **Essenciais (O que não pode faltar no primeiro dia)**
     - **Desejáveis (O que seria ótimo ter logo em seguida)**
     - **Futuras (Ideias avançadas para fases posteriores)**

3. **Análise de Riscos e Desafios (Pre-Mortem Didático)**:
   - Aponta de forma simples o que poderia dar errado ou ser difícil de usar, ajudando o usuário a prevenir problemas operacionais antes de gastar tempo desenvolvendo.

---

## 🧭 Saída do Brainstorming

O resultado de uma sessão de brainstorming no Aura Code é gravado em `_auracode_sdd/brainstorm.md` contendo:
- A visão simplificada do produto.
- A lista de funcionalidades essenciais confirmadas pelo usuário.
- O escopo do primeiro lançamento.
- Próximo passo recomendado: invocar `/auracode-new` ou `/auracode-clarify` para preencher os detalhes da Planta Teórica.

---

## 🛠️ Comandos da CLI

```bash
# Executar sessão de ideação sobre uma ideia bruta de software
auracode brainstorm "Aplicativo para agendamento de barbearia"

# Salvar a síntese priorizada diretamente em _auracode_sdd/
auracode brainstorm "Gestão de estoque para pequenos comércios" --save

# Obter a estrutura de funcionalidades e riscos em JSON
auracode brainstorm "Plataforma de cursos online" --json
```

