# Tasks: improve-agent-quality-and-token-efficiency

## 1. Seleção Inteligente e Higienização no GitHub Researcher

- [x] 1.1 Implementar pontuação e ranqueamento determinístico de repositórios em `src/agents/nodes.py` (descarte de forks, bônus de linguagens, topics e regex de descrição com word boundaries), verificando a correta ordenação via teste unitário
- [x] 1.2 Implementar a função utilitária `_clean_readme` para remoção de badges, tags HTML, blocos triviais de licença/instalação e limitação inteligente a ~1.200 caracteres, verificando que o extrato retém seções de stack e arquitetura
- [x] 1.3 Adicionar tratamento robusto de erros HTTP (403, 404, timeouts) no `github_researcher`, registrando avisos explicativos no campo `errors` do estado e verificando que a execução prossegue sem lançar exceções não tratadas

## 2. Validações Determinísticas e Zero-Token no Quality Reviewer

- [x] 2.1 Implementar checagens estruturais determinísticas no revisor (validação da tabela Markdown de 2 colunas, ausência de placeholders residuais como `<...>`, verificação de integridade de links de repositórios contra a lista consultada do GitHub)
- [x] 2.2 Estruturar o modo econômico (`strict_review=False`) para executar o diagnóstico e validação determinística sem invocar nenhuma chamada ao LLM auditor, verificando a geração de feedback estruturado com zero tokens gastos
- [x] 2.3 Em modo rigoroso (`strict_review=True`), interceptar falhas estruturais ou alucinações de links precocemente no Tier 1 e rejeitar antes de chamar a LLM auditora, verificando que o feedback corretivo é repassado ao gerador

## 3. Score ATS Objetivo e Contextualização da Carta de Apresentação

- [x] 3.1 Implementar a fórmula auditável de pontuação ATS combinando taxa real de correspondência de tecnologias, presença de palavras-chave conceituais e conformidade estrutural, verificando que a nota calculada varia entre 50 e 100 conforme evidências reais
- [x] 3.2 Atualizar o prompt do `cover_letter_generator` para receber um sumário estruturado de 1 linha por projeto selecionado (nome, stack e proposta de valor limpa), verificando que a carta gerada referencia os projetos de forma fluida sem estourar o limite de tokens

## 4. Testes e Validação Integrada

- [x] 4.1 Criar suite de testes unitários em `tests/test_agent_quality_improvements.py` validando o ranqueador de repositórios, o sanitizador de READMEs, as checagens determinísticas e o cálculo de pontuação ATS
- [x] 4.2 Executar a suite completa com `pytest` e verificar que todos os testes passam sem quebras de compatibilidade no pipeline existente
