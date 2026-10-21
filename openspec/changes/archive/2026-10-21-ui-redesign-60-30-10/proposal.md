# Proposal: Redesign de Interface com a Regra 60-30-10

## Why

A interface atual do CV Nitro utiliza um tema escuro genérico com cores roxas/indigo (#6366f1) que não refletem a proposta de um SaaS moderno, limpo e corporativo. A aplicação da regra de proporção visual 60-30-10 com a paleta "Clássico Tech Confiável" (Branco gelo, Azul noturno e Verde-menta/Ciano) estabelece uma hierarquia visual profissional, melhora a legibilidade em longos textos de currículo e eleva a percepção de credibilidade e produtividade.

## What Changes

- **Centralização de Design Tokens**: Definição de tokens de cor e espaçamento centralizados em `.streamlit/config.toml` e no módulo de componentes `src/ui/components.py`, eliminando valores hexadecimais soltos nas telas.
- **60% Fundo Neutro e Áreas de Leitura**: Adoção de Branco Gelo (`#F8FAFC`) como fundo padrão e Cinza Claro (`#F1F5F9`) para superfícies secundárias e cards de leitura/edição.
- **30% Estrutura e Identidade**: Aplicação do Azul Noturno (`#0F172A`) em cabeçalhos, títulos, textos principais, navbar superior e Cinza Azulado (`#CBD5E1`) em bordas e divisórias.
- **10% Destaques e Ações (CTAs)**: Padronização do Verde-menta (`#10B981`) para botões primários, badges de sucesso e CTAs principais; e Ciano Complementar (`#0EA5E9`) para links, gráficos de tecnologia e badges informativos.
- **Hierarquia Visual e Cards**: Estilização refinada dos `st.container(border=True)`, métricas (`st.metric`), alertas e formulários com cantos arredondados consistentes, sombras sutis e estados de hover/focus.
- **Feedback Visual e Acessibilidade**: Estados de foco visíveis, contrastes em conformidade WCAG AA entre texto e fundo, feedback visual de carregamento e badges de status com textos explicativos.
- **Preservação Funcional**: Manutenção integral de todos os fluxos de autenticação, geração por agentes, histórico no Supabase e validações.

## Capabilities

### New Capabilities
- `ui-design-system`: Define os tokens visuais, a distribuição de cores na regra 60-30-10, padrões de cards, botões de ação primária/secundária, métricas e acessibilidade visual em todas as telas da aplicação.

### Modified Capabilities
<!-- Nenhuma regra de negócio ou capacidade funcional existente foi alterada -->

## Impact

- **Código Afetado**:
  - `.streamlit/config.toml`: Configuração global do tema claro Streamlit (base, cores primárias, secundárias, texto e bordas).
  - `src/ui/components.py`: Injeção de CSS global, tokens CSS/Python, estilização de cabeçalhos, cards e inputs.
  - `src/ui/navbar.py`: Ajustes de contraste e renderização da barra de navegação no tema claro.
  - `src/ui/dashboard_view.py`: Atualização das cores dos gráficos de barras e cards analíticos.
  - `src/ui/diagnostic_view.py`: Ajuste das barras de progresso ATS e badges de palavras-chave.
  - `src/ui/wizard_view.py`: Estilização dos passos do assistente de otimização.
  - `src/ui/auth_views.py`: Estilização dos cartões de login e cadastro.
  - `src/ui/profile_view.py`: Visualização do perfil e badges de repositórios.
  - `src/ui/settings_view.py`: Painéis de status do sistema e banco de dados.
- **Dependências**: Nenhuma dependência externa adicionada.
- **APIs e Banco**: Zero alteração em contratos de API ou esquema de banco de dados.
