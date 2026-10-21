# ui-design-system Specification

## Purpose
Define a identidade visual e o design system da aplicação com base na regra de proporção 60-30-10 e paleta Clássico Tech Confiável, garantindo consistência, contraste acessível e usabilidade em todas as páginas.

## Requirements

### Requirement: 60-30-10 Color System Distribution
O sistema SHALL aplicar a paleta Clássico Tech Confiável distribuindo as cores na proporção visual aproximada de 60% fundo neutro (#F8FAFC e superfícies secundárias #F1F5F9), 30% estrutura e identidade (#0F172A para textos/títulos e #CBD5E1 para divisórias) e 10% destaques (#10B981 para ações primárias/sucesso e #0EA5E9 para links e acentos complementares).

#### Scenario: Visualização de páginas no padrão neutro e estruturado
- **WHEN** o usuário acessa qualquer tela da aplicação (Dashboard, Otimizador, Candidaturas, Perfil, Sistema, Login)
- **THEN** o fundo principal da página é branco gelo (#F8FAFC), as seções de leitura utilizam superfícies cinza claro (#F1F5F9), a tipografia principal adota azul noturno (#0F172A) e as bordas usam cinza azulado (#CBD5E1).

### Requirement: Primary and Secondary Action Hierarchy
O sistema SHALL diferenciar claramente os botões de ação primária (destaques e conversão) das ações secundárias ou utilitárias, utilizando a cor verde-menta (#10B981) com texto de alto contraste exclusivamente para ações de avanço ou conclusão.

#### Scenario: Interação com botões primários
- **WHEN** o usuário visualiza ações principais como "Iniciar Otimização", "Entrar", "Salvar Perfil" ou "Nova Otimização"
- **THEN** os botões apresentam estilo primário com preenchimento verde-menta (#10B981), cantos consistentes e feedback visual ao passar o cursor ou focar.

#### Scenario: Interação com botões secundários
- **WHEN** o usuário visualiza ações utilitárias como filtros, cópia de texto ou navegação secundária
- **THEN** os botões exibem estilo neutro secundário/terciário, sem concorrer visualmente com o botão de destaque da tela.

### Requirement: Card and Surface Visual Consistency
O sistema SHALL padronizar todos os cards, contêineres e blocos de conteúdo com superfícies discretas, cantos arredondados consistentes (baseRadius), bordas sutis e espaçamentos uniformes.

#### Scenario: Exibição de cards de métricas e formulários
- **WHEN** métricas do dashboard, diagnósticos ATS ou etapas do assistente são renderizados
- **THEN** cada bloco é envolvido por contêiner com borda sutil cinza (#CBD5E1), fundo diferenciado (#F1F5F9), cantos consistentes e respiro visual que evita poluição visual.

### Requirement: Accessibility and Contrast Standard
O sistema SHALL assegurar que todos os textos, ícones, estados de foco e indicadores visuais possuam contraste adequado conforme diretrizes WCAG AA, garantindo navegação acessível sem depender exclusivamente da cor para transmitir estado.

#### Scenario: Leitura de alertas e feedback de status
- **WHEN** uma mensagem de sucesso, alerta, erro ou badge de diagnóstico é exibida
- **THEN** a mensagem combina cor temática com ícone identificador e texto descritivo claro legível sobre o fundo claro da aplicação.
