import re
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import List, Optional
from src.core import config
import requests
import base64
from langchain_core.messages import HumanMessage, SystemMessage

class JobAnalysis(BaseModel):
    keywords: List[str] = Field(description="Principais palavras-chave, soft-skills e conceitos importantes da vaga.")
    technologies: List[str] = Field(description="Ferramentas, linguagens e frameworks técnicos exigidos ou desejados.")
    language: str = Field(default="pt", description="Idioma detectado da vaga, ex: 'en' para inglês, 'pt' para português, 'es' para espanhol.")

def job_analyzer(state: dict) -> dict:
    """
    Analisa a descrição da vaga e extrai palavras-chave, tecnologias e o idioma predominante.
    """
    job_description = state.get("job_description", "")
    
    if not job_description:
        return {"job_keywords": [], "job_technologies": [], "job_language": "pt"}
    
    try:
        llm = ChatGoogleGenerativeAI(model=config.GEMINI_MODEL, temperature=0)
        structured_llm = llm.with_structured_output(JobAnalysis)
        
        prompt = PromptTemplate.from_template(
            "Você é um recrutador especialista. Analise a seguinte vaga de emprego "
            "e extraia as principais tecnologias, palavras-chave comportamentais/conceituais "
            "e identifique o idioma principal da vaga ('en' para inglês, 'pt' para português, etc.).\n\n"
            "Vaga:\n{job_description}"
        )
        
        chain = prompt | structured_llm
        result = chain.invoke({"job_description": job_description})
        detected_lang = (result.language or "pt").lower().strip()
        if "en" in detected_lang:
            lang_code = "en"
        elif "es" in detected_lang:
            lang_code = "es"
        else:
            lang_code = "pt"

        return {
            "job_keywords": result.keywords,
            "job_technologies": result.technologies,
            "job_language": lang_code
        }
    except Exception as e:
        print(f"Erro no Job Analyzer: {e}")
        return {"job_keywords": [], "job_technologies": [], "job_language": "pt"}

def github_researcher(state: dict) -> dict:
    """
    Busca repositórios públicos do usuário no GitHub e extrai READMEs 
    dos repositórios que tenham as linguagens/tecnologias buscadas pela vaga.
    """
    username = (state.get("github_username") or "").strip()
    technologies = [t.lower() for t in state.get("job_technologies", [])]
    
    if not username:
        return {"github_repos": [], "github_readmes": {}}

    # Validação do nome de usuário do GitHub (alfanumérico com hifens simples internos, max 39 chars)
    if not re.match(r"^[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$", username):
        print(f"Nome de usuário GitHub inválido ou potencialmente inseguro: '{username}'")
        return {"github_repos": [], "github_readmes": {}}
        
    headers = {}
    token = config.GITHUB_TOKEN
    if token and "your_github_token_here" not in token:
        headers["Authorization"] = f"Bearer {token}"
        
    repos_url = f"https://api.github.com/users/{username}/repos?type=public&sort=updated&per_page=30"
    request_timeout = (5.0, 10.0)
    
    try:
        response = requests.get(repos_url, headers=headers, timeout=request_timeout)
        if response.status_code != 200:
            print(f"Erro ao acessar GitHub: {response.status_code}")
            return {"github_repos": [], "github_readmes": {}}
            
        repos = response.json()
        selected_repos = []
        readmes = {}
        
        # Filtra os repositórios mais promissores
        for repo in repos:
            repo_lang = (repo.get("language") or "").lower()
            
            if not technologies or repo_lang in technologies or any(t in str(repo.get("description", "")).lower() for t in technologies):
                selected_repos.append({
                    "name": repo["name"],
                    "description": repo.get("description", ""),
                    "language": repo.get("language"),
                    "url": repo["html_url"],
                    "default_branch": repo["default_branch"]
                })
                
                if len(selected_repos) >= 3:
                    break
                    
        for repo in selected_repos:
            repo_name = repo["name"]
            # Validação do nome do repositório para evitar path traversal ou caracteres de controle
            if not re.match(r"^[a-zA-Z0-9_.-]+$", repo_name):
                continue
                
            readme_url = f"https://api.github.com/repos/{username}/{repo_name}/readme"
            try:
                readme_resp = requests.get(readme_url, headers=headers, timeout=request_timeout)
                if readme_resp.status_code == 200:
                    content_b64 = readme_resp.json().get("content", "")
                    content_str = base64.b64decode(content_b64).decode("utf-8", errors="replace")
                    readmes[repo_name] = content_str
            except Exception as e:
                print(f"Erro ao baixar README de {repo_name}: {e}")
                
        return {
            "github_repos": selected_repos,
            "github_readmes": readmes
        }
        
    except Exception as e:
        print(f"Erro no GitHub Researcher: {e}")
        return {"github_repos": [], "github_readmes": {}}

