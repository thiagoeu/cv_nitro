# Spec Delta: ui-design-system

## ADDED Requirements

### Requirement: Global Application Footer
O sistema SHALL renderizar um rodapé institucional global padronizado em todas as visualizações da aplicação, apresentando créditos do desenvolvedor Thiago Araújo, link para GitHub (@thiagoeu), e-mail de contato (araujo.thiago1051@gmail.com), termos de licença MIT e menção à disciplina de Sistemas Multi-Agentes (SMA).

#### Scenario: Visualização do rodapé em páginas públicas e privadas
- **WHEN** qualquer página (pública ou privada) for renderizada na interface do sistema
- **THEN** o sistema exibe o rodapé com borda superior sutil (#CBD5E1), texto informativo legível (#475569), links em ciano (#0EA5E9) e informações de autoria e licença

### Requirement: Streamlined Landing Page Bottom Flow
O sistema SHALL estruturar a finalização da Landing Page de forma limpa e harmônica com a paleta 60-30-10, eliminando caixas com contraste dissonante e botões de Call-to-Action redundantes no final da página, integrando a seção de funcionamento diretamente ao rodapé global.

#### Scenario: Visualização da parte inferior da Landing Page
- **WHEN** um usuário visitante rolar até a base da Landing Page pública
- **THEN** a página encerra de forma limpa após o fluxo de etapas, sem blocos escuros com texto de baixa legibilidade e sem botões duplicados de autenticação
