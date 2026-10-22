# Spec Delta: resume-optimization

## MODIFIED Requirements

### Requirement: Buscar evidências no GitHub
O sistema SHALL consultar a API do GitHub do usuário para buscar repositórios públicos próprios (ignorando forks), ranqueando-os por aderência de tecnologias, linguagens e tópicos em relação à vaga, e registrando eventuais falhas de comunicação da API no estado para visualização do usuário.

#### Scenario: Repositório correspondente encontrado
- **WHEN** a vaga exige "Python" e o usuário possui um repositório Python
- **THEN** o sistema seleciona o README deste repositório como evidência

#### Scenario: Repositórios ranqueados por relevância
- **WHEN** o usuário possui múltiplos repositórios públicos
- **THEN** o sistema ignora forks e seleciona com prioridade os projetos cujas linguagens, tópicos e descrições apresentem maior pontuação de correspondência com as tecnologias da vaga

#### Scenario: Falha de comunicação ou limite de requisições da API
- **WHEN** a API do GitHub retornar erro HTTP (ex: 403 por rate limit, 404 por usuário inexistente ou timeout)
- **THEN** o sistema registra a mensagem de falha na lista de erros do estado sem interromper a execução dos demais agentes

### Requirement: Revisar currículo gerado
O sistema SHALL realizar verificações determinísticas de conformidade estrutural, integridade de repositórios e presença de termos ATS no currículo gerado, rejeitando alucinações e formatações inválidas antes de recorrer à auditoria por modelo de linguagem.

#### Scenario: Identificação de alucinação
- **WHEN** o currículo gerado cita uma ferramenta que não está no currículo original nem no GitHub
- **THEN** o revisor rejeita o currículo e solicita correção ao gerador

#### Scenario: Verificação determinística de integridade
- **WHEN** o currículo gerado contiver links de repositórios que não constam na lista obtida do GitHub ou estrutura de tabela fora do padrão
- **THEN** o revisor rejeita o currículo gerado e emite feedback corretivo imediato sem gastar chamadas de LLM

#### Scenario: Revisão em modo econômico
- **WHEN** a execução estiver configurada em modo econômico (`strict_review=False`)
- **THEN** o sistema valida o currículo e gera o diagnóstico de aderência de termos utilizando apenas as regras determinísticas, sem invocar o modelo auditor

## ADDED Requirements

### Requirement: Higienizar e filtrar conteúdo de READMEs
O sistema SHALL remover elementos visuais e metadados irrelevantes de READMEs (como badges, imagens e seções triviais de licença) e fornecer um extrato técnico estruturado com limite controlado de caracteres para o gerador de currículo e carta de apresentação.

#### Scenario: Extração limpa de contexto técnico
- **WHEN** um repositório contém badges, imagens e texto longo de instalação em seu README
- **THEN** o sistema filtra esses blocos e envia ao modelo apenas a descrição do projeto, funcionalidades e stack técnica respeitando o teto de caracteres definido
