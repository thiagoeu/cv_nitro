# Proposal

## Why

O CV Nitro atualmente executa o fluxo multi-agente e entrega o currículo gerado de forma opaca em uma interface estática de abas simples, sem expor o diagnóstico detalhado da otimização ATS e o feedback do revisor. Além disso, a dependência exclusiva do sistema de arquivos local impede o deploy seguro em plataformas na nuvem (como Streamlit Community Cloud) e o consumo elevado de tokens sobrecarrega contas com planos e cotas limitadas de IA.

## What Changes

- **Interface Modular com Menu**: Substituição da alternância básica de abas por uma navegação clara e amigável dividida em sessões dedicadas: Dashboard Geral, Wizard de Otimização Passo a Passo, Central de Candidaturas/Histórico e Configurações.
- **Relatório de Diagnóstico & Feedback de Otimização**: Apresentação visual detalhada do "Raio-X" da otimização (score ATS estimado, palavras-chave e tecnologias inseridas, resumo das alterações efetuadas e parecer do auditor de qualidade).
- **Otimização de Tokens & Execução Econômica**: Introdução de opções configuráveis na interface para desativar etapas opcionais (Cover Letter e loop do Quality Reviewer), corte de tamanho de prompts de entrada (resumo de READMEs e CV base) e compatibilidade com modelos mais econômicos (ex.: `gemini-2.0-flash-lite` ou Groq).
- **Persistência Híbrida Pronta para Deploy (Supabase + Fallback Local)**: Criação de um conector de dados com suporte ao Supabase para deploy na nuvem sem perda de dados em containers efêmeros, mantendo fallback automático para arquivos locais caso as credenciais não estejam configuradas.
- **Separação em Etapas e Commits Independentes**: O plano de ação organiza todo o desenvolvimento em marcos claros e commits atômicos para implementação gradual e segura.

## Capabilities

### New Capabilities
- `application-navigation`: Menu modular com navegação dedicada entre Dashboard Executivo, Wizard de Otimização, Central de Candidaturas e Painel de Configurações.

### Modified Capabilities
- `ats-optimization`: Geração e exibição do diagnóstico detalhado de conformidade ATS, incluindo score estimado, palavras-chave alinhadas e parecer explicativo do revisor.
- `resume-optimization`: Controle de execução do grafo multi-agente com modo econômico de tokens e parâmetros modulares para redução de custos de IA.
- `resume-history`: Camada de persistência desacoplada com suporte ao Supabase e fallback transparente para o armazenamento local existente.

## Impact

- **Frontend / Interface**: `app.py` reorganizado em componentes/visualizações modulares de menu.
- **Pipeline Multi-Agente**: `src/agents/state.py`, `src/agents/nodes.py` e `src/agents/graph.py` passam a retornar métricas de diagnóstico estruturadas e aceitar flags de execução econômica.
- **Persistência**: `src/core/history_manager.py` passa a delegar para um adaptador de armazenamento (Supabase ou Local).
- **Dependências**: Adição opcional de `supabase` no `requirements.txt` e atualização do `.env.example`.
