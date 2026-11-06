# Tasks

## 1. Implementação na Central de Candidaturas (UI)

- [x] 1.1 Em `src/ui/applications_view.py`, gerenciar a flag `reopt_is_generating` em `st.session_state`, aplicando `disabled=reopt_is_generating` no botão de execução (`btn_run_rerun_{filepath}`) e no botão de alternância do painel (`btn_toggle_rerun_{filepath}`), alternando rótulo e ícone durante o processamento.
- [x] 1.2 Em `src/ui/applications_view.py`, renderizar aviso em tela (`st.warning`) com ícone de ampulheta instruindo expressamente a aguardar a conclusão sem atualizar a página (F5) ou sair da tela.
- [x] 1.3 Em `src/ui/applications_view.py`, estruturar a execução do grafo em bloco `try ... finally` garantindo a restauração de `reopt_is_generating = False` e `st.rerun()` mesmo em falhas ou exceções.
- [x] 1.4 Em `src/ui/navbar.py`, registrar `reopt_is_generating` na lista `TRANSIENT_KEYS` para que limpezas de estado e navegações purguem a flag com segurança.

## 2. Testes Automatizados e Verificação

- [x] 2.1 Em `tests/test_app_views.py`, implementar teste validando a renderização dos botões desabilitados e a exibição do alerta de retenção contra F5 quando `reopt_is_generating=True`.
- [x] 2.2 Em `tests/test_app_views.py`, validar o comportamento de resiliência assegurando que falhas na execução executam o bloco `finally` e reativam os botões.
- [x] 2.3 Executar `pytest tests/test_ui.py tests/test_app_views.py` e verificar a aprovação total dos testes.
