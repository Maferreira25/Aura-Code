# Inventário de Dependências Auditadas (13 — DEPENDENCIES)

> **Diretriz Anti-Alucinação:** Nenhuma biblioteca de terceiros pode ser adicionada sem prévia auditoria no PyPI / npm.  
> **Comando de Verificação:** `auracode deps`  

---

## 1. Dependências do Core de Produção
| Pacote | Versão Fixada | Licença | Justificativa de Uso | Auditado contra Slopsquatting? |
| :--- | :--- | :--- | :--- | :--- |
| Ex: `pydantic` | `2.8.2` | MIT | Validação e tipagem estrita de schemas | SIM (Verificado via auracode deps) |

---

## 2. Dependências de Desenvolvimento e Testes
| Pacote | Versão Fixada | Licença | Justificativa de Uso |
| :--- | :--- | :--- | :--- |
| `pytest` | `>=7.0.0` | MIT | Executor de testes unitários |
| `pytest-cov` | `>=4.0.0` | MIT | Medição de cobertura de código |

---

## 3. Política de Atualização
- Fixação estrita de versões (*pinning*) em `requirements.txt` / `pyproject.toml`.
- Varredura periódica de vulnerabilidades conhecidas (CVEs).
