# Spec Delta: resume-optimization

## MODIFIED Requirements

### Requirement: Buscar evidências no GitHub
O sistema SHALL validar o nome de usuário do GitHub e consultar a API pública do GitHub utilizando timeouts estritos para buscar repositórios e READMEs relevantes.

#### Scenario: Repositório correspondente encontrado
- **WHEN** a vaga exige "Python" e o usuário possui um repositório Python válido
- **THEN** o sistema seleciona o README deste repositório como evidência

#### Scenario: Usuário com formato inválido
- **WHEN** o nome de usuário fornecido contém caracteres especiais inválidos ou tentativas de injeção
- **THEN** o sistema rejeita a chamada de rede e retorna lista vazia de repositórios de forma segura

#### Scenario: Timeout ou instabilidade na API externa
- **WHEN** a API do GitHub demorar mais que o tempo limite configurado (timeout)
- **THEN** o sistema aborta a requisição sem bloquear indefinidamente a aplicação

### Requirement: Revisar currículo gerado
O sistema SHALL revisar o currículo gerado contra alucinações e falhas estruturais, e NÃO DEVE aprovar silenciosamente caso ocorra falha de comunicação com a API do LLM.

#### Scenario: Identificação de alucinação
- **WHEN** o currículo gerado cita uma ferramenta que não está no currículo original nem no GitHub
- **THEN** o revisor rejeita o currículo e solicita correção ao gerador

#### Scenario: Falha de API durante a auditoria
- **WHEN** a API do auditor falhar ou exceder limites
- **THEN** o revisor não aprova silenciosamente o documento e sinaliza o erro explicitamente no estado

## ADDED Requirements

### Requirement: Sanitização de saída HTML do currículo
O sistema SHALL sanitizar e escapar caracteres especiais HTML (XSS prevention) em todo o conteúdo gerado antes da renderização e exportação.

#### Scenario: Conteúdo contendo tags maliciosas
- **WHEN** o currículo base ou descrição da vaga contiver tags HTML ou scripts injetados
- **THEN** o formatador escapa os caracteres perigosos impedindo a execução de scripts no navegador
