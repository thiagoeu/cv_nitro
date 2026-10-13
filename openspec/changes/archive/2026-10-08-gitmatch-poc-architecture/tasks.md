# Tasks

## 1. Configuração do Projeto

- [x] 1.1 Criar o arquivo `requirements.txt` com as dependências base (langgraph, langchain, streamlit, google-generativeai, requests, python-dotenv) e garantir que a instalação via `pip install` seja bem-sucedida.
- [x] 1.2 Configurar leitura de variáveis de ambiente (`.env`) para as chaves do Google Gemini e GitHub Token (se fornecido). Verificar a leitura correta das variáveis carregadas em memória.

## 2. Construção do Core e Armazenamento (Histórico)

- [x] 2.1 Criar módulo gerenciador de histórico (`history_manager.py`) para salvar, listar e carregar currículos na pasta local `history/` em formato `.md`. Validar a escrita e leitura dos arquivos com testes automatizados simples.

## 3. Implementação dos Nós do Agente

- [x] 3.1 Implementar a classe de Estado (`State`) do grafo no LangGraph, contendo a vaga original, metadados do GitHub, conteúdo dos READMEs, rascunho do currículo, e feedback do revisor. Validar a criação de um objeto State limpo.
- [x] 3.2 Implementar o nó do **Job Analyzer** para extrair as palavras-chave usando o Gemini. Testar o nó isoladamente com uma vaga falsa e verificar se os campos chave estão no output.
- [x] 3.3 Implementar o nó do **GitHub Researcher** para listar repositórios públicos de um usuário via API e extrair READMEs relevantes (focando em linguagens da vaga). Testar a requisição validando a extração dos READMEs.
- [x] 3.4 Implementar o nó do **Resume Generator** para juntar o currículo base, a vaga, e o portfólio GitHub em um novo Markdown formatado. Inspecionar a resposta formatada no log.
- [x] 3.5 Implementar o nó do **Quality Reviewer** para auditar alucinações (cruzamento do gerado vs GitHub original). Testar passando um currículo que invente um framework que o repositório não tenha, validando que o revisor rejeita.

## 4. Orquestração do Grafo

- [x] 4.1 Construir o fluxo final (StateGraph) conectando Analisador -> Pesquisador -> Gerador -> Revisor, incluindo o laço condicional (edge) do Revisor de volta para o Gerador com limite de tentativas. Executar um teste dry-run end-to-end do fluxo.

## 5. Interface Streamlit

- [x] 5.1 Construir a interface lateral (Sidebar) integrando o `history_manager.py` para listar currículos antigos. Clicar em um currículo deve exibi-lo na tela principal.
- [x] 5.2 Construir o painel principal com os inputs (Texto da vaga, Markdown do currículo base, Usuário do GitHub) e o botão "Otimizar".
- [x] 5.3 Conectar o clique do botão "Otimizar" ao fluxo do LangGraph e exibir o resultado Markdown processado no painel principal ao final, acionando em seguida a rotina de salvar no histórico. Validar subindo o servidor Streamlit e visualizando no navegador.

## Workflow follow-up

- Arquivar a especificação com `/openspec-archive-change` assim que o desenvolvimento e testes estiverem concluídos com sucesso.
