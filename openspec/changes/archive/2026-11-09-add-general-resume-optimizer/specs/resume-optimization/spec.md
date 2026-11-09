# Spec Delta

## ADDED Requirements

### Requirement: Otimizar currículo geral sem vaga específica por endpoint independente
O sistema SHALL disponibilizar um botão e endpoint independentes para gerar um currículo geral de alto impacto sem exigir vaga específica, mantendo o fluxo principal inalterado. O endpoint geral MUST exigir apenas o currículo base, enriquecer opcionalmente o documento com repositórios do GitHub, destacar as tecnologias comprovadas e salvar o resultado em Candidaturas com visualização A4.

#### Scenario: Geração de currículo geral apenas com currículo base
- **WHEN** o usuário informa o currículo base (deixando título e descrição da vaga em branco) e aciona o botão de otimização geral sem vaga específica
- **THEN** o sistema executa o endpoint dedicado de otimização geral (sem acionar o grafo de análise de vaga específica), gera o currículo estruturado no padrão A4 destacando as tecnologias relevantes do candidato, registra o título padrão (ou o foco profissional informado) e redireciona para a tela da candidatura gerada

#### Scenario: Geração de currículo geral enriquecida com portfólio do GitHub
- **WHEN** o usuário informa o currículo base e um nome de usuário do GitHub ao acionar o botão de otimização geral
- **THEN** o sistema consulta os repositórios públicos não-fork do usuário, seleciona os principais projetos pelo mérito técnico e estrelas, extrai seus READMEs higienizados e inclui a seção de Projetos em Destaque e as tecnologias comprovadas no currículo geral gerado

#### Scenario: Validação de currículo base ausente no modo geral
- **WHEN** o usuário aciona o botão de otimização geral sem ter preenchido ou enviado o currículo base
- **THEN** o sistema exibe erro informando que o currículo base é obrigatório e não inicia chamadas aos modelos de IA

#### Scenario: Isolamento em relação ao fluxo principal de vaga específica
- **WHEN** o usuário utiliza o botão original de otimização para vaga específica ou o novo botão de otimização geral
- **THEN** cada botão aciona seu respectivo endpoint sem interferir nos prompts, regras ou estado do outro fluxo

#### Scenario: Edição e adição de projetos escolhidos pelo usuário no currículo geral
- **WHEN** o currículo geral sem vaga específica é gerado e aberto (ou quando o usuário informa links de projetos específicos do GitHub)
- **THEN** o usuário dispõe do botão/aba de edição do currículo e da seção de adicionar projetos por link do GitHub para incluir ou editar quantos projetos desejar mantendo o padrão do documento A4
