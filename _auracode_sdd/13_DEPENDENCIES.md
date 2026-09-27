# Dependências, Empacotamento e Cadeia de Suprimentos

> **Status:** APROVADO PELO USUÁRIO EM 2026-09-27  
> **Licença do framework:** MIT

## 1. Tecnologias autorizadas

| Área | Escolha aprovada | Papel |
|---|---|---|
| Núcleo Aura Code | Python compatível com os sistemas suportados | CLI, orquestração e verificadores |
| Studio e interface gerada | Next.js/TypeScript | salão web responsivo |
| Servidor gerado | FastAPI/Python | cozinha e contrato OpenAPI |
| Dados de produção | PostgreSQL | armário inteligente e fila durável |
| Estado local | SQLite + Markdown + JSON | estado, especificação e contratos |
| Ambiente | Docker/DevContainer | reprodução e isolamento |
| Produção | Kubernetes | publicação portátil |
| CI inicial | GitHub Actions | primeiro adaptador de automação |
| Observabilidade | OpenTelemetry | registros, métricas e rastros abertos |

Bibliotecas concretas e versões só entram quando a implementação demonstrar necessidade, licença compatível e auditoria. Esta planta não inventa pacotes ainda não avaliados.

## 2. Contrato de pacote oficial

O artefato instalável deve conter:

- módulos Python importáveis e entrada `auracode`;
- servidor e ativos compilados do Aura Studio;
- todas as skills oficiais com manifestos;
- templates micro, lite, standard e enterprise;
- catálogos português/inglês;
- schemas e políticas;
- metadados de versão únicos;
- verificadores e dados necessários em runtime;
- licença, aviso, SBOM, assinatura e proveniência.

Um teste instala a distribuição construída em ambiente vazio, sem acesso ao checkout, e executa `auracode doctor`, criação de planta, auditoria mínima e abertura do Studio.

## 3. Contrato de skill

Cada skill declara em manifesto versionado:

`id`, versão, descrição PT/EN, versão mínima/máxima do núcleo, entradas, saídas, permissões, ferramentas, arquivos, hashes, garantias produzidas e pontos de falha.

Regras:

- arquivo ausente, hash divergente ou faixa incompatível impede ativação;
- permissão não declarada é negada;
- atualização incompatível exige nova versão principal;
- skill externa não recebe confiança de skill oficial por localização ou nome;
- catálogo mostra origem e estado de verificação.

## 4. Seleção e verificação

- Dependência deve existir no registro oficial e corresponder exatamente ao nome esperado.
- Lockfiles fixam versões e hashes por plataforma.
- Lockfiles e ativos compilados são artefatos determinísticos gerados: não entram na contagem de 500 linhas de código/configuração escritos, mas falham fechados sem gerador e versão fixos, comando normalizado, entradas autorizadas, hash, auditoria e reprodução limpa. Edição manual invalida a prova.
- Licença e manutenção são registradas.
- Scanner de vulnerabilidade roda na proposta e continuamente.
- Dependência crítica abandonada ou vulnerável abre decisão de substituição.
- Atualizações são propostas por mudança pequena, passam pelos mesmos gates e nunca entram automaticamente em produção.

## 5. SBOM, assinatura e proveniência

- Cada pacote e imagem recebe inventário legível por máquina.
- Proveniência liga fonte, revisão, workflow e artefato.
- Assinatura é verificada na instalação e implantação.
- Artefato sem prova de origem é rejeitado.

## 6. Provedores substituíveis

IA, e-mail, CI, observabilidade, registro de imagem e infraestrutura usam portas. O primeiro adaptador pode ser documentado e testado, mas contratos de domínio não importam SDK proprietário.

## 7. Atualização do Aura Code

- Canal informa versão, compatibilidade, mudanças e assinatura.
- Usuário autoriza; backup precede migração.
- Falha reativa versão anterior.
- Estado novo incompatível não é gravado sem caminho de restauração comprovado.
