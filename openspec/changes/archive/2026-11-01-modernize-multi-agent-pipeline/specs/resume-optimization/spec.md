# Spec Delta

## MODIFIED Requirements

### Requirement: Buscar evidências no GitHub
O sistema SHALL listar repositórios públicos concorrentemente com a análise de vaga e permitir a obtenção detalhada de arquivos README sob demanda através de chamada de ferramenta (*tool-calling*) pelo gerador.

#### Scenario: Repositório correspondente encontrado
- **WHEN** a vaga exige "Python" e o usuário possui um repositório Python
- **THEN** o sistema classifica o repositório por pontuação de relevância e disponibiliza o extrato técnico sob demanda

#### Scenario: Repositórios ranqueados por relevância
- **WHEN** o usuário possui múltiplos repositórios públicos
- **THEN** o sistema ignora forks e seleciona com prioridade os projetos cujas linguagens, tópicos e descrições apresentem maior pontuação de correspondência com as tecnologias da vaga

#### Scenario: Falha de comunicação ou limite de requisições da API
- **WHEN** a API do GitHub retornar erro HTTP (ex: 403 por rate limit, 404 por usuário inexistente ou timeout)
- **THEN** o sistema registra a mensagem de falha na lista de erros do estado sem interromper a execução dos demais agentes

#### Scenario: Usuário com formato inválido
- **WHEN** o nome de usuário fornecido contém caracteres especiais inválidos ou tentativas de injeção
- **THEN** o sistema rejeita a chamada de rede e retorna lista vazia de repositórios de forma segura

#### Scenario: Timeout ou instabilidade na API externa
- **WHEN** a API do GitHub demorar mais que o tempo limite configurado (timeout)
- **THEN** o sistema aborta a requisição sem bloquear indefinidamente a aplicação

### Requirement: Revisar currículo gerado
O sistema SHALL revisar o currículo gerado contra alucinações e conformidade de layout, classificando falhas leves para refinamento cirúrgico de seção (*delta patching*) ou falhas graves para reescrita completa.

#### Scenario: Identificação de alucinação ou ajuste de seção
- **WHEN** o currículo gerado apresenta erro pontual de formatação ou de alinhamento em uma seção específica
- **THEN** o sistema aciona o refinamento cirúrgico da seção afetada sem reescrever o restante do documento

#### Scenario: Identificação de alucinação
- **WHEN** o currículo gerado cita uma ferramenta que não está no currículo original nem no GitHub
- **THEN** o revisor rejeita o currículo e solicita correção ao gerador

#### Scenario: Verificação determinística de integridade
- **WHEN** o currículo gerado contiver links de repositórios que não constam na lista obtida do GitHub ou estrutura de tabela fora do padrão
- **THEN** o revisor rejeita o currículo gerado e emite feedback corretivo imediato sem gastar chamadas de LLM

#### Scenario: Revisão em modo econômico
- **WHEN** a execução estiver configurada em modo econômico (`strict_review=False`)
- **THEN** o sistema valida o currículo e gera o diagnóstico de aderência de termos utilizando apenas as regras determinísticas, sem invocar o modelo auditor

#### Scenario: Falha de API durante a auditoria
- **WHEN** a API do auditor falhar ou exceder limites
- **THEN** o revisor não aprova silenciosamente o documento e sinaliza o erro explicitamente no estado

## ADDED Requirements

### Requirement: Execução concorrente inicial no grafo
O sistema SHALL disparar a análise textual da vaga e a consulta à API de repositórios do GitHub concorrentemente a partir do nó inicial do grafo, sincronizando os resultados em um nó determinístico de ranqueamento de relevância.

#### Scenario: Disparo simultâneo de nós iniciais
- **WHEN** o grafo é iniciado com os dados da vaga e o nome de usuário do GitHub
- **THEN** as requisições de análise de requisitos e de listagem de repositórios são executadas em paralelo
