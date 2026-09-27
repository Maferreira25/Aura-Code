# Segurança, Privacidade e Modelo de Ameaças

> **Status:** APROVADO PELO USUÁRIO EM 2026-09-27  
> **Postura:** confiança zero, privilégio mínimo e falha fechada

## 1. Ativos prioritários

Segredos de provedores, código do usuário, prompts, decisões, evidências, assinatura de releases, dados pessoais, sessões, dados de cada empresa e backups.

## 2. Fronteiras de confiança

1. Navegador local ↔ servidor local do Aura Studio.
2. Aura Code ↔ provedor de IA.
3. Agente ↔ sistema operacional e ferramentas.
4. Workspace ↔ conteúdo externo e dependências.
5. Interface Next.js ↔ API FastAPI.
6. API/trabalhador ↔ PostgreSQL e provedor de e-mail.
7. CI ↔ registro de artefatos e Kubernetes.

## 3. Ameaças e controles

| Ameaça | Controle obrigatório | Prova |
|---|---|---|
| Pessoa ou serviço falsificado | senha derivada resistente, MFA TOTP, sessão rotacionada, assinatura de artefato | testes de autenticação e assinatura |
| Alteração de planta/evidência | hashes, histórico somente de acréscimo, revisão aprovada imutável | teste de adulteração |
| Negação de ação | histórico encadeado de ações sensíveis | verificador de integridade |
| Vazamento à IA/log/telemetria | minimização, detector de segredo, redação, prévia e consentimento | testes canário |
| Injeção em prompt externo | separar dados de instruções, negar ferramentas e rede por padrão | suíte adversarial |
| Injeção SQL/comando/script | validação estrita, consultas parametrizadas, execução sem shell, saída codificada | SAST + testes dinâmicos |
| Abuso entre empresas | `organization_id`, política no banco e autorização no caso de uso | testes negativos cruzados |
| Escalada de papel | matriz central, negação padrão, confirmação recente | testes por ação/papel |
| Negação de serviço | limites, paginação, timeouts, filas, backoff e limites de recursos | testes de carga/abuso |
| Dependência comprometida | lock, hash, origem, SBOM, scanner e assinatura | relatório de cadeia |

## 4. Segredos e criptografia

- Chaves de IA locais ficam no chaveiro do sistema; CI usa variáveis protegidas.
- Nenhum segredo é persistido no SQLite, Markdown, JSON, Git ou diagnóstico.
- Tráfego externo e de produção usa TLS; dados persistidos usam criptografia do ambiente e proteção específica para segredo MFA.
- Senhas, tokens de convite, recuperação, sessão e códigos de recuperação são guardados apenas em forma derivada quando não precisarem ser recuperados.
- Rotação invalida material anterior de forma controlada.

## 5. Autorização da aplicação

- Autorização é feita no servidor para cada ação, não confiada à interface.
- Papel de empresa e participação no projeto são ambos conferidos.
- Visitante lê e comenta apenas em projetos convidados.
- Somente proprietário transfere ou exclui empresa.
- Somente proprietário/administrador gerencia membros, projetos e lixeira.
- Políticas no PostgreSQL oferecem segunda barreira contra acesso cruzado.

## 6. Privacidade e LGPD

- Coletar apenas nome de exibição, e-mail, idioma e fuso no perfil.
- Inventário liga cada dado a finalidade, retenção e acesso.
- Usuário dispõe de acesso, correção, exportação e exclusão.
- Telemetria do Aura Code é desligada por padrão e opcional; nunca contém código, prompts ou segredos.
- Pacote de suporte é local, mostra prévia e só é enviado após autorização separada.
- Esses controles apoiam a LGPD, mas não constituem parecer ou certificação jurídica.

## 7. Agente, rede e sandbox

- Aura Guard decide antes da execução e falha fechado.
- Aura Cage opera como usuário sem privilégios, com rede negada por padrão e lista de destinos autorizados.
- Aura Worktree isola alterações da branch ativa.
- Comandos destrutivos, mudança de credencial, publicação e exfiltração precisam de autorização humana.
- Conteúdo lido de site, issue, dependência, log ou arquivo é não confiável; não muda a política.

## 8. Segurança de release

- Build reproduzível a partir de fonte e lockfiles revisados.
- SBOM e proveniência acompanham cada artefato.
- Imagem e pacote são assinados; implantação verifica a assinatura.
- Vulnerabilidade crítica explorável bloqueia release.
- Exceção não crítica expira e não altera a evidência original.

## 9. Categorias nunca dispensáveis

Segredo exposto, isolamento entre empresas, bypass de autenticação/autorização, execução remota, injeção confirmada, assinatura inválida, backup irrecuperável e migração com risco não aprovado.
