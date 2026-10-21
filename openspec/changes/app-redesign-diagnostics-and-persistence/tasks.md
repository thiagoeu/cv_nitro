# Tasks

## 1. Otimização de Tokens & Pipeline Configurável (Commit 1)

- [x] 1.1 Atualizar `src/agents/state.py` para incluir flags de execução modular (`generate_cover_letter: bool`, `strict_review: bool`) e campo estruturado de diagnóstico (`diagnostic: Dict[str, Any]`), validando as tipagens.
- [x] 1.2 Otimizar `_portfolio_context` e prompts em `src/agents/nodes.py` (redução de caracteres de README para corte de tokens de entrada) e estender `quality_reviewer` para calcular score ATS e registrar resumo das alterações realizadas.
- [x] 1.3 Atualizar o roteamento em `src/agents/graph.py` para que o fluxo pule o nó de Cover Letter quando a flag `generate_cover_letter` for False.
- [x] 1.4 Adicionar testes unitários para a execução modular e métricas de diagnóstico em `tests/test_agents.py` e verificar com `pytest tests/`.

## 2. Camada de Persistência Híbrida & Suporte ao Supabase (Commit 2)

- [x] 2.1 Criar o arquivo `supabase_schema.sql` com o schema da tabela `applications` (incluindo colunas para currículo, carta, metadados e diagnóstico JSON).
- [x] 2.2 Implementar suporte ao Supabase em `src/core/history_manager.py` (ou módulo de storage dedicado) com detecção automática de variáveis de ambiente e fallback transparente para armazenamento local.
- [x] 2.3 Atualizar `requirements.txt` e `.env.example` com as variáveis e dependências necessárias (`supabase`).
- [x] 2.4 Criar testes de unidade para persistência híbrida e fallback local em `tests/test_history.py` e verificar aprovação com `pytest tests/test_history.py`.

## 3. Painel de Diagnóstico & Exibição de Feedback ATS (Commit 3)

- [x] 3.1 Criar componente de exibição de diagnóstico ATS com métricas visuais (score percentual, palavras-chave alinhadas, alterações realizadas e feedback do auditor).
- [x] 3.2 Conectar a exibição do diagnóstico na visualização pós-geração imediata e na tela de detalhe de candidaturas salvas no histórico.
- [x] 3.3 Validar a renderização do diagnóstico salvando e recarregando uma candidatura com dados de diagnóstico completos.

## 4. Redesenho da Interface com Menu e Sessões Dedicadas (Commit 4)

- [x] 4.1 Estruturar menu de navegação lateral amigável em `app.py` com navegação entre Dashboard, Nova Otimização (Wizard), Central de Candidaturas e Configurações.
- [x] 4.2 Implementar o Wizard de Nova Otimização dividido em seções claras: Upload de Currículo, Informações da Vaga, Opções de IA/Economia de Tokens e Execução.
- [x] 4.3 Implementar a página de Configurações exibindo o status de conexão com o banco de dados (Supabase vs Local) e o modelo de IA ativo.
- [x] 4.4 Verificar a navegação completa e responsividade de todas as páginas no Streamlit.

## 5. Validação de Integração e Documentação de Deploy (Commit 5)

- [x] 5.1 Executar toda a suíte de testes com `pytest` e garantir 100% de aprovação sem regressões.
- [x] 5.2 Atualizar o `README.md` com instruções detalhadas de configuração do Supabase, deploy no Streamlit Cloud e uso do modo econômico de tokens.
- [x] 5.3 Validar a integridade da especificação com `openspec validate app-redesign-diagnostics-and-persistence --strict`.
