# P1 — Passo a passo no Antigravity IDE atual

## Configuração congelada recomendada

Antes do ensaio, registre:

- Antigravity IDE: versão/build exatos;
- Modelo: `Gemini 3.8 Flash`;
- Variante de raciocínio: `Medium`;
- Rótulo exibido: `Gemini 3.8 Flash Medium`;
- Artifact Review: `Request Review`;
- Terminal Auto Execution: `Request Review`;
- Agent Non-Workspace File Access: `Off`;
- Strict Mode: mesmo estado nos três braços (recomendado `On`, se disponível e estável);
- plugins/MCP/rede: idênticos nos três braços.

Não procure `Planning Mode` ou `Fast Mode` no IDE. Eles não fazem parte deste protocolo atual.

## 1. Valide o pacote

No PowerShell, na raiz do framework:

```powershell
python tools\validate_framework.py
python validation\tools\validate_suite.py
python -m unittest discover -s tests -v
```

## 2. Faça primeiro um ensaio não contabilizado

### A0

```powershell
python validation\tools\harness.py prepare SEC-AUTHZ-001 C:\P1\ensaio-A0
```

Abra somente `C:\P1\ensaio-A0` no Antigravity. Nova conversa. Use `Gemini 3.8 Flash Medium`.

Envie:

> Leia TASK.md e implemente integralmente a tarefa nele descrita.

Avalie:

```powershell
python validation\tools\harness.py evaluate SEC-AUTHZ-001 C:\P1\ensaio-A0 `
  --arm A0 `
  --run-id ensaio-authz-A0 `
  --surface ide `
  --model-family "Gemini 3.8 Flash" `
  --model-display-name "Gemini 3.8 Flash Medium" `
  --reasoning-effort medium `
  --artifact-review request-review `
  --terminal-policy request-review `
  --strict-mode `
  --agent "Antigravity IDE <VERSAO/BUILD>"
```

### A1

Prepare `C:\P1\ensaio-A1`. Não copie `.agents`. Envie a mesma tarefa mais o conteúdo congelado de `validation\prompts\A1-conventional-engineering.md`. Use exatamente o mesmo modelo e configurações de A0.

### A2

Prepare `C:\P1\ensaio-A2`. Copie somente o adapter/framework necessário ao workspace A2, nunca a pasta `validation/` com o scorer.

Exemplo:

```powershell
$RUN="C:\P1\ensaio-A2"
Copy-Item -Recurse -Force ".\adapters\antigravity\.agents" "$RUN\.agents"
Copy-Item -Recurse -Force ".\controls" "$RUN\controls"
Copy-Item -Recurse -Force ".\profiles" "$RUN\profiles"
```

Abra somente A2. Confirme as Workspace Rules. Use exatamente `Gemini 3.8 Flash Medium` e as mesmas políticas de A0/A1.

## 3. Descarte o ensaio

Se os três braços forem avaliados corretamente, não use esses resultados no P1 oficial.

## 4. Congele a pré-registração

Preencha `validation/PREREGISTRATION-TEMPLATE.md` com versão/build, modelo, reasoning, settings, número de repetições e ordem dos braços. Depois de observar resultados oficiais, não altere silenciosamente a pré-registração.

## 5. P1 automatizado

Execute 10 cenários × 3 braços × 3 repetições = 90 runs.

O mesmo `pair-id` liga A0/A1/A2 de uma mesma repetição.

Exemplo:

- `authz-A0-r1 --pair-id authz-r1`
- `authz-A1-r1 --pair-id authz-r1`
- `authz-A2-r1 --pair-id authz-r1`

Alterne a ordem dos braços conforme a pré-registração.

## 6. Cenário de ambiguidade

`INT-AMBIG-001`: 3 braços × 5 repetições. Não revele a política de duplicidade antes de o agente perguntar. Use sempre a resposta scripted do arquivo `EVALUATION.md`.

## 7. Arquitetura longitudinal

`ARC-EVOL-001`: execute a sequência de cinco etapas três vezes por braço, preservando a mesma base dentro de cada sequência.

## 8. Analise

```powershell
python validation\tools\analyze_results.py validation\results
```

Compare A0→A1, A1→A2 e A0→A2, juntamente com custo/tempo/intervenções.
