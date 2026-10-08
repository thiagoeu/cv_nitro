# GitMatch - Arquitetura e Decisões de Design (PoC)

Com base nas nossas decisões, aqui está a arquitetura detalhada para iniciarmos o desenvolvimento do **GitMatch**:

## 1. Stack Tecnológico Principal
* **Linguagem:** Python
* **Orquestração Multi-Agente:** LangChain / LangGraph
* **Interface (UI):** Streamlit
* **LLM (Cérebro):** Google Gemini 1.5 Pro (devido à sua janela de contexto gigante, perfeito para ler vários READMEs simultaneamente).

## 2. Fluxo de Entrada e Saída
* **Entrada:** 
  1. Descrição da Vaga copiada e colada livremente pelo usuário (evita problemas com bloqueios anti-bot na PoC).
  2. Currículo Base (Markdown ou Texto).
  3. Nome de usuário do GitHub.
* **Saída:** O currículo gerado e otimizado será apresentado na tela do Streamlit em formato Markdown, permitindo que o usuário edite, copie, ou imprima como PDF usando o navegador.

## 3. O Grafo de Agentes (LangGraph)
O sistema usará um **Fluxo Cíclico com Validação Estruturada**. Isso garante previsibilidade (uma linha de montagem clara), mas com um loop de "controle de qualidade".

### Nós (Nodes) do Grafo:
1. **Job Analyzer (Analisador de Vaga):**
   * Lê a vaga colada pelo usuário.
   * Extrai os principais requisitos técnicos, ferramentas e soft skills.
2. **GitHub Researcher (Buscador do GitHub):**
   * Faz requisição à API do GitHub e lista todos os repositórios públicos.
   * Seleciona os repositórios mais aderentes aos requisitos (olhando nome e linguagens).
   * Baixa os arquivos `README.md` dos repositórios filtrados.
3. **Resume Generator (Gerador de Currículo):**
   * Recebe o currículo base, a análise da vaga e os READMEs.
   * Escreve uma nova versão do currículo, injetando uma seção "Projetos em Destaque" com base nas evidências reais do GitHub e ajustando as palavras-chave gerais.
4. **Quality Reviewer (Revisor Crítico):**
   * Inspeciona o currículo final comparando-o com o currículo original e a API do GitHub.
   * Verifica se há **alucinações** (inventou algo?) ou se esqueceu palavras-chave importantes.
   * **Decisão (Edge):** Se aprovado, finaliza o processo. Se reprovado (encontrou erro), devolve para o Gerador com feedback para corrigir (com um limite de 2 a 3 tentativas).

## 4. Estratégia do GitHub
Para lidar com usuários que têm muitos projetos, o fluxo será inteligente:
* O sistema fará um primeiro filtro baseado nos metadados (linguagem principal e descrição curta).
* Em seguida, apenas os `README.md` dos projetos mais promissores serão baixados na íntegra para serem enviados ao Gemini. (Embora o Gemini 1.5 Pro tenha contexto de sobra, isso reduzirá o tempo de execução e espera).
