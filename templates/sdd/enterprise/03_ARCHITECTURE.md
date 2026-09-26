# Arquitetura de Software e ADRs (03 — ARCHITECTURE)

> **Padrão:** Clean Architecture de 4 Camadas  
> **Estilo:** C4 Model (Contexto, Contêineres, Componentes)  

---

## 1. Visão Arquitetural em Camadas
```mermaid
graph TD
    subgraph Presentation ["Camada de Apresentação (UI / CLI / API)"]
        UI[Interface / CLI]
    end
    
    subgraph Application ["Camada de Aplicação (Casos de Uso)"]
        UC[Use Cases & Orquestração]
    end
    
    subgraph Domain ["Camada de Domínio (Entidades Puras)"]
        Entities[Entidades & Regras de Negócio]
    end
    
    subgraph Infrastructure ["Camada de Infraestrutura (Adapters & DB)"]
        DB[(Banco de Dados)]
        ExtAPI[Serviços Externos]
    end
    
    UI --> UC
    UC --> Entities
    Infrastructure --> UC
    Infrastructure --> Entities
```

---

## 2. Contratos e Regras de Importação
- `domain/` nunca pode importar de nenhuma outra camada (0 dependências externas).
- `usecases/` só pode importar de `domain/`.
- `adapters/` conecta o mundo exterior aos casos de uso.
- `infrastructure/` implementa repositórios e clientes de rede definidos por interfaces no domínio.

---

## 3. Registro de Decisões Arquiteturais (ADRs)

### ADR-001: [Título da Decisão, ex: Adoção de SQLite para Persistência Local]
- **Status:** Aprovado
- **Contexto:** [Qual era a necessidade ou problema]
- **Decisão:** [O que foi decidido]
- **Consequências Positivas:** [Benefícios obtidos]
- **Consequências Negativas / Tradeoffs:** [Limitações aceitas]
