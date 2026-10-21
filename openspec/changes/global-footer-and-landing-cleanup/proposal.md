# Proposal: Rodapé Global da Aplicação e Limpeza Visual da Landing Page

## Why

A aplicação carece de um rodapé (footer) institucional global que identifique a autoria do projeto, forneça canais de contato com o desenvolvedor (Thiago Araújo), link para o GitHub, termos de licença e contexto acadêmico (Sistemas Multi-Agentes).
Além disso, a seção final da Landing Page (`src/ui/landing_view.py`) apresenta uma caixa com fundo escuro que destoa da paleta 60-30-10, prejudica a legibilidade dos textos e introduz botões de CTA inferiores redundantes, que poluem a experiência antes do rodapé.

## What Changes

- **Novo Componente de Rodapé Global (`render_footer`)**: Criar um rodapé moderno em `src/ui/components.py` integrado à paleta Clássico Tech Confiável (60-30-10), exibindo créditos do desenvolvedor (*Thiago Araújo*), e-mail (`araujo.thiago1051@gmail.com`), GitHub ([@thiagoeu](https://github.com/thiagoeu)), licença MIT e menção à disciplina de Sistemas Multi-Agentes.
- **Integração no Layout Global (`app.py`)**: Chamar `render_footer()` no ponto de saída do layout principal, garantindo presença consistente em todas as páginas e estados da aplicação.
- **Limpeza Visual e Correção da Landing Page (`src/ui/landing_view.py`)**:
  - Remover a caixa de encerramento escura/ilegível e os botões inferiores duplicados ("Criar Conta e Começar" / "Acessar Minha Conta").
  - Centralizar as ações de conversão exclusivamente na Hero Section superior de alto impacto.
  - Ajustar o fluxo visual para que a seção "Como Funciona" finalize harmoniosamente e se conecte diretamente com o novo rodapé institucional.

## Capabilities

### New Capabilities
<!-- Nenhuma nova capacidade necessária; este trabalho estende o design system existente. -->

### Modified Capabilities
- `ui-design-system`: Adiciona o requisito de Rodapé Global da Aplicação (créditos do autor, contato, licença e links) e refinamento de harmonia e contraste visual na Landing Page.

## Impact

- **Código Afetado**:
  - `src/ui/components.py`: Adição da função `render_footer()` com estilos de borda e tipografia 60-30-10.
  - `src/ui/landing_view.py`: Remoção da caixa com fundo escuro e botões redundantes inferiores.
  - `app.py`: Chamada de `render_footer()` ao final da renderização da página ativa.
  - `tests/test_ui.py`: Testes unitários para validar a renderização do rodapé global e o layout limpo da landing page.
- **APIs e Dependências**: Nenhuma dependência externa nova. Utiliza componentes nativos do Streamlit.
