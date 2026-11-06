# Design Técnico: Prevenção de Múltiplos Disparos e Alerta de Execução no Assistente

## Context

Consulte [`proposal.md`](proposal.md) para a motivação. Atualmente, a função `render_wizard_view` em [`src/ui/wizard_view.py`](src/ui/wizard_view.py) renderiza o botão `wizard_submit_btn` estático e executa a função síncrona `run_pipeline_with_status`. Enquanto o pipeline dos agentes é executado, o botão permanece habilitado visualmente no DOM inicial e não há aviso instruindo o usuário a não recarregar (F5).

## Goals / Non-Goals

**Goals:**
- Desabilitar fisicamente o botão `wizard_submit_btn` durante o ciclo de vida da execução de geração do currículo.
- Alterar o texto e ícone do botão enquanto estiver executando (ex.: "Otimizando currículo com agentes...", ícone de ampulheta) para feedback visual imediato.
- Exibir alerta visual proeminente (`st.warning`) orientando o usuário a não recarregar (F5) nem fechar a aba enquanto a IA e os agentes estiverem trabalhando.
- Garantir que o estado de bloqueio seja sempre revertido com segurança através de bloco `try ... finally`, inclusive em falhas de API ou exceções não tratadas.

**Non-Goals:**
- Injetar componentes customizados de JavaScript para interceptar `window.onbeforeunload` (Streamlit não possui suporte nativo confiável para `beforeunload` sem bibliotecas externas; o aviso visual nativo atende ao requisito sem adicionar dependências ou fragilidade).
- Fila assíncrona desacoplada em segundo plano (Celery/Redis); a arquitetura do projeto permanece no fluxo de streaming reativo do Streamlit.

## Decisions

### Decisão 1: Controle de estado no `st.session_state` (`wizard_is_generating`)
- **Abordagem**: Utilizar a flag booleana `wizard_is_generating` no `st.session_state`.
- **Comportamento**:
  - No início da renderização do formulário, ler `is_generating = st.session_state.get("wizard_is_generating", False)`.
  - Passar `disabled=is_generating` para o `st.button`.
  - Se `is_generating` for verdadeiro, alternar o rótulo do botão para `"Otimizando currículo com agentes..."` e ícone para `:material/hourglass_top:`.
- **Alternativas consideradas**:
  - *Bloqueio apenas por formulário `st.form`:* O `st.form` não permite streaming incremental do currículo nem atualizações dinâmicas do `st.status` dentro do container durante a execução.

### Decisão 2: Alerta visual de retenção
- **Abordagem**: Renderizar um `st.warning` com ícone de ampulheta imediatamente antes do botão e da barra de status quando a submissão for disparada.
- **Mensagem**: *"⏳ **Processando candidatura com múltiplos agentes...** Por favor, aguarde a finalização e **não atualize a página (F5) nem saia desta tela** para não interromper a geração."*
- **Alternativas consideradas**:
  - *Toast flutuante (`st.toast`):* Desaparece após poucos segundos; o alerta precisa ser persistente durante todo o tempo em que o grafo roda.

### Decisão 3: Garantia de restauração via `try ... finally`
- **Abordagem**: A ativação da flag `st.session_state.wizard_is_generating = True` é acompanhada obrigatoriamente de uma estrutura:
  ```python
  try:
      # execução do pipeline e salvamento
  finally:
      st.session_state.wizard_is_generating = False
  ```
- **Rationale**: Impede que um erro de rede ou estouro de cota deixe o botão travado para o usuário, permitindo que ele tente novamente após a mensagem de erro ser exibida.

## Risks / Trade-offs

- **[Risco: Usuário aperta F5 mesmo com o aviso]** $\to$ *Mitigação:* O Streamlit reinicia a sessão do zero para aquela aba ou restaura o estado padrão. Garantir que `wizard_is_generating` inicie como `False` se não houver execução ativa previne qualquer bloqueio zumbi.
- **[Risco: Compatibilidade com testes automatizados existentes]** $\to$ *Mitigação:* Testes como `test_wizard_view_streaming_success` mockam `fake_button` verificando `"Gerar currículo otimizado" in label`. Ao manter esse texto quando `is_generating` for `False`, os testes existentes passam sem alterações, e novos testes unitários validam especificamente o estado `disabled=True`.

