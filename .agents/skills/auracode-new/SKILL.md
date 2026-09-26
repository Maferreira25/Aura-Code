---
name: auracode-new
description: Orquestrador de novos projetos e funcionalidades no Aura Code. Conduz a entrevista de briefing sem jargões para pessoas leigas e constrói a Planta Teórica Completa em _auracode_sdd/ antes de gerar código.
---

# Aura Code — Novo Projeto & Planta Teórica (`auracode-new`)

O `auracode-new` guia a criação de um sistema do zero ou uma nova funcionalidade completa, focado em pessoas leigas no mundo da tecnologia.

---

## 🔒 Regras Obrigatórias de Execução

1. **Tolerância Zero a Presunções**:
   - NUNCA assuma nem infira nada. Se o usuário disse "quero um aplicativo de vendas", NÃO decida sozinho se terá login com Google, qual o banco de dados ou como será o botão.
   - Faça perguntas simples para CADA detalhe. Se o usuário não souber escolher, apresente opções com comparações cotidianas.

2. **Paradigma da Planta da Casa (House Blueprint Paradigm)**:
   - Nenhuma pasta de aplicação ou código de programação (Python, JS, HTML, SQL) pode ser gerado nesta etapa.
   - O resultado desta etapa é **estritamente o conjunto de 7 especificações teóricas** no diretório `_auracode_sdd/`.

3. **Protocolo de Comunicação Didática**:
   - Use apenas linguagem cotidiana. Evite jargões como "REST API", "PostgreSQL", "JWT", "ORM", "Docker", "Middleware" sem explicá-los através de analogias simples do dia a dia.

---

## 🛠️ Etapas do Fluxo `auracode-new`

### Etapa 1: Briefing Interativo (Entrevista Didática)
Conduza uma conversa por rodadas, perguntando:
1. **Objetivo e Público**: Quem vai usar a aplicação e qual problema ela resolve?
2. **Funcionalidades Principais**: O que a pessoa precisa conseguir fazer tela por tela?
3. **Informações e Dados**: Quais informações precisam ser guardadas (ex: nomes, fotos, valores, datas)? (Use a analogia do *Armário Inteligente*).
4. **Regras e Segurança**: Quem pode ver ou alterar o quê? (Use a analogia do *Crachá de Acesso*).
5. **Aparência e Estilo**: Quais cores, sensações ou estilo visual o usuário prefere para a interface? (Use a analogia da *Decoração da Loja*).

Se restar QUALQUER dúvida, faça mais rodadas até obter 100% de clareza.

---

### Etapa 2: Gerar a Planta Teórica Completa (`_auracode_sdd/`)
Assim que todas as respostas forem consolidadas, crie os 7 documentos de especificação no diretório `_auracode_sdd/`:

1. `_auracode_sdd/01_visao_geral_e_negocio.md`:
   - Propósito do produto, público-alvo, regras de negócio e critérios de sucesso sem termos técnicos.

2. `_auracode_sdd/02_arquitetura_e_componentes.md`:
   - Módulos teóricos da aplicação (Painel Visual, Processador de Pedidos, Guardião de Dados).

3. `_auracode_sdd/03_modelo_de_dados_e_armazenamento.md`:
   - Estrutura de dados conceitual (entidades, atributos e conexões) e especificação técnica em banco de dados.

4. `_auracode_sdd/04_seguranca_e_permissoes.md`:
   - Perfis de acesso, criptografia, proteção de dados e autenticação.

5. `_auracode_sdd/05_apis_e_integracoes.md`:
   - Contratos formais de comunicação (o garçom que conecta a interface com o servidor), rotas, entradas e saídas.

6. `_auracode_sdd/06_interface_e_design_system.md`:
   - Telas do sistema, fluxo de navegação, paleta de cores harmoniosa, tipografia, componentes visuais e animações.

7. `_auracode_sdd/07_nivel_de_garantia_e_testes.md`:
   - Nível de Garantia (AL1 para protótipos locais, AL2 para uso interno, AL3 para comercial, AL4 para crítico) e suíte de testes de aceitação.

---

### Etapa 3: Apresentação do Resumo e Portão de Aprovação
Ao concluir a criação dos 7 arquivos da Planta Teórica:
1. Apresente um resumo executivo em linguagem simples para o usuário.
2. Explique que a "planta da casa" está 100% desenhada e revisada.
3. Solicite a **autorização explícita** do usuário para prosseguir para a fase de construção de código (`/auracode-forward`).
