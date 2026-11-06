# Proposta: Prevenção de Múltiplos Disparos e Alerta de Execução no Assistente de Currículo

## Why

Atualmente, ao clicar no botão "Gerar currículo otimizado e diagnóstico ATS", o pipeline multi-agente é iniciado, mas o botão permanece interativo e não há uma sinalização enfática para o usuário aguardar a finalização. Isso propicia cliques repetidos (gerando requisições duplicadas e consumo desnecessário de cota/tokens da LLM) ou recarregamentos acidentais da página (F5), que interrompem a execução do grafo e descartam o progresso em andamento.

## What Changes

- **Desativação do botão de disparo durante a execução**: O botão principal do assistente (`wizard_submit_btn`) passa a ficar desabilitado (`disabled=True`) enquanto o pipeline multi-agente estiver em processamento ativo, prevenindo chamadas concorrentes ou duplicadas.
- **Sinalização em tela contra recarregamento (F5) e navegação**: Exibição de um alerta visual persistente em destaque durante a execução (`st.warning` ou `st.info`) advertindo expressamente o usuário para aguardar a conclusão sem fechar a aba ou pressionar F5.
- **Controle resiliente de estado da UI**: Gerenciamento de uma flag de execução no `st.session_state` (ex.: `wizard_is_generating`), assegurando que a UI restaure o estado interativo caso ocorra alguma falha ou após o término com sucesso.

## Capabilities

### New Capabilities
<!-- Nenhuma nova capacidade introduzida -->

### Modified Capabilities
- `pipeline-streaming`: Adiciona os requisitos de bloqueio de submissão concorrente (desativação do botão de geração durante o ciclo de vida da execução) e alerta visual de retenção para evitar recarregamento da página (F5) enquanto os agentes trabalham.

## Impact

- **Código afetado**: [`src/ui/wizard_view.py`](src/ui/wizard_view.py) (gerenciamento de estado de geração e renderização condicional de alerta/botão).
- **Testes afetados**: [`tests/test_ui.py`](tests/test_ui.py) e [`tests/test_app_views.py`](tests/test_app_views.py) para cobrir o comportamento do botão desabilitado e a limpeza de estado.
- **APIs/Dependências**: Nenhuma nova dependência externa; utiliza recursos nativos do Streamlit (`st.session_state`, `st.button(..., disabled=...)`, `st.warning`).

