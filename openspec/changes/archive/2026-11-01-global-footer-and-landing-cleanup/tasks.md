# Tasks: Rodapé Global da Aplicação e Limpeza Visual da Landing Page

## 1. Rodapé Global da Aplicação

- [x] 1.1 Implementar a função `render_footer()` em `src/ui/components.py` com estilização alinhada à paleta 60-30-10, contendo nome do desenvolvedor (Thiago Araújo), link para o GitHub (`https://github.com/thiagoeu`), e-mail (`araujo.thiago1051@gmail.com`), termos de licença MIT e menção à disciplina de Sistemas Multi-Agentes (SMA).
- [x] 1.2 Integrar a chamada de `render_footer()` em `app.py` após a execução da página ativa (`page.run()`), garantindo a renderização do rodapé em todas as telas da aplicação.
- [x] 1.3 Adicionar testes unitários para o componente `render_footer` em `tests/test_ui.py` e verificar aprovação com `pytest`.

## 2. Limpeza Visual da Landing Page

- [x] 2.1 Remover a seção 4 ("Banner Final de Fechamento") com caixa escura e os botões redundantes inferiores (`landing_btn_bottom_signup` e `landing_btn_bottom_login`) em `src/ui/landing_view.py`.
- [x] 2.2 Ajustar o espaçamento da seção "Como Funciona" em `src/ui/landing_view.py` para que finalize de forma limpa antes do rodapé global.
- [x] 2.3 Atualizar os testes da landing page em `tests/test_ui.py` para refletir a nova estrutura limpa e verificar aprovação com `pytest`.

## 3. Validação Integrada e Verificação Visual

- [x] 3.1 Executar a suíte completa de testes automatizados com `pytest` e garantir que todos os testes passem sem regressões.
- [x] 3.2 Validar a interface no navegador (`http://localhost:8501`), confirmando a presença do rodapé global e a ausência da caixa escura e botões inferiores na Landing Page.
