# Design System e Interface do Usuário (10 — DESIGN-SYSTEM)

> **Diretriz Estética:** Design Premium, Moderno, Dinâmico e com Micro-animações  
> **Padrão de Cores:** HSL Harmonioso (Dark Mode nativo)  

---

## 1. Tokens de Design

### Paleta de Cores
- **Fundo Principal (Background):** `hsl(222, 47%, 11%)` (Azul escuro profundo)
- **Fundo de Superfície (Cards):** `hsl(217, 33%, 17%)` (Cinza azulado)
- **Destaque Primário (Primary Accent):** `hsl(210, 100%, 56%)` (Azul elétrico vibrante)
- **Sucesso (Success):** `hsl(142, 71%, 45%)` (Verde esmeralda)
- **Alerta / Erro (Destructive):** `hsl(0, 84%, 60%)` (Vermelho coral)
- **Texto Principal:** `hsl(210, 40%, 98%)`
- **Texto Secundário:** `hsl(215, 20%, 65%)`

### Tipografia
- **Família de Fontes:** Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif.
- **Tamanhos:**
  - H1: `2.25rem (36px)` / Peso: `700 Bold`
  - H2: `1.5rem (24px)` / Peso: `600 SemiBold`
  - Body: `1.0rem (16px)` / Peso: `400 Regular`

---

## 2. Componentes e Interatividade
- **Botões:** Transição suave de hover (`transition: all 0.2s cubic-bezier(...)`), feedback visual de clique e estado de carregamento (*loading spinner*).
- **Cards:** Sombra suave e borda sutil translúcida (`border: 1px solid rgba(255, 255, 255, 0.1)`).
