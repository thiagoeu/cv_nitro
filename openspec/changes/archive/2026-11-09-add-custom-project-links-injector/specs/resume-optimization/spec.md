# Spec Delta

## ADDED Requirements

### Requirement: Incremento sob demanda de projetos em destaque via link do GitHub
O sistema SHALL permitir que o usuário adicione incrementalmente novos projetos à seção de projetos do currículo gerado fornecendo links de repositórios do GitHub, buscando os dados do repositório e redigindo cada entrada via IA no idioma e padrão canônico do documento sem sobrescrever os projetos existentes.

#### Scenario: Adição incremental de projeto por link do GitHub
- **WHEN** o usuário informa um link válido de repositório do GitHub na seção de incremento de projetos do currículo e aciona a adição
- **THEN** o sistema coleta os metadados e o README do repositório, gera a descrição formatada no idioma e padrão do documento (título H3, stack em itálico, bullets em 1ª pessoa e link do repositório) e anexa o projeto ao final da seção de projetos mantendo os anteriores intactos

#### Scenario: Adição sucessiva de múltiplos projetos e prevenção de duplicidade
- **WHEN** o usuário envia um novo link de repositório posteriormente ou informa um link já presente na seção de projetos
- **THEN** o sistema preserva todos os projetos existentes, adiciona apenas os novos projetos (ou atualiza o projeto de mesma URL sem duplicá-lo) e recompila a folha A4 automaticamente

#### Scenario: Tratamento de link inválido ou repositório inacessível
- **WHEN** o usuário informa uma URL que não pertence a um repositório válido do GitHub ou a consulta à API falha
- **THEN** o sistema exibe uma mensagem de erro clara ao usuário e preserva o currículo atual sem alterações

