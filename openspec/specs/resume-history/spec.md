# resume-history Specification

## Purpose
Permite que o usuário acesse, visualize e gerencie todos os currículos otimizados gerados anteriormente.

## Requirements

### Requirement: Listar currículos gerados
O sistema SHALL exibir uma lista de todos os currículos salvos no histórico associados ao `user_id` do usuário conectado, ordenados da data mais recente à mais antiga, com datas exibidas no fuso horário local. Registros sem dono ou de outros usuários MUST NOT aparecer.

#### Scenario: Visualização do histórico vazio
- **WHEN** não há currículos salvos para o usuário atual no histórico
- **THEN** o sistema exibe uma mensagem indicando que o histórico está vazio

#### Scenario: Visualização do histórico com itens
- **WHEN** há currículos salvos pertencentes ao usuário logado
- **THEN** o sistema lista os currículos com seus respectivos títulos da vaga, idioma, score ATS e data formatada

#### Scenario: Arquivos locais sem dono ou de outros usuários
- **WHEN** a pasta de histórico local contém arquivos sem `user_id` ou com o `user_id` de outro usuário
- **THEN** esses arquivos não aparecem na lista, no painel nem na barra lateral do usuário conectado

#### Scenario: Data exibida no fuso local
- **WHEN** uma candidatura criada às 08:03 no horário local é lida da nuvem, onde está gravada em UTC
- **THEN** a data exibida é 08:03, igual à de uma candidatura local criada no mesmo instante

### Requirement: Carregar currículo salvo
O sistema SHALL carregar e exibir o conteúdo Markdown de um currículo ao ser selecionado no histórico.

#### Scenario: Seleção de currículo
- **WHEN** o usuário clica em um currículo específico na aba de histórico
- **THEN** o conteúdo completo do currículo é exibido na tela principal para cópia e leitura

### Requirement: Armazenamento e recuperação de Cover Letter
O sistema SHALL persistir a Cover Letter gerada junto com o currículo no registro histórico e permitir a recuperação individual de ambos os documentos.

#### Scenario: Carregamento de aplicação com Cover Letter
- **WHEN** o usuário seleciona uma candidatura gravada no histórico
- **THEN** o sistema carrega tanto o currículo ajustado quanto a respectiva carta de apresentação

### Requirement: Suporte a persistência em nuvem com fallback
O sistema SHALL persistir as candidaturas e metadados no Supabase, vinculados ao `user_id` do usuário autenticado, quando as credenciais estiverem configuradas, mantendo fallback transparente para armazenamento local em caso de ausência de configuração. Falhas de gravação na nuvem MUST ser comunicadas ao usuário.

#### Scenario: Persistência com credenciais de nuvem
- **WHEN** as variáveis de ambiente do Supabase estão configuradas
- **THEN** as candidaturas e metadados são salvos vinculados ao `user_id` do usuário e carregados a partir do banco de dados na nuvem

#### Scenario: Fallback automático local
- **WHEN** as credenciais do Supabase não estão definidas
- **THEN** o sistema salva e lê o histórico a partir do sistema de arquivos local sem gerar exceções

#### Scenario: Falha de gravação na nuvem
- **WHEN** o Supabase está configurado mas a gravação de uma candidatura falha
- **THEN** a candidatura é salva localmente e o usuário vê um aviso de que ela não foi sincronizada com a nuvem

### Requirement: Persistência de metadados de diagnóstico
O sistema SHALL registrar o relatório de diagnóstico da otimização junto ao registro de cada candidatura.

#### Scenario: Consulta de diagnóstico de candidatura salva
- **WHEN** o usuário abre uma candidatura anterior salva no histórico
- **THEN** o painel exibe o diagnóstico e feedback que foram obtidos no momento da otimização

### Requirement: Edição preserva identidade da candidatura
O sistema SHALL manter a data de criação e o identificador de uma candidatura quando o usuário editar o currículo ou a carta, sem criar registros ou arquivos duplicados.

#### Scenario: Edição de candidatura
- **WHEN** o usuário edita o currículo de uma candidatura antiga e salva
- **THEN** a data de criação exibida não muda e a candidatura mantém sua posição na lista

#### Scenario: Edições repetidas de candidatura na nuvem
- **WHEN** o usuário salva três edições seguidas de uma candidatura persistida na nuvem
- **THEN** continua existindo um único registro na nuvem e uma única cópia local

### Requirement: Sincronização do histórico local com dono
O sistema SHALL enviar à nuvem, na sincronização manual, apenas as candidaturas locais pertencentes ao usuário conectado, gravando-as vinculadas ao seu `user_id`.

#### Scenario: Pasta local com candidaturas de vários usuários
- **WHEN** a pasta local contém candidaturas dos usuários A e B e o usuário A aciona a sincronização
- **THEN** apenas as candidaturas de A são enviadas, todas vinculadas ao `user_id` de A

### Requirement: Exclusão restrita ao dono
O sistema SHALL excluir apenas a candidatura explicitamente selecionada pelo usuário e pertencente a ele, e MUST NOT oferecer exclusão em massa por título de vaga.

#### Scenario: Exclusão de candidatura própria
- **WHEN** o usuário confirma a exclusão de uma candidatura sua
- **THEN** a candidatura e sua cópia local são removidas e as candidaturas de outros usuários permanecem intactas

#### Scenario: Ausência de limpeza em massa
- **WHEN** qualquer usuário acessa a tela Sistema
- **THEN** não existe ação que exclua candidaturas por título de vaga
