# Tasks: App Hardening, Security & Quality

## 1. Configuração e Isolamento da Suíte de Testes

- [x] 1.1 Criar `pytest.ini` configurando `pythonpath = .` para permitir execução direta do pytest
- [x] 1.2 Configurar fixture de isolamento de histórico em `tests/conftest.py` utilizando `tmp_path` e variável `HISTORY_DIR` para evitar poluição do repositório
- [x] 1.3 Executar `pytest` e validar que a descoberta de módulos funciona sem `ModuleNotFoundError`

## 2. Sanitização contra Stored XSS e HTML Injection

- [x] 2.1 Aplicar sanitização com `html.escape` em todas as interpolações de strings em `src/core/resume_formatter.py`
- [x] 2.2 Adicionar testes unitários em `tests/test_resume_formatter.py` verificando escape de tags perigosas (`<script>`, `<img onerror>`) e links maliciosos
- [x] 2.3 Executar testes do formatador e validar prevenção de injeção

## 3. Hardening de Rede, Validação e Resiliência dos Agentes

- [ ] 3.1 Implementar validação regex do nome de usuário GitHub e timeouts de conexão/leitura em `src/agents/nodes.py`
- [ ] 3.2 Ajustar `quality_reviewer` para não aprovar automaticamente o currículo em caso de falha de API ou conexão
- [ ] 3.3 Adicionar testes unitários com mocks em `tests/test_nodes.py` cobrindo timeout de rede e falha no revisor

## 4. Parser de Documentos e Suporte a Tabelas

- [ ] 4.1 Adicionar extração de texto em tabelas (`doc.tables`) e remover extensão inválida `.doc` em `src/core/document_parser.py` e `app.py`
- [ ] 4.2 Adicionar teste unitário cobrindo extração de dados em tabelas DOCX e validação de formatos suportados
- [ ] 4.3 Executar os testes de parser e validar extração completa

## 5. Validação Integrada e Conclusão

- [ ] 5.1 Executar a suíte completa de testes automatizados com `pytest`
- [ ] 5.2 Verificar `git status` assegurando que nenhum arquivo temporário de teste foi gerado no diretório `history/`
