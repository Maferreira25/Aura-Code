# Design System e Interface

> **Status:** APROVADO PELO USUÁRIO EM 2026-09-27  
> **Diretriz:** sóbrio, responsivo, explicável e WCAG 2.2 AA

## 1. Princípios

1. Linguagem cotidiana primeiro; detalhe técnico fica disponível sem ser escondido.
2. Estado nunca depende somente de cor, animação ou ícone.
3. Ação sensível mostra consequência, alvo e caminho de recuperação antes da confirmação.
4. Teclado e leitor de tela executam toda a jornada.
5. Computador, tablet e celular usam a mesma aplicação web responsiva; não há aplicativo nativo inicial.

## 2. Identidades separadas

### Aura Studio

- Base grafite neutra com destaque azul-violeta.
- Aparência de ferramenta confiável, sem simular que resultados incertos são definitivos.
- Provas, riscos e limitações têm a mesma importância visual que ações de construção.

### Aplicação de validação

- Azul profundo e cinzas neutros.
- Não exibe a marca Aura Code como se fosse parte do construtor.
- Demonstra que aplicativos gerados podem ter identidade independente.

As cores finais são tokens semânticos (`background`, `surface`, `text`, `primary`, `success`, `warning`, `danger`, `focus`) com variantes claro, escuro e alto contraste. Cada combinação precisa passar contraste WCAG 2.2 AA antes de ser aceita.

## 3. Tipografia e movimento

- Fonte de sistema para evitar download obrigatório e melhorar desempenho.
- Texto comum nunca menor que 16 px na configuração padrão.
- Escala tipográfica relativa, zoom até 200% sem perda de conteúdo.
- Movimento curto e funcional; `prefers-reduced-motion` elimina transições não essenciais.
- Foco de teclado espesso, contrastante e nunca removido.

## 4. Estrutura responsiva

| Largura prática | Comportamento |
|---|---|
| Celular | uma coluna; navegação recolhível; tabelas viram cartões/listas; ações primárias permanecem acessíveis |
| Tablet | uma ou duas colunas conforme conteúdo; painéis secundários recolhíveis |
| Computador | navegação lateral, área principal e painel contextual opcional |

Nenhuma ação essencial depende de passar o mouse. Arrastar tarefas possui alternativa por menu e teclado.

## 5. Telas do Aura Studio

| Tela | Conteúdo essencial |
|---|---|
| Projetos | estado, última atividade, próxima ação e saúde do ambiente |
| Entrevista | uma decisão por vez, explicação, opções, dúvidas restantes e progresso real |
| Decisões | histórico, origem, impacto e revisão atual |
| Planta | 15 cadernos, mudanças, rastreabilidade e botão de aprovação da revisão |
| Construção | etapa atual, arquivos afetados, risco, testes e checkpoint |
| Auditoria/Evidências | matriz por garantia, prova, escopo, falha e correção; sem nota geral |
| Prévia | aplicação local, dados de exemplo e estado dos serviços |
| Publicação | checklist, ambiente, risco, responsável, rollout e retorno |

## 6. Telas da aplicação de validação

Entrada/recuperação/MFA; seleção de empresa; projetos; quadro/lista de tarefas; detalhe de tarefa e comentários; notificações; membros/convites; perfil/sessões/privacidade; configurações e histórico de segurança conforme papel.

## 7. Componentes obrigatórios

- Botão, link, campo, seleção, diálogo e menu com nomes acessíveis.
- Banner de estado para sucesso, alerta, falha, não executado e não aplicável.
- Cartão de decisão com comparação cotidiana e detalhes expansíveis.
- Visualizador de diff com resumo simples e visão técnica.
- Tabela/lista paginada com busca, filtros anunciados e estado vazio útil.
- Quadro de tarefas operável sem arrastar.
- Confirmação forte que repete alvo e efeito de exclusão/publicação.
- Aviso de privacidade antes de qualquer envio externo.

## 8. Conteúdo e idiomas

- Português é o padrão inicial; inglês pode ser escolhido sem reiniciar o trabalho.
- Frases curtas, verbos diretos e jargão acompanhado de explicação.
- Nenhum texto crítico é concatenado em código; plurais, datas e números usam regras do idioma.
- IDs de mensagem são estáveis e testados quanto a parâmetros equivalentes.

## 9. Estados obrigatórios por tela

Carregando, vazio, sucesso, erro recuperável, erro bloqueante, sem permissão, offline/dependência indisponível e conflito de edição. Cada estado explica o que ocorreu, o que foi preservado e a próxima ação segura.
