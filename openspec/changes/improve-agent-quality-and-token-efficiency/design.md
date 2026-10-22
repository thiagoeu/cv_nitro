# Design: improve-agent-quality-and-token-efficiency

## Context
Ver `proposal.md` para motivação e problemas identificados no fluxo atual de nós do LangGraph.
Atualmente, as chamadas de LLM ocorrem em cascata: `job_analyzer` → `github_researcher` (chamada HTTP pura) → `resume_generator` → `quality_reviewer` (chamada LLM com structured output ou bypass sem validação) → `cover_letter_generator`.
A principal oportunidade de elevar a qualidade e economizar tokens consiste em deslocar a inteligência de ranqueamento, sanitização de dados e auditoria estrutural para código determinístico (Python puro), reservando a criatividade e geração de linguagem natural da LLM apenas para a reescrita executiva e fechamento persuasivo.

## Goals / Non-Goals

**Goals:**
- Maximização da qualidade das evidências de projetos do GitHub sem gastar tokens com LLM para triagem.
- Eliminação do desperdício de tokens em chamadas de auditoria do revisor quando houver falhas sintáticas ou alucinações de links facilmente detectáveis por código.
- Garantia de que o modo econômico (`strict_review=False`) execute verificações reais e retorne métricas autênticas de ATS com 0 tokens de LLM.
- Aumento do contexto útil dos READMEs (de 400 para ~1.200 caracteres úteis por repo selecionado), limpando ruídos (badges, links, licenças).
- Diagnóstico de ATS baseado em contagem e cobertura comprovável de termos e integridade estrutural.

**Non-Goals:**
- Não criar novos agentes de terceiros ou frameworks complexos além do LangGraph existente.
- Não refazer a interface gráfica Streamlit, mantendo o consumo das variáveis existentes (`state["diagnostic"]`, `state["errors"]`, `state["reviewer_feedback"]`).
- Não alterar os modelos padrão configurados em `config.py` nem forçar chamadas adicionais de LLM.

## Decisions

### 1. Ranqueamento Determinístico de Repositórios no GitHub Researcher
- **Decisão:** Calcular uma pontuação heurística ponderada para cada repositório do usuário antes da seleção:
  - Repositório é fork: desqualificado imediatamente (score 0).
  - Correspondência da linguagem principal: +3 pontos.
  - Correspondência de tópicos/tags (`topics` da API GitHub): +2 pontos por tópico alinhado.
  - Correspondência de palavras-chave na descrição com word boundaries (`\btermo\b` case-insensitive para evitar falsos positivos com `c`, `r`, `go`): +1 ponto por termo.
  - Popularidade e manutenção: log de `stargazers_count` e bônus para atualizações nos últimos 12 meses.
- **Alternativa rejeitada:** Usar um agente LLM para ranquear os repositórios. Rejeitado para evitar latência extra e consumo desnecessário de tokens.

### 2. Sanitizador de READMEs (Higienização Inteligente)
- **Decisão:** Criar a função utilitária `_clean_readme(raw_markdown: str, max_chars: int = 1200) -> str`.
  - Remove blocos HTML, badges de shields.io / build / codecov, tags `<img>`, seções inteiras de `License`, `Contributing`, e comandos triviais de instalação (`git clone`, `npm install`).
  - Preserva parágrafos introdutórios, tópicos de arquitetura, funcionalidades (`Features`) e stack tecnológica.
  - Limita a 1.200 caracteres limpos por repositório para o `resume_generator` e 300 caracteres para o resumo da `cover_letter_generator`.
- **Alternativa rejeitada:** Enviar o README bruto de 4.000 caracteres (desperdiça tokens com badges e licenças) ou manter em 400 caracteres (impede que o modelo compreenda o que o projeto realmente fez).

### 3. Revisor Híbrido em Duas Camadas (Tier 1 Determinístico + Tier 2 LLM)
- **Decisão:**
  - **Tier 1 (Determinístico - 0 tokens):**
    1. Checagem de integridade de links: todas as URLs `https://github.com/...` presentes no currículo gerado pertencem aos repositórios consultados?
    2. Checagem de placeholders residuais: detectar padrões como `<Nome>`, `<Email>`, `<Empresa>` ou colchetes não preenchidos.
    3. Checagem da tabela Markdown de habilidades: validação da linha separadora `| :--- | :--- |` e presença de pelo menos duas categorias.
    4. Mapeamento de termos ATS: busca exata/normalizada das tecnologias e palavras-chave da vaga no texto gerado.
  - **Execução em Modo Econômico (`strict_review=False`):**
    - Interrompe no Tier 1: calcula o score ATS com base nas métricas reais encontradas e aprova o currículo sem chamar o modelo, economizando centenas de tokens e vários segundos de latência.
  - **Execução em Modo Rigoroso (`strict_review=True`):**
    - Se o Tier 1 detectar link inventado ou placeholder não substituído, rejeita imediatamente (`approved=False`) com feedback cirúrgico direto para o gerador, sem gastar chamada de LLM.
    - Se o Tier 1 passar com sucesso, invoca o modelo de auditoria semântica fina (Tier 2).

### 4. Fórmula Transparente de Score ATS
- **Decisão:** Substituir notas heurísticas arbitrárias por cálculo determinístico:
  - `score = (0.50 * tech_coverage) + (0.25 * keyword_coverage) + (0.25 * structural_score)`
  - `tech_coverage`: proporção de tecnologias da vaga presentes no currículo (0 a 100).
  - `keyword_coverage`: proporção de palavras-chave comportamentais e conceitos presentes (0 a 100).
  - `structural_score`: 100 se tabela e seções obrigatórias estiverem íntegras; penalidade de 15 pontos por inconformidade.
  - Resultado final limitado entre 50 e 100 (ou proporcional à cobertura real).

### 5. Resumo Sintético de Projetos para a Cover Letter
- **Decisão:** Em vez de fornecer apenas o nome ou URLs cruas, formatar para a carta:
  `- <Nome>: <Linguagem> — <Descrição limpa de 1 frase>`
  Isso custa menos de 80 tokens no total e fornece ao modelo a essência para contextualizar a carta de apresentação com naturalidade.

## Risks / Trade-offs

- **[Risco]** Usuário com repositórios sem descrição ou sem tags no GitHub pode receber pontuação de ranqueamento baixa.
  - **Mitigação:** Critério de fallback que seleciona os repositórios mais recentes do usuário mesmo com pontuação zero se nenhum repo atingir pontuação positiva.
- **[Risco]** Vagas com poucos termos ou formatos atípicos de descrição.
  - **Mitigação:** Tratamento defensivo em divisões por zero e normalização de termos compostos (ex: "Node.js" vs "Node", "React.js" vs "React").
