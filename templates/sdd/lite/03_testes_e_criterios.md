# Caderno 03 — Plano de Testes e Critérios de Aceite (Perfil Lite — AL2)

> **Perfil Lite:** Define os testes obrigatórios e critérios de aprovação para assegurar qualidade no nível AL2.

---

## 1. Pirâmide de Testes do MVP

No nível AL2, a cobertura foca nos fluxos essenciais de negócio e tratamento de exceções:

1. **Testes de Domínio e Casos de Uso (Prioridade Máxima):**
   - Validações das regras de negócio isoladas sem tocar em banco ou internet.
   - Execução em memória via `unittest` em milissegundos.
2. **Testes de Integração de Adaptadores:**
   - Verificação de que as rotas da API e os repositórios em SQLite salvam e recuperam dados corretamente.
3. **Casos de Erro e Tratamento Amigável:**
   - Teste de entrada com campos vazios (deve retornar erro 400 amigável com mensagem em português).
   - Teste de busca por item inexistente (deve retornar 404).

---

## 2. Tabela de Casos de Teste Essenciais

| ID do Teste | Cenário Testado | Dado de Entrada | Resultado Esperado |
| :--- | :--- | :--- | :--- |
| **TEST-01** | Criar item válido com sucesso | Dados corretos preenchidos | Item salvo com ID gerado e status 201 |
| **TEST-02** | Rejeitar item com nome em branco | Campo `nome` vazio | Erro de validação com mensagem didática |
| **TEST-03** | Buscar item por ID inexistente | ID `99999` | Resposta amigável informando que não foi encontrado |
| **TEST-04** | Bloquear acesso sem crachá/token | Requisição sem cabeçalho | Resposta 401 (Acesso não autorizado) |

---

## 3. Critérios de Pronto (Definition of Done — DoD)

O projeto ou funcionalidade só é considerado concluído quando:
- [ ] Todos os testes unitários da suíte passarem sem falhas (`OK`).
- [ ] O comando `auracode slop .` reportar **0 violações** (sem código morto ou stubs `pass`).
- [ ] O comando `auracode leaks .` reportar **0 vazamentos** (todos os arquivos/DBs fechados).
- [ ] O comando `auracode types .` reportar **0 anotações de tipo faltantes**.
- [ ] O comando `auracode sec .` reportar **0 vetores de injeção**.
- [ ] O comando `auracode diff .` validar que as alterações estão limitadas a menos de 500 linhas.
