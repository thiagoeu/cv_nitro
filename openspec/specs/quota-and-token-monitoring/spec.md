# quota-and-token-monitoring Specification

## Purpose

Monitora o consumo de tokens e requisições dos provedores de IA e os limites da API do GitHub, exibindo barras de progresso da porcentagem de cota restante e estimativa de capacidade operacional na tela de configurações do sistema.

## Requirements

### Requirement: Contabilizar consumo diário de tokens e requisições de IA
O sistema SHALL registrar a quantidade de tokens e chamadas de API realizados nos provedores de IA durante as execuções do pipeline, mantendo o acumulado do dia atual e reiniciando automaticamente na virada de data. Cada chamada MUST ser contada uma única vez, no provedor que de fato respondeu.

#### Scenario: Registro de consumo após execução de agentes
- **WHEN** um nó do grafo invoca o modelo de linguagem para análise, geração ou revisão
- **THEN** o sistema soma os tokens consumidos e incrementa o contador de requisições diárias do provedor utilizado

#### Scenario: Reinício automático na virada do dia
- **WHEN** a data atual diverge da data do último registro de consumo salvo
- **THEN** o sistema zera os contadores diários e restaura a capacidade disponível para 100%

#### Scenario: Candidatura salva após a otimização
- **WHEN** uma otimização com 4 chamadas ao modelo termina e a candidatura é salva no histórico
- **THEN** o contador de requisições do dia aumenta exatamente 4

#### Scenario: Resposta estruturada vinda do provedor de reserva
- **WHEN** o Gemini falha e o Groq responde a uma chamada de saída estruturada, como a análise da vaga
- **THEN** os tokens e a requisição são somados ao Groq, e não ao Gemini

#### Scenario: Otimizações simultâneas
- **WHEN** duas sessões do app registram consumo ao mesmo tempo
- **THEN** o acumulado do dia inclui o consumo das duas sessões

### Requirement: Exibir barras de porcentagem de cota restante na tela Sistema
O sistema SHALL apresentar barras visuais de progresso na tela de Sistema indicando a porcentagem de cota restante (de 0% a 100%), o número estimado de otimizações completas ainda suportadas no dia e alertas visuais quando a capacidade estiver baixa.

#### Scenario: Cota saudável disponível
- **WHEN** o usuário acessa a tela de Sistema e o consumo diário está abaixo de 75% do orçamento configurado
- **THEN** o sistema exibe a barra de progresso com a porcentagem restante (ex.: 90% disponível) e a estimativa de quantas novas otimizações podem ser executadas com segurança

#### Scenario: Alerta de cota crítica para próximas execuções
- **WHEN** a porcentagem de cota restante do provedor principal cai para 15% ou menos
- **THEN** o sistema exibe um aviso preventivo indicando risco de limite de taxa nas próximas execuções e informando se o provedor de reserva (Groq) está ativo

### Requirement: Consultar cota restante da API do GitHub
O sistema SHALL permitir consultar e visualizar em barra de progresso a porcentagem de requisições restantes na janela horária da API do GitHub.

#### Scenario: Exibição do limite horário do GitHub
- **WHEN** a consulta de status da API do GitHub retorna os contadores de limite e requisições restantes
- **THEN** a tela de Sistema exibe a barra de porcentagem disponível e a relação de chamadas restantes sobre o limite total da hora
