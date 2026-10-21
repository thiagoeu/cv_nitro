# Design: Rodapé Global da Aplicação e Limpeza Visual da Landing Page

## Context

A aplicação possui um layout baseado em Streamlit (`app.py`), onde o footer nativo da plataforma é ocultado via CSS em `src/ui/components.py`.
Não havia um rodapé institucional próprio para apresentar os créditos do desenvolvedor (Thiago Araújo), links de contato, repositório GitHub e termos de licença.
Adicionalmente, em `src/ui/landing_view.py`, a última seção possuía um bloco escuro com texto de baixo contraste e botões de ação repetidos que causavam poluição visual antes do encerramento da página.

## Goals / Non-Goals

**Goals:**
- Implementar um rodapé global reutilizável (`render_footer()`) em `src/ui/components.py`.
- Exibir os dados do autor com destaque e links diretos:
  - Autor: Thiago Araújo
  - GitHub: [@thiagoeu](https://github.com/thiagoeu)
  - E-mail: `araujo.thiago1051@gmail.com`
  - Licença e contexto: Licença MIT · Disciplina de Sistemas Multi-Agentes (SMA).
- Renderizar o rodapé em todas as páginas da aplicação chamando-o ao final de `app.py`.
- Limpar a Landing Page (`src/ui/landing_view.py`), removendo a caixa escura e os botões redundantes inferiores, mantendo o foco de conversão na Hero Section superior.
- Garantir 100% de aprovação na suíte de testes.

**Non-Goals:**
- Não alterar as rotas, autenticação ou fluxo dos agentes LangGraph.
- Não modificar os botões de CTA da Hero Section no topo da Landing Page.

## Decisions

### Decisão 1: Centralização do Rodapé em `src/ui/components.py` e Chamada em `app.py`
- **Abordagem**: Criar a função `render_footer()` em `src/ui/components.py` e chamá-la no ponto único de término do ciclo de renderização em `app.py` (`page.run()` seguido de `render_footer()`).
- **Alternativa Descartada**: Chamar `render_footer()` manualmente dentro de cada uma das 8 views individuais. A chamada única em `app.py` elimina duplicação de código e garante que qualquer nova página receba o rodapé automaticamente.

### Decisão 2: Estilização do Rodapé no Padrão 60-30-10
- **Abordagem**: Utilizar divisória discreta (`border-top: 1px solid #CBD5E1`), margem superior generosa (`margin-top: 3.5rem`), tipografia legível em tons de cinza ardósia (`#475569`) e links em ciano (`#0EA5E9`).
- **Alternativa Descartada**: Rodapé fixo na parte inferior da tela (sticky footer com `position: fixed`). Footers fixos ocupam espaço precioso de visualização em telas de trabalho e conflitam com barras de rolagem nativas do Streamlit.

### Decisão 3: Simplificação da Landing Page
- **Abordagem**: Remover a seção 4 do arquivo `src/ui/landing_view.py`. O fluxo da Landing Page passa a ser: Hero Section com CTAs -> Grid de Diferenciais de Valor -> Passo a Passo de Como Funciona -> Rodapé Global.
- **Alternativa Descartada**: Alterar apenas as cores da caixa escura da seção 4. O usuário solicitou explicitamente a remoção dos botões de baixo e da caixa dissonante, tornando a experiência mais limpa e focada no CTA da Hero.

## Risks / Trade-offs

- **[Risco] Testes unitários que verificam elementos da landing page**:
  - *Mitigação*: Os testes unitários existentes em `tests/test_ui.py` validam os botões da Hero Section (`landing_btn_signup`), que permanecerão ativos. Adicionaremos testes específicos para o novo componente `render_footer`.

## Migration Plan

1. Implementar `render_footer()` em `src/ui/components.py`.
2. Remover a caixa escura e botões redundantes em `src/ui/landing_view.py`.
3. Injetar `render_footer()` em `app.py`.
4. Adicionar testes unitários para o rodapé em `tests/test_ui.py`.
5. Validar suite com `pytest` e inspecionar visualmente no navegador.
