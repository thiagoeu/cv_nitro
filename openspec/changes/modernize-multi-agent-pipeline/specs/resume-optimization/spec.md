# Spec Delta

## MODIFIED Requirements

### Requirement: Buscar evidências no GitHub
O sistema SHALL listar repositórios públicos concorrentemente com a análise de vaga e permitir a obtenção detalhada de arquivos README sob demanda através de chamada de ferramenta (*tool-calling*) pelo gerador.

#### Scenario: Repositório correspondente encontrado
- **WHEN** a vaga exige "Python" e o usuário possui um repositório Python
- **THEN** o sistema classifica o repositório por pontuação de relevância e disponibiliza o extrato técnico sob demanda

### Requirement: Revisar currículo gerado
O sistema SHALL revisar o currículo gerado contra alucinações e conformidade de layout, classificando falhas leves para refinamento cirúrgico de seção (*delta patching*) ou falhas graves para reescrita completa.

#### Scenario: Identificação de alucinação ou ajuste de seção
- **WHEN** o currículo gerado apresenta erro pontual de formatação ou de alinhamento em uma seção específica
- **THEN** o sistema aciona o refinamento cirúrgico da seção afetada sem reescrever o restante do documento

## ADDED Requirements

### Requirement: Execução concorrente inicial no grafo
O sistema SHALL disparar a análise textual da vaga e a consulta à API de repositórios do GitHub concorrentemente a partir do nó inicial do grafo, sincronizando os resultados em um nó determinístico de ranqueamento de relevância.

#### Scenario: Disparo simultâneo de nós iniciais
- **WHEN** o grafo é iniciado com os dados da vaga e o nome de usuário do GitHub
- **THEN** as requisições de análise de requisitos e de listagem de repositórios são executadas em paralelo
