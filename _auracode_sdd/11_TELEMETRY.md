# Observabilidade, Diagnóstico e Alertas

> **Status:** APROVADO PELO USUÁRIO EM 2026-09-27  
> **Padrão:** OpenTelemetry e formatos abertos; nenhum fornecedor obrigatório

## 1. Separação essencial

- **Observabilidade da aplicação:** informações operacionais necessárias para manter o serviço, configuradas pelo responsável da implantação.
- **Diagnóstico do Aura Code:** fica local por padrão; envio anônimo é opcional e depende de consentimento.
- **Evidência de garantia:** registro reproduzível de verificação, não telemetria de uso.

Nenhuma dessas categorias pode ser usada para transportar fonte, prompts, segredo ou conteúdo pessoal desnecessário.

## 2. Registros estruturados

Campos permitidos: horário UTC, nível, serviço, ambiente, versão, evento estável, `request_id`, `trace_id`, duração, resultado, código de erro seguro e identificadores opacos necessários.

Campos proibidos: senha, token, cookie, chave, corpo integral de requisição, prompt, código-fonte, comentário, descrição de tarefa, e-mail em claro e pilha de erro devolvida ao usuário.

Redação acontece antes da gravação. Testes com valores-canário comprovam que o material proibido não aparece.

## 3. Indicadores

### Aura Code

- duração e resultado de entrevista, geração, verificação, build e publicação;
- número de garantias por estado, sem converter em nota geral;
- falhas de skill, incompatibilidade, rollback e restauração;
- quantidade/categoria de dados proposta para envio à IA, sem conteúdo.

### Aplicação de validação

- taxa, erros e duração de requisições;
- disponibilidade mensal com meta de 99,9%;
- profundidade, idade e falhas da fila durável;
- conexões e saturação do banco;
- resultado de backup, idade do último ponto recuperável e exercício de restauração;
- sucesso/falha de rollout e rollback.

A planta não promete um número de latência ainda não autorizado. Percentis p50, p95 e p99 serão medidos e exibidos; uma meta de latência só poderá virar promessa pública após baseline e aprovação registrada.

## 4. Alertas

| Gravidade | Exemplo | Resposta |
|---|---|---|
| P1 crítica | vazamento/isolamento suspeito, serviço indisponível, corrupção, restauração impossível | aviso imediato, contenção, responsável acionado e procedimento P1 |
| P2 alta | consumo acelerado do orçamento de 99,9%, fila parada, backup atrasado | atendimento prioritário e mitigação documentada |
| P3 moderada | degradação de latência, aumento de novas tentativas, capacidade próxima do limite | investigação planejada |
| P4 informativa | tendência sem impacto atual | registrar e revisar |

Alertas usam janelas para evitar ruído e agrupam sintomas do mesmo incidente.

## 5. Painéis mínimos

1. Saúde da jornada Aura Code: entrevista → planta → construção → auditoria → release.
2. Garantias por estado, idade da evidência e exceções próximas do vencimento.
3. Saúde da aplicação: disponibilidade, erros, latência, tráfego e saturação.
4. Fila e integrações externas.
5. Backup/restauração e objetivo de 15 minutos/1 hora.
6. Segurança: autenticação anormal, negações entre empresas e ações administrativas.

## 6. Diagnóstico opcional do Aura Code

- Desativado na instalação.
- Consentimento mostra finalidade, campos, destino e retenção.
- Identificador é aleatório e renovável; não deriva de máquina, conta ou projeto.
- Usuário pode retirar consentimento a qualquer momento.
- Pacote de suporte é gerado localmente, passa por redação, exibe prévia e exige confirmação de envio.

## 7. Retenção

- Registros locais do Aura Studio são configuráveis e limitados por tamanho/tempo.
- Eventos de segurança da aplicação ficam por um ano.
- Métricas não carregam dados pessoais.
- Traces usam amostragem e nunca incluem conteúdo proibido.
