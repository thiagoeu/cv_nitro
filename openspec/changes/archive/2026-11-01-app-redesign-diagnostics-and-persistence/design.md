# Design

## Context

O CV Nitro é construído em Python com Streamlit (`app.py`), LangGraph (`src/agents/`) e persistência baseada em arquivos Markdown locais (`src/core/history_manager.py`). O pipeline multi-agente é composto por:
1. `job_analyzer`
2. `github_researcher`
3. `resume_generator`
4. `quality_reviewer` (com loop condicional de até 2 tentativas)
5. `cover_letter_generator`

Para preparar a aplicação para produção e deploy em nuvem (ex.: Streamlit Cloud), é necessário desacoplar o armazenamento local para suportar um banco na nuvem (Supabase), reestruturar a interface para uma navegação modular em seções, exibir o diagnóstico da otimização e fornecer controles para redução no consumo de tokens da LLM.

## Goals / Non-Goals

**Goals:**
- Modularizar a interface com navegação por menu (`Dashboard`, `Nova Otimização`, `Candidaturas/Histórico`, `Configurações`).
- Gerar e exibir visualmente o relatório de diagnóstico da otimização ATS (score estimado, palavras-chave alinhadas, alterações efetuadas e parecer do auditor).
- Permitir execução modular e econômica do grafo de agentes (seleção de geração de carta e nível de revisão pelo usuário, truncamento otimizado de prompts).
- Implementar camada de persistência com driver Supabase e fallback automático para armazenamento local.
- Estruturar o plano de implementação em etapas atômicas para commits individuais.

**Non-Goals:**
- Não substituir o Streamlit por outro framework de frontend (ex.: React/Next.js).
- Não implementar sistema completo de autenticação multi-tenant com login/senha neste momento (foco na persistência de dados em banco para deploy).

## Decisions

### Decisão 1: Organização Modular da Interface
- **Escolha**: Criar submódulos de visualização organizados em `src/ui/` (ou componentes dedicados) para cada seção do menu:
  - `views/dashboard.py`: Métricas consolidadas, gráficos de mercado e acesso rápido.
  - `views/optimizer.py`: Assistente passo a passo (upload de arquivo, parâmetros da vaga, opções de IA e diagnóstico final).
  - `views/history.py`: Visualização detalhada de candidaturas salvas, impressão A4/PDF, exportação Markdown e diagnóstico.
  - `views/settings.py`: Status das chaves de API (Gemini/Groq/GitHub), status do banco de dados e seleção de modelo padrão.
- **Alternativa descartada**: Manter todo o código concentrado em `app.py` com mais de 700 linhas, o que prejudica a manutenibilidade e dificulta testes.

### Decisão 2: Modelo Estruturado de Diagnóstico ATS
- **Escolha**: Expandir `GraphState` em `src/agents/state.py` com um campo de diagnóstico:
  ```python
  class OptimizationDiagnostic(TypedDict):
      ats_score: int
      matched_keywords: List[str]
      applied_changes: List[str]
      reviewer_summary: str
  ```
  O `quality_reviewer` (ou um parser leve no nó de revisão) calcula o score e resume os ajustes realizados.
- **Alternativa descartada**: Fazer uma nova chamada LLM separada apenas para gerar o diagnóstico (aumentaria custos de token desnecessariamente).

### Decisão 3: Execução Modular e Economia de Tokens
- **Escolha**:
  - Permitir checkboxes na tela: `[ ] Gerar Cover Letter (Carta de Apresentação)` e `[ ] Revisão Rígida com Revisor`.
  - No `graph.py`, se a geração de carta for desmarcada, a rota final direciona diretamente para `END`.
  - Reduzir o corte de caracteres de READMEs de 1000 para 400 por repositório em `_portfolio_context`, economizando até 40% dos tokens de entrada no `resume_generator`.
  - Suportar seleção de modelo no `config.py` via variável `GEMINI_MODEL` (ex: `gemini-2.0-flash-lite` ou `gemini-2.5-flash`).
- **Alternativa descartada**: Manter o fluxo sempre executando todas as 5 etapas obrigatoriamente.

### Decisão 4: Persistência Híbrida (Supabase com Fallback Local)
- **Escolha**:
  - Criar um módulo `src/core/storage_manager.py` (ou adaptar `history_manager.py`) que verifica se as variáveis `SUPABASE_URL` e `SUPABASE_KEY` estão presentes.
  - Se presentes, salva e busca registros na tabela `applications` do Supabase via biblioteca cliente oficial.
  - Se ausentes, executa a persistência tradicional em arquivos `.md` na pasta `history/`.
  - Fornecer um script SQL `supabase_schema.sql` na raiz do projeto para criação fácil da tabela no painel do Supabase.
- **Alternativa descartada**: Forçar obrigatoriedade do Supabase, que quebraria o ambiente local de quem não tem chave configurada.

## Risks / Trade-offs

- **[Risco] Latência ou indisponibilidade da API do Supabase**:
  - *Mitigação*: Implementar bloco try/except com fallback transparente e mensagens de aviso amigáveis na interface, sem travar a sessão.
- **[Risco] Compatibilidade com registros históricos antigos**:
  - *Mitigação*: Manter suporte total à leitura dos arquivos `.md` gerados anteriormente que não possuíam campos de diagnóstico.

## Migration Plan

1. Nenhuma quebra de retrocompatibilidade com os arquivos `.md` já salvos na pasta `history/`.
2. A migração para o Supabase é opcional e habilitada via variáveis de ambiente (`SUPABASE_URL`, `SUPABASE_KEY`).
