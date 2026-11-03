# Spec Delta

## ADDED Requirements

### Requirement: Preservar melhor versão e interromper revisão por estagnação
O sistema SHALL manter um snapshot da versão de currículo com a maior pontuação ATS durante o ciclo de revisão, interrompendo novas rodadas caso uma revisão não supere a melhor nota anterior e restaurando automaticamente a versão de maior pontuação.

#### Scenario: Revisão subsequente com nota inferior ou igual à anterior
- **WHEN** uma segunda rodada de avaliação do revisor resulta em pontuação ATS menor ou igual à melhor nota já registrada e sem erros estruturais determinísticos críticos
- **THEN** o sistema encerra o loop de revisão imediatamente para não forçar alucinações e restaura o currículo e o diagnóstico correspondentes à melhor versão avaliada

#### Scenario: Revisão subsequente que melhora a pontuação
- **WHEN** uma rodada de refinamento eleva a pontuação ATS acima da tentativa anterior
- **THEN** o sistema atualiza o snapshot da melhor versão com o novo currículo e diagnóstico aprimorados

### Requirement: Obter arquivos README selecionados de forma concorrente
O sistema SHALL realizar o download dos arquivos README dos repositórios selecionados no ranking de relevância de maneira paralela.

#### Scenario: Download concorrente dos Top 3 READMEs
- **WHEN** o nó de ranqueamento seleciona múltiplos repositórios relevantes do candidato
- **THEN** as requisições para obtenção dos conteúdos de README são disparadas concorrentemente respeitando o tempo limite configurado

