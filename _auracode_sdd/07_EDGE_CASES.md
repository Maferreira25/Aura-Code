# Casos de Borda e Falhas Determinísticas

> **Status:** APROVADO PELO USUÁRIO EM 2026-09-27  
> **Regra:** nenhum caso abaixo pode terminar em aprovação silenciosa, perda invisível ou acesso ampliado.

## 1. Aura Code

| ID | Situação | Tratamento obrigatório |
|---|---|---|
| AC-EC-001 | Caminho alvo não existe | Encerrar com `ERROR`; zero garantias aprovadas |
| AC-EC-002 | Projeto não possui arquivos compatíveis | `NOT_RUN` com explicação; publicação bloqueada |
| AC-EC-003 | Verificador não suporta a linguagem | `NOT_APPLICABLE` ou `NOT_RUN`, nunca `PASS` |
| AC-EC-004 | Verificador trava ou excede tempo | Preservar saída segura, marcar `ERROR` e bloquear gate dependente |
| AC-EC-005 | Evidência foi alterada | Hash diverge; invalidar a evidência e reexecutar |
| AC-EC-006 | README promete capacidade sem prova | Verificação documental falha |
| AC-EC-007 | Versões CLI/skill incompatíveis | Instalação/execução recusada com caminho de correção |
| AC-EC-008 | Arquivo obrigatório da skill ausente | `doctor` falha e a skill não aparece como utilizável |
| AC-EC-009 | Tradução ausente ou variável divergente | Build falha; fallback não mascara conteúdo crítico |
| AC-EC-010 | Segredo detectado no contexto de IA | Envio bloqueado e evento local registrado sem copiar o segredo |
| AC-EC-011 | Conteúdo externo manda ignorar regras | Instrução descartada; dado continua disponível apenas como referência |
| AC-EC-012 | Destino de rede não autorizado | Conexão bloqueada antes do envio |
| AC-EC-013 | Resposta da IA é truncada/inválida | Nenhuma alteração aplicada; tentativa pode ser refeita com novo registro |
| AC-EC-014 | Patch excede 500 linhas | Dividir em iterações ou pedir aprovação de mudança de plano; não aplicar inteiro |
| AC-EC-015 | Usuário cancela durante operação | Parar no limite seguro, preservar checkpoint e indicar estado exato |
| AC-EC-016 | Atualização falha após migrar estado | Restaurar backup e binário anterior, mantendo diagnóstico |
| AC-EC-017 | SQLite e Markdown divergem | Bloquear avanço e apresentar revisões; nunca escolher silenciosamente |
| AC-EC-018 | Exceção vence durante release | Gate volta a falhar antes da publicação |
| AC-EC-019 | Aprovação pertence a revisão anterior | Exigir nova aprovação para a revisão atual |
| AC-EC-020 | Telemetria sem consentimento | Nenhum envio; somente registros locais |

## 2. Aplicação de validação

| ID | Situação | Tratamento obrigatório |
|---|---|---|
| APP-EC-001 | ID válido pertence a outra empresa | Resposta indistinguível de recurso inacessível; evento de segurança sem revelar existência |
| APP-EC-002 | Último proprietário tenta sair | Rejeitar até transferir propriedade ou excluir a empresa |
| APP-EC-003 | Convite usado, revogado, expirado ou de outro e-mail | Rejeitar sem criar vínculo |
| APP-EC-004 | Duas pessoas criam mesmo nome de projeto | Restrição atômica permite uma e retorna conflito à outra |
| APP-EC-005 | Duas pessoas editam a mesma tarefa | Versão antiga recebe `409`; interface oferece recarregar/comparar |
| APP-EC-006 | Responsável é removido do projeto | Tarefa fica sem responsável e participantes autorizados são notificados |
| APP-EC-007 | Menção aponta para pessoa sem acesso | Rejeitar menção e não enviar notificação |
| APP-EC-008 | Prazo atravessa fusos/horário de verão | Persistir UTC e calcular apresentação no fuso do perfil |
| APP-EC-009 | Trabalho de notificação repete | Chave de idempotência evita duplicação; novas tentativas são registradas |
| APP-EC-010 | E-mail externo está indisponível | Pedido principal permanece válido; fila tenta novamente e mostra estado seguro |
| APP-EC-011 | Link de recuperação é solicitado várias vezes | Apenas o mais recente permanece válido; resposta não confirma cadastro |
| APP-EC-012 | Código de recuperação de MFA é reutilizado | Rejeitar; cada código é de uso único |
| APP-EC-013 | Dispositivo confiável é revogado | Próxima tentativa perde a sessão e exige autenticação completa |
| APP-EC-014 | Tarefa na lixeira recebe atualização | Rejeitar alteração comum; apenas restauração ou purga autorizada |
| APP-EC-015 | Purga ocorre enquanto restauração é pedida | Bloqueio transacional define um único vencedor e informa resultado |
| APP-EC-016 | Exportação inclui outra empresa | Teste de isolamento falha e entrega é bloqueada |
| APP-EC-017 | Banco fica temporariamente indisponível | Falhar fechado, limitar novas tentativas e retornar serviço indisponível |
| APP-EC-018 | Rollout novo falha na migração | Interromper liberação e manter versão anterior compatível |
| APP-EC-019 | Backup existe mas não restaura | Gate de recuperação falha; não conta como backup válido |
| APP-EC-020 | Comentário contém HTML/script | Tratar como texto seguro; nunca executar conteúdo |

## 3. Condições de carga e abuso

- Listagens sempre paginadas e com ordenação permitida.
- Login, recuperação, convites, comentários, buscas e exportações recebem limites por usuário e origem.
- Limites excedidos retornam mensagem segura e tempo de nova tentativa.
- Tamanho máximo dos campos e limites de página serão definidos no contrato técnico antes da implementação de cada endpoint, sem criar novos campos de negócio.
- Operações em lote são limitadas e retomáveis; nenhuma transação longa bloqueia o armário inteiro.
