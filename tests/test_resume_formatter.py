from src.core.resume_formatter import format_resume_to_html

def test_format_resume_to_html_full():
    sample_md = """# Thiago Barbosa de Araújo
### Desenvolvedor Full Stack
Campina Grande, PB | araujo.thiago1051@gmail.com | linkedin.com/in/thiago-araujo | github.com/thiagoeu

## RESUMO PROFISSIONAL
Desenvolvedor Full Stack com sólida experiência no ecossistema Node.js, NestJS e React.

## HABILIDADES TÉCNICAS
| Categoria | Tecnologias & Conceitos |
| :--- | :--- |
| **Back-end & Arquitetura:** | Node.js, NestJS, TypeScript, Python, Clean Architecture |
| **Front-end & Mobile:** | React 19, Next.js, Tailwind CSS |

## EXPERIÊNCIA PROFISSIONAL
### Ministério da Saúde / IFPB — Projeto e-SUS AF
*Desenvolvedor Full Stack Júnior | Agosto 2025 – Presente | Campina Grande, PB (Remoto)*
- ● **Impacto Nacional:** Atuação no desenvolvimento da plataforma e-SUS AF impactando 500 estabelecimentos.
- ● **Back-end & Arquitetura:** Construção de APIs RESTful com NestJS e SOLID.

## PROJETOS EM DESTAQUE
### RepoContext — Plataforma de Otimização de Código
*Next.js, React 19, TypeScript, Ollama*
- ● **Motor RAG & Busca Semântica:** Implementação de pipeline RAG 100% local.
- ● https://github.com/thiagoeu/repo-context

## FORMAÇÃO ACADÊMICA
### Bacharelado em Engenharia da Computação
*Instituto Federal da Paraíba (IFPB) | Conclusão Prevista: 2026*
"""

    html = format_resume_to_html(sample_md, "Thiago Barbosa de Araújo")
    
    # Validações estruturais e tipográficas
    assert "<h1 class='candidate-name'>Thiago Barbosa de Araújo</h1>" in html
    assert "Desenvolvedor Full Stack" in html
    assert "RESUMO PROFISSIONAL" in html
    assert "<table class='skills-table'>" in html
    assert "Back-end &amp; Arquitetura:" in html
    assert "Impacto Nacional:" in html
    assert "class='bullet-item'" in html
    assert "@media print" in html
    assert "window.print()" in html
    assert "https://github.com/thiagoeu/repo-context" in html

def test_format_resume_to_html_xss_sanitization():
    malicious_md = """# <script>alert('pwned')</script>
### <img src=x onerror=alert(1)>
Malicious City | bad<user>@evil.com | linkedin.com/in/<script> | [Click Me](javascript:alert(1))

## <svg onload=alert(2)>SEÇÃO MALICIOSA</svg>
Parágrafo com <iframe src='evil.com'></iframe> e **<script>negrito perigoso</script>**.

- ● **Ataque:** Tentativa de injeção com <img src='x' onerror='steal()'> e link https://safe.com/test?a=1&b=2
"""
    html = format_resume_to_html(malicious_md, "<script>doc_title</script>")

    # Garante que nenhuma tag executável de injeção sobreviveu sem escape
    assert "<script>" not in html
    assert "</script>" not in html
    assert "<img src=x onerror=alert(1)>" not in html
    assert "<svg onload" not in html
    assert "<iframe" not in html
    assert "javascript:alert(1)" not in html

    # Garante que os caracteres foram convertidos em entidades HTML seguras
    assert "&lt;script&gt;alert(&#x27;pwned&#x27;)&lt;/script&gt;" in html
    assert f"<title>&lt;script&gt;alert(&#x27;pwned&#x27;)&lt;/script&gt;</title>" in html
    assert "&lt;svg onload=alert(2)&gt;" in html
    assert "<strong>&lt;script&gt;negrito perigoso&lt;/script&gt;</strong>" in html
    assert "<a href='https://safe.com/test?a=1&amp;b=2'" in html

    # Testa fallback de doc_title quando não há H1
    html_fallback = format_resume_to_html("Parágrafo sem H1", "<script>fallback_title</script>")
    assert "<title>&lt;script&gt;fallback_title&lt;/script&gt;</title>" in html_fallback

