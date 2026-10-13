from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import List
from src.core import config

class JobAnalysis(BaseModel):
    keywords: List[str] = Field(description="Principais palavras-chave, soft-skills e conceitos importantes da vaga.")
    technologies: List[str] = Field(description="Ferramentas, linguagens e frameworks técnicos exigidos ou desejados.")

def job_analyzer(state: dict) -> dict:
    """
    Analisa a descrição da vaga e extrai palavras-chave e tecnologias.
    """
    job_description = state.get("job_description", "")
    
    if not job_description:
        return {"job_keywords": [], "job_technologies": []}
    
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0)
    structured_llm = llm.with_structured_output(JobAnalysis)
    
    prompt = PromptTemplate.from_template(
        "Você é um recrutador especialista. Analise a seguinte vaga de emprego "
        "e extraia as principais tecnologias e palavras-chave comportamentais/conceituais.\n\n"
        "Vaga:\n{job_description}"
    )
    
    chain = prompt | structured_llm
    
    try:
        result = chain.invoke({"job_description": job_description})
        return {
            "job_keywords": result.keywords,
            "job_technologies": result.technologies
        }
    except Exception as e:
        print(f"Erro no Job Analyzer: {e}")
        return {"job_keywords": [], "job_technologies": []}

import requests
import base64

def github_researcher(state: dict) -> dict:
    """
    Busca repositórios públicos do usuário no GitHub e extrai READMEs 
    dos repositórios que tenham as linguagens/tecnologias buscadas pela vaga.
    """
    username = state.get("github_username", "")
    technologies = [t.lower() for t in state.get("job_technologies", [])]
    
    if not username:
        return {"github_repos": [], "github_readmes": {}}
        
    headers = {}
    token = config.GITHUB_TOKEN
    if token and "your_github_token_here" not in token:
        headers["Authorization"] = f"token {token}"
        
    repos_url = f"https://api.github.com/users/{username}/repos?type=public&sort=updated&per_page=30"
    
    try:
        response = requests.get(repos_url, headers=headers)
        if response.status_code != 200:
            print(f"Erro ao acessar GitHub: {response.status_code}")
            return {"github_repos": [], "github_readmes": {}}
            
        repos = response.json()
        selected_repos = []
        readmes = {}
        
        # Filtra os repositórios mais promissores
        for repo in repos:
            repo_lang = (repo.get("language") or "").lower()
            
            # Se a linguagem do repo estiver nas tecnologias da vaga, ou se a vaga não especificar tecnologia
            if not technologies or repo_lang in technologies or any(t in str(repo.get("description", "")).lower() for t in technologies):
                selected_repos.append({
                    "name": repo["name"],
                    "description": repo.get("description", ""),
                    "language": repo.get("language"),
                    "url": repo["html_url"],
                    "default_branch": repo["default_branch"]
                })
                
                # Limitamos a 3 repositórios para não sobrecarregar o prompt e as requisições
                if len(selected_repos) >= 3:
                    break
                    
        # Para os repositórios selecionados, tenta baixar o README
        for repo in selected_repos:
            readme_url = f"https://api.github.com/repos/{username}/{repo['name']}/readme"
            try:
                readme_resp = requests.get(readme_url, headers=headers)
                if readme_resp.status_code == 200:
                    content_b64 = readme_resp.json().get("content", "")
                    content_str = base64.b64decode(content_b64).decode("utf-8")
                    readmes[repo["name"]] = content_str
            except Exception as e:
                print(f"Erro ao baixar README de {repo['name']}: {e}")
                
        return {
            "github_repos": selected_repos,
            "github_readmes": readmes
        }
        
    except Exception as e:
        print(f"Erro no GitHub Researcher: {e}")
        return {"github_repos": [], "github_readmes": {}}

from langchain_core.messages import HumanMessage, SystemMessage

