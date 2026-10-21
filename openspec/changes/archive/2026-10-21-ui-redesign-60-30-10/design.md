# Design: Redesign de Interface com a Regra 60-30-10

## Context

A aplicação CV Nitro é construída sobre Streamlit com arquitetura modular desacoplada em `src/ui/`. A identidade visual anterior utilizava tema escuro com tons de indigo (#6366f1) e ardósia escura. O objetivo deste design é reestruturar as regras de estilo para a paleta "Clássico Tech Confiável" sob a proporção 60-30-10, mantendo integralmente todas as funcionalidades e código de negócio.

## Goals / Non-Goals

**Goals:**
- Implementar a distribuição 60-30-10: 60% fundo neutro (#F8FAFC / #F1F5F9), 30% estrutura e texto (#0F172A / #CBD5E1), 10% destaques (#10B981 / #0EA5E9).
- Centralizar os tokens de design em `.streamlit/config.toml` e no módulo `src/ui/components.py`.
- Garantir contraste acessível WCAG AA em todas as telas (Dashboard, Otimizador, Candidaturas, Perfil, Sistema, Login e Cadastro).
- Padronizar componentes reutilizáveis (cards, botões, cabeçalhos, formulários e métricas).
- Manter 100% dos testes existentes passando sem quebras de contrato.

**Non-Goals:**
- Não reescrever regras de negócio, agentes LangGraph, prompts ou rotas de persistência no Supabase.
- Não introduzir frameworks CSS externos pesados ou dependências npm desnecessárias.
- Não alterar validações de formulário ou fluxo de sessões de usuário.

## Decisions

### 1. Configuração Nativa do Streamlit via `config.toml`
- **Decisão**: Configurar as variáveis do tema nativo do Streamlit (`base = "light"`, `primaryColor = "#10B981"`, `backgroundColor = "#F8FAFC"`, `secondaryBackgroundColor = "#F1F5F9"`, `textColor = "#0F172A"`, `borderColor = "#CBD5E1"`, `linkColor = "#0EA5E9"`).
- **Justificativa**: O Streamlit injeta automaticamente esses valores nos componentes internos (inputs, selects, alerts, sidebar e métricas), assegurando comportamento consistente sem gambiarras de sobrescrita excessiva.
- **Alternativas consideradas**: Forçar todas as cores via CSS puro com `!important` em cada tag — descartado por causar inconsistências de renderização e quebras em atualizações da biblioteca.

### 2. Dicionário de Tokens e CSS Global Complementar em `src/ui/components.py`
- **Decisão**: Criar um dicionário `THEME_TOKENS` exportável em `src/ui/components.py` e expandir a função `apply_theme()` para injetar o CSS complementar:
  - Estilização da navbar no topo com fundo semitransparente claro (`rgba(248, 250, 252, 0.95)`), backdrop-filter blur e borda inferior `#CBD5E1`.
  - Estilização dos cartões `st.container(border=True)` com superfícies discretas `#F1F5F9`, bordas sutis e raio de canto `0.6rem`.
  - Avatar do usuário (`.gm-avatar`) atualizado com gradiente moderno alinhado aos tons tecnológicos azul noturno e ciano/menta.
- **Justificativa**: Centraliza as customizações finas que o `config.toml` nativo não cobre, permitindo que qualquer view importe as cores programaticamente (como em gráficos `st.bar_chart`).

### 3. Hierarquia de Ações em Botões
- **Decisão**: Ações principais de conversão/avanço ("Iniciar Otimização", "Entrar", "Salvar Perfil", "Nova Otimização") usam `type="primary"` (renderizado em verde-menta `#10B981`). Ações secundárias, cancelamento ou filtros usam `type="secondary"` ou `type="tertiary"`.
- **Justificativa**: Respeita os 10% da regra 60-30-10 para manter o verde reservado a pontos focais de decisão do usuário.

### 4. Gráficos Analíticos e Badges de Diagnóstico
- **Decisão**: No `dashboard_view.py`, a cor do gráfico de barras de tecnologias mais pedidas passa de `#6366f1` para `#0EA5E9` (ciano complementar). No `diagnostic_view.py`, a barra de progresso e as badges de palavras-chave adotam contrastes adequados sobre o fundo claro.
- **Justificativa**: Reforça a identidade SaaS tecnológica e elimina resquícios da paleta roxa antiga.

## Risks / Trade-offs

- **[Risco] Contraste de texto em componentes nativos sobre fundo claro**:
  - *Mitigação*: Validar visualmente e via testes se elementos como `st.caption`, `st.metric` e placeholders permanecem legíveis com contraste superior a 4.5:1.
- **[Risco] Sobrescrita de elementos da navbar superior pelo CSS do Streamlit**:
  - *Mitigação*: Ajustar `header[data-testid="stHeader"]` com fundo correspondente à paleta clara `#F8FAFC` e borda `#CBD5E1`.
