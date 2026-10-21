# Proposta de Projeto: Otimizador Multi-Agente de Currículos

---

### Nome dos Integrantes do Grupo
* [Seu Nome Completo] *(adicione os demais integrantes aqui)*

---

### Título Provisório do Projeto
* **GitMatch (CV Nitro):** Otimizador Inteligente de Currículos com Base em Portfólio GitHub, ATS e Persistência em Nuvem
* **Aplicação em Produção (Deploy Ativo):** [https://cvnitro-xzvgi43qkmsbovbt87h9bz.streamlit.app/](https://cvnitro-xzvgi43qkmsbovbt87h9bz.streamlit.app/)

---

### Problema Concreto
* Candidatos perdem tempo adaptando manualmente seus currículos para cada vaga e frequentemente falham em destacar os projetos práticos certos que comprovam os requisitos exigidos pelos sistemas de triagem (ATS).

---

### Exemplo Concreto de Entrada
* Texto ou link da descrição da vaga (Job Description), arquivo do currículo base (texto/Markdown) e o nome de usuário do GitHub do candidato.

---

### Resultado ou Comportamento Esperado
* Um currículo final completo em Markdown/PDF otimizado para a vaga, com palavras-chave alinhadas ao ATS e destacando automaticamente os repositórios reais mais pertinentes do GitHub do usuário.

---

### Critérios de Sucesso
* **100% de precisão factual:** Zero ferramentas ou repositórios inventados fora do histórico real do candidato.
* **Relevância prática:** Inclusão e contextualização justificada de 2 a 3 repositórios com alta aderência técnica à vaga.
* **Eficiência:** Redução do tempo de customização de currículo de ~40 minutos para menos de 2 minutos.

---

### Qual é a solução mais simples que vocês tentariam primeiro, sem usar uma arquitetura agentiva?
* Um script simples enviando um prompt único para um LLM contendo o texto da vaga e o currículo base colados juntos, solicitando a reescrita com inclusão de palavras-chave.

---

### Que característica do problema faz vocês suspeitarem que uma solução agentiva pode superar o baseline?
* O fluxo exige planejamento em etapas e integração com ferramentas externas: extração do texto da vaga, consulta à API do GitHub (inspeção de READMEs e linguagens), matching deliberado de requisitos com evidências reais e uma etapa de revisão crítica para evitar alucinações.

---

### Ambiente e Capacidades
* **API do GitHub:** Leitura de metadados, linguagens e arquivos README dos repositórios públicos.
* **Leitor HTTP / Web Scraping:** Extração de descrições de vagas a partir de URLs.
* **LLM com Function Calling:** Geração de saídas estruturadas (JSON/Pydantic) e orquestração de ferramentas.

---

### Qual é o menor experimento que vocês conseguem executar para testar se esta ideia vale continuar?
* Uma Prova de Conceito (PoC) via CLI: fornecer 1 vaga em texto e 1 usuário do GitHub; o sistema consome a API do GitHub, seleciona os repositórios compatíveis e gera uma seção de "Projetos em Destaque" coerente e sem dados inventados.

---

### Que resultado faria vocês concluírem que uma arquitetura agentiva NÃO vale a complexidade adicional neste problema?
* Se a orquestração multi-agente apresentar alta taxa de alucinação, se a latência/custo por execução inviabilizar o uso, ou se um prompt único direto entregar uma qualidade técnica e precisão equivalentes sem justificar a infraestrutura agentiva.