def resume_generator(state: dict) -> dict:
    """
    Gera um novo currículo em Markdown, mesclando o currículo original,
    os requisitos da vaga e as evidências do GitHub.
    """
    base_resume = state.get("base_resume_md", "")
    job_desc = state.get("job_description", "")
    github_repos = state.get("github_repos", [])
    readmes = state.get("github_readmes", {})
    feedback = state.get("reviewer_feedback", "")
    
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.3)
    
    portfolio_context = ""
    for repo in github_repos:
        name = repo["name"]
        desc = repo.get("description", "")
        lang = repo.get("language", "")
        readme = readmes.get(name, "")
        portfolio_context += f"\\n### Repositório: {name}\\nLinguagem: {lang}\\nDescrição: {desc}\\nREADME:\\n{readme[:1000]}\\n"
        
    system_prompt = (
        "Você é um especialista em recrutamento de tecnologia e sistemas ATS (Applicant Tracking Systems). "
        "Sua tarefa é REESCREVER COMPLETAMENTE e OTIMIZAR o currículo base do candidato em formato Markdown "
        "para garantir que ele passe nos filtros de ATS e impressione os recrutadores para a vaga fornecida.\\n\\n"
        "Regras estritas de Otimização:\\n"
        "1. **Adequação ATS**: Use as MESMAS palavras-chave e jargões encontrados na vaga. Integre essas palavras de forma natural no Resumo Profissional e nas Experiências.\\n"
        "2. **Estrutura Limpa**: Use seções com títulos padrões e reconhecíveis por ATS (ex: 'Resumo Profissional', 'Experiência Profissional', 'Educação', 'Habilidades Técnicas', 'Projetos em Destaque').\\n"
        "3. **Impacto e Ação**: Reescreva os bullet points das experiências usando verbos de ação fortes (ex: Desenvolveu, Otimizou, Liderou) e inclua resultados quantificáveis quando possível, focado no que a vaga pede.\\n"
        "4. **Projetos em Destaque**: Adicione ou melhore uma seção 'Projetos em Destaque' usando os repositórios do GitHub fornecidos, provando na prática o conhecimento nas tecnologias exigidas.\\n"
        "5. **NÃO ALUCINE**: NUNCA invente empregos, cargos, ferramentas, habilidades ou métricas que o candidato não possui no currículo original ou no portfólio GitHub.\\n"
        "- Retorne APENAS o currículo em Markdown válido.\\n"
    )
    
    if feedback:
        system_prompt += f"\\n\\nATENÇÃO! O revisor rejeitou a versão anterior pelo seguinte motivo: {feedback}. Corrija o currículo focando nisso."
        
    user_prompt = (
        f"--- VAGA ---\\n{job_desc}\\n\\n"
        f"--- CURRÍCULO BASE ---\\n{base_resume}\\n\\n"
        f"--- PORTFÓLIO GITHUB ---\\n{portfolio_context}"
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
    approved: bool = Field(description="True se o currículo NÃO tiver alucinações e estiver bom, False caso contrário.")
    feedback: str = Field(description="Feedback caso reprovado, explicando o que deve ser removido ou alterado.")

def quality_reviewer(state: dict) -> dict:
    """
    Revisa o currículo gerado para garantir que não contém ferramentas ou
    projetos inventados que não existiam no currículo base ou nos READMEs.
    """
    generated = state.get("generated_resume_md", "")
    base_resume = state.get("base_resume_md", "")
    github_repos = state.get("github_repos", [])
    readmes = state.get("github_readmes", {})
    attempts = state.get("review_attempts", 0)
    
    # Se já tentou muitas vezes, aprova o que tem para não ficar em loop
    if attempts >= 2:
        return {"reviewer_approved": True, "reviewer_feedback": "Aprovado por limite de tentativas", "review_attempts": attempts + 1}
        
    portfolio_context = ""
    for repo in github_repos:
        name = repo["name"]
        readme = readmes.get(name, "")
        portfolio_context += f"\\n### Repositório: {name}\\nREADME:\\n{readme[:500]}\\n"
        
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0)
    structured_llm = llm.with_structured_output(ReviewResult)
    
    prompt = PromptTemplate.from_template(
        "Você é um auditor rigoroso de currículos. O candidato gerou uma nova versão do currículo, "
        "mas você deve verificar se ele inventou alguma ferramenta técnica ou projeto nos 'Projetos em Destaque' "
        "que NÃO consta no currículo base e NÃO consta nos READMEs fornecidos.\\n\\n"
        "--- CURRÍCULO BASE ---\\n{base_resume}\\n\\n"
        "--- READMEs FORNECIDOS ---\\n{portfolio_context}\\n\\n"
        "--- CURRÍCULO GERADO (Para revisão) ---\\n{generated}\\n\\n"
        "Avalie o currículo gerado. Há alucinações claras? Retorne aprovado (True) se estiver tudo limpo, "
        "ou (False) se houver problemas, detalhando no feedback."
    )
    
    chain = prompt | structured_llm
    
    try:
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
        # Em caso de falha de API, aprova por padrão para não quebrar o fluxo
        return {"reviewer_approved": True, "reviewer_feedback": f"Erro de API: {e}", "review_attempts": attempts + 1}

