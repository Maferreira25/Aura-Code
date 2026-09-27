# Glossário do Aura Code e da Aplicação de Validação

> **Status:** APROVADO PELO USUÁRIO EM 2026-09-27  
> **Objetivo:** humanos, agentes, código e documentação usam os mesmos significados.

## 1. Termos do Aura Code

| Termo | Significado simples e preciso |
|---|---|
| Aura Code | Framework completo de desenvolvimento assistido e garantia; não é a aplicação de validação |
| Aura Studio | Interface web local que conduz a jornada visual |
| CLI | Porta de entrada por comandos para automação e usuários técnicos |
| Planta / SDD | Conjunto aprovado de cadernos que define o que será construído antes do código |
| Decisão | Escolha explícita do usuário, com origem e revisão |
| Requisito | Comportamento obrigatório derivado de decisão autorizada |
| Pilha certificada | Conjunto de tecnologias para o qual a jornada completa possui provas vigentes |
| Extensão experimental | Integração ainda sem todas as provas necessárias para garantia oficial |
| Garantia | Propriedade verificada, como isolamento, tipos ou recuperação |
| Gate | Portão que só abre quando garantias obrigatórias estão aprovadas |
| Evidência | Resultado reproduzível, identificado por versão, escopo e hash |
| Artefato determinístico gerado | Lockfile, inventário ou saída compilada produzida por comando e gerador fixos; não é editada manualmente e precisa de hash, auditoria e reprodução |
| `PASS` | Verificação aplicável foi executada com sucesso sobre o alvo declarado |
| `FAIL` | Verificação executou e encontrou violação |
| `NOT_RUN` | Verificação necessária não foi executada; não equivale a aprovação |
| `NOT_APPLICABLE` | Verificação não se aplica, com justificativa explícita |
| `ERROR` | A verificação não conseguiu concluir; não equivale a aprovação |
| Exceção / waiver | Aceitação temporária e registrada de falha não crítica |
| Aura Guard | Porteiro que decide se uma ação pode ser executada |
| Aura Cage | Ambiente isolado com rede negada por padrão |
| Aura Worktree | Cópia de trabalho Git separada da branch ativa |
| Aura Loop | Execução autônoma em iterações pequenas e sem depender de memória longa |
| Skill | Capacidade empacotada com contrato, versão, permissões e arquivos |
| Adaptador | Peça substituível que liga o núcleo a IA, e-mail, CI, editor ou infraestrutura |
| AST | Estrutura real do código usada por verificadores, diferente de procurar texto por expressão regular |
| SBOM | Lista de ingredientes de software presentes em um pacote ou imagem |
| Proveniência | Prova de qual fonte e processo produziram um artefato |
| Rollout gradual | Abertura da nova versão em etapas, observando saúde |
| Rollback | Retorno controlado à versão anterior |
| Telemetria | Dados enviados para entender uso/erros; no Aura Code fica desligada por padrão |
| Observabilidade | Registros, indicadores e rastros usados para operar um sistema |
| AL3 | Nível de garantia comercial escolhido; não é certificação legal nem nível crítico AL4 |

## 2. Analogias oficiais

| Termo técnico | Analogia usada com pessoas leigas |
|---|---|
| Banco de dados | Armário inteligente de fichas |
| Servidor/backend | Cozinha que prepara os pedidos |
| API | Garçom que leva e traz pedidos |
| Interface/frontend | Salão e balcão de atendimento |
| Autenticação | Crachá ou chave do prédio |
| Criptografia | Cofre trancado com segredo |
| Nuvem | Computador alugado em prédio protegido |
| Publicação/deploy | Inauguração e abertura da loja |

## 3. Termos da aplicação de validação

| Termo | Definição inequívoca |
|---|---|
| Aplicação de validação | SaaS separado usado para provar a capacidade do construtor |
| Empresa | Limite principal que isola pessoas e dados de outro cliente |
| Proprietário | Única pessoa que transfere propriedade ou exclui a empresa |
| Administrador | Pessoa que gerencia membros, projetos, configurações e lixeira, sem excluir a empresa |
| Membro | Participante que cria, edita e move tarefas nos projetos permitidos |
| Visitante | Participante que consulta e comenta apenas em projetos convidados |
| Projeto | Espaço ativo ou arquivado, de nome único na empresa, que reúne participantes e tarefas |
| Tarefa | Trabalho com título, descrição opcional, etapa, prioridade, responsável e prazo opcionais e etiquetas |
| Etapa | A fazer, Em andamento, Em revisão ou Concluída |
| Prioridade | Baixa, Média, Alta ou Urgente |
| Comentário | Texto associado a uma tarefa; não contém anexo |
| Menção | Referência a participante autorizado que gera notificação |
| Notificação interna | Aviso exibido dentro do SaaS, sem SMS ou push na primeira versão |
| Lixeira | Área recuperável por 30 dias antes da eliminação definitiva |
| Convite | Entrada individual, revogável, de uso único e válida por sete dias |
| Dispositivo confiável | Dispositivo autorizado a manter sessão por até 30 dias |
| Fila durável | Lista de trabalhos guardada no PostgreSQL até conclusão segura |

## 4. Termos que não podem ser usados como sinônimos

- `Aprovado` não significa `não encontrado`, `não executado` ou `não aplicável`.
- `Pronto para produção` não significa “sem risco”, “serve para qualquer domínio” ou “dispensa responsável humano”.
- `Compatível` não significa `certificado`.
- `Suporte multilíngue` não significa busca textual por padrões em linguagens sem analisador estrutural.
- `Backup` não significa apenas arquivo copiado; precisa restaurar dentro dos objetivos definidos.
- `Enterprise` descreve o perfil documental e operacional provado, não um slogan automático.