def resume_generator(state: dict) -> dict:
    """
    Gera um novo currículo em Markdown com formatação de alta fidelidade e aderência ATS,
    seguindo o padrão estrutural canônico com tabela de habilidades e bullets de impacto.
    """
    base_resume = state.get("base_resume_md", "")
    job_desc = state.get("job_description", "")
    github_repos = state.get("github_repos", [])
    readmes = state.get("github_readmes", {})
    feedback = state.get("reviewer_feedback", "")
    job_language = state.get("job_language", "pt")
    
    llm = ChatGoogleGenerativeAI(model=config.GEMINI_MODEL, temperature=0.2)
    
    portfolio_context = ""
    for repo in github_repos:
        name = repo["name"]
        desc = repo.get("description", "")
        lang = repo.get("language", "")
        readme = readmes.get(name, "")
        portfolio_context += f"\n### Repositório: {name}\nLinguagem: {lang}\nDescrição: {desc}\nREADME:\n{readme[:1000]}\n"
        
    is_english = (job_language == "en")
    lang_directive = "em INGLÊS (English)" if is_english else "em PORTUGUÊS"
    
    # Rótulos canônicos de seções conforme o idioma
    sec_summary = "PROFESSIONAL SUMMARY" if is_english else "RESUMO PROFISSIONAL"
    sec_skills = "TECHNICAL SKILLS" if is_english else "HABILIDADES TÉCNICAS"
    sec_experience = "WORK EXPERIENCE" if is_english else "EXPERIÊNCIA PROFISSIONAL"
    sec_projects = "KEY PROJECTS" if is_english else "PROJETOS EM DESTAQUE"
    sec_education = "EDUCATION" if is_english else "FORMAÇÃO ACADÊMICA"
    sec_certifications = "CERTIFICATIONS" if is_english else "CURSOS E CERTIFICAÇÕES"
    sec_languages = "LANGUAGES" if is_english else "IDIOMAS"

    system_prompt = f"""Você é um especialista em recrutamento executivo de tecnologia e sistemas ATS.
Sua missão é reescrever o currículo base em Markdown de ALTA FIDELIDADE e PADRONIZAÇÃO EXECUTIVA {lang_directive}.

ESTRUTURA OBRIGATÓRIA DO CURRÍCULO (Siga RIGOROSAMENTE este modelo):

# [Nome Completo do Candidato]
### [Cargo Alvo / Especialidade Relevante para a Vaga]
[Cidade, UF / País] | [Email] | [LinkedIn] | [GitHub]

## {sec_summary}
[Um único parágrafo denso e de alto impacto destacando senioridade, stack tecnológica principal alinhada à vaga, experiências em projetos de larga escala/escalabilidade, Clean Architecture/SOLID e diferenciais técnicos reais].

## {sec_skills}
| Categoria | Tecnologias & Conceitos |
| :--- | :--- |
| **Back-end & Arquitetura:** | [Node.js, NestJS, TypeScript, Python, RESTful APIs, Microsserviços, Clean Architecture, SOLID, Design Patterns...] |
| **Front-end & Mobile:** | [React, Next.js, React Native, TypeScript, Tailwind CSS, UI/UX Responsivo...] |
| **IA, RAG & Agentes:** | [RAG, Embeddings, Vector Stores, LLMs Locais, Tool Calling, LangGraph...] |
| **Mensageria & Filas:** | [RabbitMQ, Filas, Comunicação Assíncrona...] |
| **Banco de Dados & ORM:** | [PostgreSQL, MongoDB, Prisma, TypeORM...] |
| **DevOps & Ferramentas:** | [Docker, Git, GitHub Actions (CI/CD), Linux, Jira / Scrum...] |

*(Adapte as categorias se houver especialidades relevantes, mas mantenha a tabela de 2 colunas).*

## {sec_experience}
Para CADA experiência relevante:
### [Empresa / Órgão — Nome do Projeto]
*[Cargo] | [Período, ex: Mês Ano – Presente] | [Localidade (Remoto ou Presencial)]*
- ● **[Impacto / Dimensão]:** [Verbo de ação forte + escopo + resultado mensurável ou de escala]
- ● **[Back-end & Arquitetura]:** [Tecnologias e padrões técnicos aplicados]
- ● **[Front-end & UX]:** [Interface e usabilidade se aplicável]
- ● **[Persistência & Integração]:** [Bancos de dados, APIs ou documentação técnica padronizada]
- ● **[Processos Ágeis & Qualidade]:** [Scrum, Code Review, CI/CD]

## {sec_projects}
Para CADA projeto destacado (enriqueça com os repositórios do GitHub fornecidos):
### [Nome do Projeto] — [Subtítulo / Proposta de Valor]
*[Stack tecnológica separada por vírgulas]*
- ● **[Pilar Arquitetural 1]:** [Explicação técnica profunda de implementação e features]
- ● **[Pilar Arquitetural 2]:** [Segundo diferencial técnico comprovado]
- ● **[Repositório GitHub]:** [Link direto, ex: https://github.com/usuario/repo]

## {sec_education}
### [Grau e Curso]
*[Instituição de Ensino] | [Ano de Conclusão / Previsão]*
[Ênfase ou destaques acadêmicos relevantes se houver]

## {sec_certifications}
- ● **[Nome do Curso/Certificação]:** [Instituição] ([Ano]) | [Código/Link se houver]

## {sec_languages}
[Idioma 1]: Nativo | [Idioma 2]: Fluente / Avançado | [Idioma 3]: Intermediário

REGRAS CRÍTICAS:
1. Formato dos Bullets: NUNCA use marcadores simples sem negrito. SEMPRE use `- ● **[Tópico de Impacto]:** [Ação...]`.
2. Tabela de Habilidades: SEMPRE formate a seção de habilidades como a tabela Markdown acima com as categorias alinhadas à esquerda.
3. Alinhamento ATS: Integre naturalmente as palavras-chave exigidas pela vaga nas descrições de cargo e habilidades.
4. NUNCA ALUCINE: Não invente empregos, empresas ou repositórios que o candidato não possui.
5. Retorne APENAS o Markdown limpo e completo."""

    if feedback:
        system_prompt += f"\n\nATENÇÃO! O revisor rejeitou a versão anterior pelo seguinte motivo: {feedback}. Ajuste o currículo rigorosamente conforme esse feedback."
        
    user_prompt = (
        f"--- VAGA ---\n{job_desc}\n\n"
        f"--- CURRÍCULO BASE ---\n{base_resume}\n\n"
        f"--- PORTFÓLIO GITHUB ---\n{portfolio_context}"
    )
    
    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        return {"generated_resume_md": response.content}
    except Exception as e:
        print(f"Erro no Resume Generator: {e}")
        return {"generated_resume_md": base_resume}

