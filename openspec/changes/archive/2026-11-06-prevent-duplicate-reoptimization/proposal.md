# Proposta: Prevenção de Múltiplos Disparos e Alerta de Execução na Re-otimização de Currículos

## Why

No painel de detalhes de uma candidatura ([`src/ui/applications_view.py`](src/ui/applications_view.py)), o usuário pode re-executar o fluxo multi-agente através do botão "Executar re-otimização". No entanto, durante o processamento do pipeline, o botão permanece interativo e não há aviso explícito advertindo contra a atualização da página. Isso expõe o sistema a cliques concorrentes/duplicados (desperdiçando cota da LLM) ou recarregamentos acidentais (F5), que interrompem a execução do grafo e perdem o progresso do candidato.

## What Changes

- **Desativação do botão de re-otimização durante o processamento**: O botão principal de re-execução (`btn_run_rerun_{filepath}`) torna-se desabilitado (`disabled=True`) durante o processamento, alterando seu rótulo para `"Re-otimizando currículo..."` e ícone para `:material/hourglass_top:`.
- **Bloqueio do botão de alternância do painel**: O botão "Fechar re-otimização" também fica desabilitado durante a execução para evitar que o usuário feche o painel acidentalmente enquanto os agentes estão trabalhando.
- **Sinalização em tela contra recarregamento (F5) e navegação**: Exibição de um alerta visual persistente em destaque (`st.warning`) dentro do container de re-otimização, orientando o usuário a aguardar a finalização sem pressionar F5 ou fechar a aba.
- **Controle resiliente com bloco `try ... finally`**: Gerenciamento de flag de estado (`reopt_is_generating` ou indexada por aplicação) garantindo que falhas de rede, exceções da LLM ou conclusão com sucesso sempre restaurem a interatividade da tela.

## Capabilities

### New Capabilities
<!-- Nenhuma nova capacidade introduzida -->

### Modified Capabilities
- `pipeline-streaming`: Atualiza os requisitos normativos de bloqueio de submissão concorrente e alerta de retenção contra recarregamento da página para abranger explicitamente o fluxo de re-otimização de candidaturas existentes.

## Impact

- **Código afetado**: [`src/ui/applications_view.py`](src/ui/applications_view.py) (gestão de estado de geração e renderização do botão/alerta) e [`src/ui/navbar.py`](src/ui/navbar.py) (registro em chaves transitórias).
- **Testes afetados**: [`tests/test_app_views.py`](tests/test_app_views.py) para cobrir o bloqueio e os alertas durante a re-otimização.
- **APIs/Dependências**: Recursos nativos do Streamlit (`st.session_state`, `st.button(..., disabled=...)`, `st.warning`).

