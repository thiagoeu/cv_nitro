# Tasks: Redesign de Interface com a Regra 60-30-10

## 1. Centralização do Tema e Tokens Visuais

- [x] 1.1 Atualizar `.streamlit/config.toml` configurando o tema claro nativo com a paleta Clássico Tech Confiável (fundo `#F8FAFC`, secundário `#F1F5F9`, texto `#0F172A`, borda `#CBD5E1`, primária `#10B981`, links `#0EA5E9`) e verificar a correta leitura da configuração.
- [x] 1.2 Definir o dicionário de design tokens e aprimorar a injeção `apply_theme()` em `src/ui/components.py` com estilização refinada de containers, navbar superior clara com blur, avatar e estados de foco, validando com execução dos testes de componentes.

## 2. Refinamento dos Componentes Compartilhados e Navbar

- [x] 2.1 Ajustar a navbar superior em `src/ui/navbar.py` para garantir legibilidade dos links de navegação, ícones e menu de conta com o fundo claro e bordas sutis.
- [x] 2.2 Padronizar `src/ui/components.py` (`page_header`, `login_gate`, `resume_input`, `application_card`) aplicando a hierarquia de botões primários verde-menta e ações secundárias neutras.

## 3. Aplicação da Proporção 60-30-10 nas Telas

- [x] 3.1 Atualizar `src/ui/dashboard_view.py` integrando superfícies `#F1F5F9` nos cards de métricas e alterando a cor do gráfico de barras de tecnologias para ciano complementar (`#0EA5E9`), verificando a renderização no teste `test_app_views.py`.
- [x] 3.2 Atualizar `src/ui/diagnostic_view.py` garantindo contrastes na barra de compatibilidade ATS, parecer do revisor e badges de palavras-chave sobre superfícies claras.
- [x] 3.3 Atualizar `src/ui/wizard_view.py` estilizando os contêineres das etapas 1, 2 e 3 com visual SaaS limpo e botão principal de disparo verde-menta.
- [x] 3.4 Atualizar `src/ui/auth_views.py` (login e cadastro) com cartões centralizados, títulos azul noturno e botões primários verde-menta com feedback de erro/sucesso.
- [x] 3.5 Atualizar `src/ui/profile_view.py` e `src/ui/settings_view.py` com os novos tokens de cor, badges de status do sistema e contraste acessível.

## 4. Validação de Qualidade e Regressão

- [x] 4.1 Executar a suíte de testes automatizados com `pytest` e garantir que todos os 56 testes continuam passando com sucesso.
- [x] 4.2 Validar a interface em execução no navegador, confirmando a proporção 60-30-10, responsividade, estados de hover/focus e a completa remoção de valores hexadecimais legados (#6366f1).