class ReviewResult(BaseModel):
    approved: bool = Field(description="True se o currículo NÃO tiver alucinações e seguir o padrão estrutural, False caso contrário.")
    feedback: str = Field(description="Feedback caso reprovado, explicando o que deve ser corrigido.")

def quality_reviewer(state: dict) -> dict:
    """
    Revisa o currículo gerado para garantir conformidade estrutural, padrão dos bullets
    e ausência de informações técnicas ou cargos inventados.
    """
    generated = state.get("generated_resume_md", "")
    base_resume = state.get("base_resume_md", "")
    github_repos = state.get("github_repos", [])
    readmes = state.get("github_readmes", {})
    attempts = state.get("review_attempts", 0)
    
    if attempts >= 2:
        return {
            "reviewer_approved": False,
            "reviewer_feedback": "Limite de tentativas de revisão atingido. Prosseguindo com versão atual.",
            "review_attempts": attempts + 1
        }
        
    portfolio_context = ""
    for repo in github_repos:
        name = repo["name"]
        readme = readmes.get(name, "")
        portfolio_context += f"\n### Repositório: {name}\nREADME:\n{readme[:500]}\n"
        
    try:
        llm = ChatGoogleGenerativeAI(model=config.GEMINI_MODEL, temperature=0)
        structured_llm = llm.with_structured_output(ReviewResult)
        
        prompt = PromptTemplate.from_template(
            "Você é um auditor rigoroso de currículos técnicos de alto padrão.\n"
            "Avalie o currículo gerado segundo dois critérios:\n"
            "1. **Alucinações:** O candidato inventou tecnologias ou ferramentas nos projetos que NÃO constam no currículo base nem nos READMEs?\n"
            "2. **Conformidade de Layout:** O currículo possui a tabela de 'HABILIDADES TÉCNICAS' e os bullet points no padrão '● **Tópico:** Ação...'?\n\n"
            "--- CURRÍCULO BASE ---\n{base_resume}\n\n"
            "--- READMEs FORNECIDOS ---\n{portfolio_context}\n\n"
            "--- CURRÍCULO GERADO (Para revisão) ---\n{generated}\n\n"
            "Retorne aprovado (True) se estiver tudo limpo e bem formatado, ou (False) se houver problemas, explicando no feedback."
        )
        
        chain = prompt | structured_llm
        result = chain.invoke({
            "base_resume": base_resume,
            "portfolio_context": portfolio_context,
            "generated": generated
        })
        return {
            "reviewer_approved": result.approved,
            "reviewer_feedback": result.feedback,
            "review_attempts": attempts + 1
        }
    except Exception as e:
        print(f"Erro no Quality Reviewer: {e}")
        return {
            "reviewer_approved": False,
            "reviewer_feedback": f"Falha na API de auditoria de qualidade: {e}. Revise o conteúdo manualmente.",
            "review_attempts": attempts + 1
        }

