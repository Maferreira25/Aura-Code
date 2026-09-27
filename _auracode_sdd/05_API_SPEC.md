# Contratos de Comunicação

> **Status:** APROVADO PELO USUÁRIO EM 2026-09-27  
> **Padrão:** REST, JSON UTF-8 e OpenAPI 3.1

## 1. Regras comuns

- Contrato OpenAPI é fonte verificável entre o salão (interface) e a cozinha (servidor).
- Rotas de negócio usam `/api/v1` e aceitam apenas campos declarados.
- Sessão é transportada em cookie seguro, inacessível a scripts e protegido contra envio entre sites.
- Toda escrita aceita `Idempotency-Key` quando repetição puder duplicar efeitos.
- Toda resposta inclui `request_id`; erros não expõem pilha, SQL, caminhos ou segredo.
- Paginação usa `cursor` e `limit` com limite máximo definido pelo contrato gerado.
- Datas e horas trafegam em ISO 8601 UTC; a interface apresenta o fuso do perfil.

## 2. Formato de erro

```json
{
  "error": {
    "code": "TASK_VERSION_CONFLICT",
    "message_key": "errors.task_version_conflict",
    "request_id": "uuid",
    "field_errors": []
  }
}
```

`message_key` possui tradução equivalente; a mensagem apresentada não é usada como regra de programa.

## 3. API local do Aura Studio

| Método e rota | Finalidade | Aprovação exigida |
|---|---|---|
| `GET /studio/v1/projects` | Listar projetos locais | Não |
| `POST /studio/v1/projects` | Criar/registrar workspace | Confirmação de local |
| `GET/POST /studio/v1/projects/{id}/decisions` | Ler e responder decisões | Escolha explícita |
| `GET /studio/v1/projects/{id}/specifications` | Ler planta e rastreabilidade | Não |
| `POST /studio/v1/projects/{id}/specifications/approve` | Aprovar revisão exata | Sim, sempre |
| `POST /studio/v1/projects/{id}/build/iterations` | Propor/executar iteração | Conforme risco |
| `POST /studio/v1/projects/{id}/audits` | Executar garantias | Não destrutiva |
| `GET /studio/v1/projects/{id}/evidence` | Consultar provas | Não |
| `POST /studio/v1/projects/{id}/preview` | Iniciar prévia local | Confirmação se abrir rede |
| `POST /studio/v1/projects/{id}/releases` | Preparar/publicar | Aprovação humana obrigatória |
| `POST /studio/v1/support-bundles` | Montar pacote revisável | Envio nunca automático |

A API local escuta apenas interface de loopback por padrão, exige segredo de sessão efêmero e rejeita origem desconhecida.

## 4. API da aplicação de validação

### Acesso e perfil

`POST /auth/register`, `POST /auth/login`, `POST /auth/logout`, `POST /auth/recover`, `POST /auth/reset`, `POST /auth/mfa/setup`, `POST /auth/mfa/verify`, `GET/DELETE /sessions`, `GET/PATCH /me`, `POST /me/export`, `DELETE /me`.

Respostas de login e recuperação não revelam se um e-mail alheio está cadastrado. Operações sensíveis aceitam confirmação recente.

### Empresas, membros e convites

`GET/POST /organizations`, `GET/PATCH/DELETE /organizations/{org}`, `GET /organizations/{org}/members`, `PATCH/DELETE /organizations/{org}/members/{member}`, `POST/GET/DELETE /organizations/{org}/invitations`, `POST /invitations/{token}/accept`.

Transferência e exclusão de empresa são exclusivas do proprietário e têm contratos separados de confirmação.

### Projetos

`GET/POST /organizations/{org}/projects`, `GET/PATCH /projects/{project}`, `POST /projects/{project}/archive`, `GET/PUT/DELETE /projects/{project}/members`.

A listagem aceita busca por nome/descrição, estado, membro, cursor e ordenação autorizada.

### Tarefas, etiquetas e comentários

`GET/POST /projects/{project}/tasks`, `GET/PATCH /tasks/{task}`, `POST /tasks/{task}/trash`, `POST /tasks/{task}/restore`, `GET/POST /tasks/{task}/comments`, `PATCH/DELETE /comments/{comment}`, `GET/POST/PATCH/DELETE /projects/{project}/labels`.

Busca e filtros de tarefa: título/descrição, etapa, responsável, prioridade, etiqueta e prazo. Atualização envia a versão lida; conflito retorna `409`.

### Notificações, privacidade e segurança

`GET /notifications`, `POST /notifications/{id}/read`, `POST /notifications/read-all`, `GET /privacy/export-status/{id}`, `GET /security-events` (somente proprietário/administrador).

## 5. Integrações externas

| Integração | Contrato |
|---|---|
| Provedor de IA | Capacidades negociadas, tempo limite, cancelamento, uso e divulgação registrados |
| E-mail | Porta substituível; ambiente local usa caixa capturadora, produção recebe adaptador configurado |
| Git | Checkpoint, diff, identidade e recuperação; sem envio remoto implícito |
| Docker/Kubernetes | Build e rollout por comandos reproduzíveis e manifesto auditado |
| CI | Motor local; primeiro adaptador gera GitHub Actions |
| Editores | Integração opcional por protocolo público; nenhuma lógica de negócio exclusiva |

## 6. Compatibilidade

- Mudança incompatível exige nova versão principal da API.
- Mudanças aditivas permanecem na mesma versão e são testadas contra clientes anteriores suportados.
- O cliente gerado para Next.js deriva do OpenAPI e falha na CI se o contrato estiver divergente.
