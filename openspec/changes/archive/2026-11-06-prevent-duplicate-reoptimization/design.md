# Design Técnico: Prevenção de Múltiplos Disparos e Alerta de Execução na Re-otimização

## Context

Consulte [`proposal.md`](proposal.md) para a motivação. Em [`src/ui/applications_view.py`](src/ui/applications_view.py), a função `render_application_view` disponibiliza um painel de re-otimização que executa o grafo via `run_pipeline_with_status`. Similarmente ao assistente inicial, esse painel não desabilitava o botão `btn_run_rerun_{filepath}` nem exibia o aviso de permanência contra recarregamentos (F5), permitindo chamadas concorrentes ou interrupções acidentais.

## Goals / Non-Goals

**Goals:**
- Desabilitar os botões de execução (`btn_run_rerun_{filepath}`) e de alternância do painel (`btn_toggle_rerun_{filepath}`) durante o processamento da re-otimização.
- Exibir alerta visual destacado (`st.warning`) orientando o usuário a não recarregar (F5) nem sair da página durante a re-otimização.
- Alternar o texto e ícone do botão para indicar o estado de execução ativa.
- Garantir a liberação da flag com `try ... finally` inclusive em caso de exceções no grafo.

**Non-Goals:**
- Alterar o mecanismo de persistência de arquivos ou a lógica do grafo de agentes.

## Decisions

### Decisão 1: Flag de estado `reopt_is_generating` em `st.session_state`
- **Abordagem**: Utilizar `reopt_is_generating` no `st.session_state`.
- **Efeito**:
  - `disabled=reopt_is_generating` nos botões de disparo e alternância.
  - Alternância do rótulo para `"Re-otimizando com agentes..."` e ícone para `:material/hourglass_top:`.
- **Limpeza**: A chave é registrada em `TRANSIENT_KEYS` em [`src/ui/navbar.py`](src/ui/navbar.py) para ser limpa em transições de página ou logout.

### Decisão 2: Alerta visual de retenção
- **Abordagem**: `st.warning` renderizado dentro do container de re-otimização com texto:
  *"⏳ **Re-otimizando candidatura com múltiplos agentes...** Por favor, aguarde a finalização e **não atualize a página (F5) nem saia desta tela** para não interromper a geração."*

### Decisão 3: Estrutura `try ... finally`
- **Abordagem**: O bloco de execução do pipeline é envelopado com `try ... finally` garantindo que `st.session_state.reopt_is_generating = False` e `st.rerun()` ocorram sempre, liberando a tela caso ocorra qualquer erro da LLM ou falha de conectividade.

## Risks / Trade-offs

- **[Risco: Erro fatal durante a re-otimização]** $\to$ *Mitigação:* O bloco `finally` garante a desativação da flag e o bloco `except` exibe o erro via `st.error`, deixando a interface pronta para nova tentativa.

