# Relatório Histórico de Resultados P1 — Snapshot Piloto

**ID do experimento:** P1-IDE-GEMINI-3.8-FLASH-MED-001  
**Data do snapshot histórico:** 2026-09-11  
**Versão do framework naquele snapshot:** 0.1.1-draft  
**Superfície:** Antigravity IDE 2.5.5  
**Modelo:** Gemini 3.8 Flash Medium

> **IMPORTANTE — P1 FORMAL ATUAL: INCOMPLETO**
>
> Este arquivo preserva os 36 runs históricos já coletados. Ele **não** representa a conclusão formal do protocolo P1 atualmente congelado.
>
> O protocolo vigente exige 114 execuções totais:
> - 90 runs automatizados: 10 cenários × 3 braços × 3 repetições;
> - 15 runs de ambiguidade: 3 braços × 5 repetições;
> - 9 sequências arquiteturais: 3 braços × 3 sequências.
>
> O snapshot atual contém 36/114 execuções: 30/90 automatizadas, 3/15 de ambiguidade e 3/9 de arquitetura. Portanto, faltam 78 execuções.
>
> A fonte de verdade para completude é validation/tools/validate_experiment_evidence.py e a matriz de execução é validation/tools/p1_matrix.py. Nenhuma alegação de eficácia comparativa ou conclusão formal de P1 deve ser feita enquanto formal_p1_complete for false.

---

## 1. O que este snapshot histórico demonstra

Os 36 resultados armazenados em validation/results demonstram que:

1. o harness consegue preparar e avaliar os cenários já executados;
2. os testes públicos/protegidos e a coleta de resultados funcionaram para esse conjunto;
3. os três braços A0/A1/A2 foram exercitados uma vez em cada cenário histórico;
4. a infraestrutura experimental é operacional para smoke/pilot;
5. os resultados históricos apresentaram efeito teto e, portanto, não demonstraram vantagem comparativa do A2.

Eles não demonstram:

- conclusão formal do P1 congelado atual;
- eficácia geral do AuraCode;
- superioridade de A2 sobre A0/A1;
- validade externa;
- resistência à contaminação;
- prontidão para uma versão estável 1.0.

---

## 2. Resultados históricos dos 36 runs

### Métrica consolidada do snapshot

~~~text
Runs: 36
A0: QS 12/12 = 1.000
A1: QS 12/12 = 1.000
A2: QS 12/12 = 1.000

Diferença pareada A2 - A0: 0.000
~~~

Esse resultado constitui um **efeito teto**: os três braços obtiveram sucesso total no conjunto já executado. Por isso, o snapshot não fornece sinal discriminativo suficiente para atribuir benefício causal ao framework.

---

## 3. Cenários já executados uma vez por braço

| Categoria | Cenários/Sequências | A0 | A1 | A2 |
| --- | ---: | ---: | ---: | ---: |
| Automatizados | 10 | 10 | 10 | 10 |
| Ambiguidade | INT-AMBIG-001 r1 | 1 | 1 | 1 |
| Arquitetura longitudinal | ARC-EVOL-001 seq1 | 1 | 1 | 1 |
| **Total** | 12 unidades experimentais por braço | **12** | **12** | **12** |

Os arquivos JSON correspondentes permanecem em validation/results para rastreabilidade.

---

## 4. Estado formal do protocolo atual

O protocolo congelado exige:

- automatizados: 90 runs;
- ambiguidade: 15 runs;
- arquitetura longitudinal: 9 runs;
- total: 114 runs.

Estado do snapshot preservado:

- automatizados: 30/90;
- ambiguidade: 3/15;
- arquitetura: 3/9;
- total: 36/114;
- faltantes: 78.

O comando de referência é:

~~~text
python validation/tools/validate_experiment_evidence.py validation/results --require-complete
~~~

Enquanto esse comando não retornar conclusão formal, o P1 deve ser tratado como INCOMPLETE.

A fila determinística de runs restantes pode ser obtida com:

~~~text
python validation/tools/p1_matrix.py validation/results --missing-only
~~~

---

## 5. Limite de interpretação

Os resultados existentes podem ser usados para:

- testar o harness;
- validar a mecânica do benchmark;
- identificar problemas metodológicos;
- estimar carga operacional inicial;
- orientar o restante do P1.

Não devem ser usados como:

- prova de eficácia do framework;
- prova de superioridade de A2;
- certificação de segurança;
- evidência suficiente para 1.0;
- substituto de P2/P3/P4.

O gate de maturidade do AuraCode deve permanecer bloqueado enquanto os critérios obrigatórios estiverem UNKNOWN ou FAIL.

---

## 6. Próxima ação experimental

Executar somente os runs MISSING da matriz P1, mantendo congelados:

- modelo e variante;
- versão/superfície do Antigravity;
- políticas de Artifact Review e Terminal Auto Execution;
- Strict Mode;
- orçamento e permissões;
- isolamento de sessão;
- prompts congelados de A0/A1/A2;
- ordem registrada na matriz.

Nenhum resultado faltante deve ser preenchido por inferência, simulação retrospectiva ou duplicação de um run anterior.