def cover_letter_generator(state: dict) -> dict:
    """
    Gera uma Cover Letter (Carta de Apresentação) personalizada, convincente e alinhada
    com a vaga e o portfólio GitHub, escrita no mesmo idioma da vaga.
    """
    job_desc = state.get("job_description", "")
    generated_resume = state.get("generated_resume_md", "")
    github_repos = state.get("github_repos", [])
    job_language = state.get("job_language", "pt")
    
    repos_summary = ", ".join([r.get("name", "") for r in github_repos if r.get("name")])
    
    lang_directive = "em PORTUGUÊS"
    if job_language == "en":
        lang_directive = "em INGLÊS (English)"
    elif job_language == "es":
        lang_directive = "em ESPANHOL (Español)"
        
    system_prompt = (
        "Você é um especialista sênior em redação de cartas de apresentação (Cover Letters) e aconselhamento de carreira.\n"
        f"Escreva uma Cover Letter profissional, elegante e persuasiva {lang_directive} adaptada para a vaga descrita.\n\n"
        "Diretrizes:\n"
        "1. **Abertura**: Saudação formal ao time de recrutamento/gerente de contratação e apresentação com entusiasmo pela vaga.\n"
        "2. **Conexão Técnica & Experiência**: Destaque as principais realizações do candidato pertinentes à vaga, citando experiência prática e projetos reais.\n"
        "3. **Fit Cultural & Valor**: Mostre compreensão dos objetivos da empresa e como o candidato resolverá os desafios propostos.\n"
        "4. **Fechamento**: Conclusão cordial solicitando uma entrevista/conversa técnica.\n"
        "5. **Alinhamento Rigoroso**: NÃO invente informações que não estejam presentes no currículo do candidato.\n"
        "- Retorne APENAS o texto da carta de apresentação formatado em Markdown limpo."
    )
    
    user_prompt = (
        f"--- VAGA ---\n{job_desc}\n\n"
        f"--- CURRÍCULO DO CANDIDATO ---\n{generated_resume}\n\n"
        f"--- PROJETOS DESTACADOS GITHUB ---\n{repos_summary}"
    )
    
    try:
        llm = ChatGoogleGenerativeAI(model=config.GEMINI_MODEL, temperature=0.3)
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        return {"generated_cover_letter_md": response.content}
    except Exception as e:
        print(f"Erro no Cover Letter Generator: {e}")
        fallback_letter = (
            "Dear Hiring Team,\n\nI am writing to express my enthusiasm for this position. "
            "Please review my attached resume and GitHub projects.\n\nBest regards."
            if job_language == "en" else
            "Prezado time de recrutamento,\n\nEscrevo para manifestar meu grande interesse nesta oportunidade. "
            "Por favor, confira meu currículo anexado e projetos no GitHub.\n\nAtenciosamente."
        )
        return {"generated_cover_letter_md": fallback_letter}
