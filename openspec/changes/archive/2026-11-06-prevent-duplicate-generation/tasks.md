# Tasks

## 1. Implementação no Assistente de Otimização (UI)

- [x] 1.1 Em `src/ui/wizard_view.py`, gerenciar a flag `wizard_is_generating` no `st.session_state`, aplicando `disabled=is_generating` e alternando o rótulo/ícone do botão principal (`wizard_submit_btn`) durante o processamento.
- [x] 1.2 Em `src/ui/wizard_view.py`, renderizar aviso em tela (`st.warning`) com ícone de ampulheta instruindo expressamente a aguardar a conclusão sem atualizar a página (F5) ou sair da tela.
- [x] 1.3 Em `src/ui/wizard_view.py`, estruturar o ciclo de execução do grafo com bloco `try ... finally` para garantir a reativação do botão (`wizard_is_generating = False`) mesmo em falhas ou interrupções.
- [x] 1.4 Em `src/ui/navbar.py`, registrar `wizard_is_generating` na lista `TRANSIENT_KEYS` para assegurar que transições e limpezas de estado transitório purguem a flag com segurança.

## 2. Testes Automatizados e Verificação

- [x] 2.1 Em `tests/test_app_views.py`, implementar teste cobrindo a renderização do botão desabilitado e a exibição do alerta de retenção contra F5 quando `wizard_is_generating=True`.
- [x] 2.2 Em `tests/test_app_views.py`, validar o comportamento de resiliência assegurando que exceções do pipeline executam o bloco `finally` e reativam o botão.
- [x] 2.3 Executar `pytest tests/test_ui.py tests/test_app_views.py` e verificar a aprovação total dos testes unitários e de integração.
