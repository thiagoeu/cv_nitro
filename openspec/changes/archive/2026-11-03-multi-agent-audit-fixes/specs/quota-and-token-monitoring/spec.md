# Spec Delta

## MODIFIED Requirements

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
