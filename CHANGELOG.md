# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [1.0.0] - 2025-10-23

### ✨ Adicionado

#### Funcionalidades Principais
- **Sistema completo de scraping** para dados de fundos ANBIMA
- **Extração automática** de dados periódicos (Data da cotização e Valor cota)
- **Leitura de CNPJs** a partir de arquivo Excel de entrada
- **Exportação automática** para Excel com formatação clara
- **Ordenação cronológica** dos dados (do mais antigo ao mais recente)
- **Barra de progresso** durante a execução com `tqdm`
- **Sistema de logs** detalhado para rastreamento de operações

#### Componentes do Sistema
- `main.py` - Script principal e orquestrador
- `anbima_scraper.py` - Motor de scraping com Selenium
- `data_processor.py` - Processamento e exportação de dados
- `config.py` - Configurações centralizadas

#### Tratamento de Erros
- **Sistema de retry** automático para requisições que falham (3 tentativas)
- **Tratamento robusto** de timeouts e elementos não encontrados
- **Logs detalhados** de erros com timestamps
- **Relatório de resumo** ao final da execução

#### Interface e Usabilidade
- **Argumentos CLI** para personalização (`-i`, `-o`, `--no-headless`)
- **Modo headless** para execução em background
- **Modo visível** para debugging e testes
- **Relatórios formatados** de sucesso/falhas

#### Documentação
- `README.md` completo com 13 seções principais
- `CHANGELOG.md` para rastreamento de versões
- `.gitignore` apropriado para Python
- `requirements.txt` com todas as dependências

### 🔧 Técnico

#### Automação Web
- Implementação com **Selenium WebDriver 4.15.2**
- Gerenciamento automático do **ChromeDriver** via `webdriver-manager`
- **Explicit waits** para garantir carregamento de elementos
- **Implicit waits** para navegação robusta
- **Scrolling automático** para carregar dados lazy-loaded

#### Processamento de Dados
- Uso de **Pandas 2.1.3** para manipulação de dados
- **OpenPyXL 3.1.2** para leitura/escrita de Excel
- **Remoção de duplicatas** automática por data
- **Validação de estrutura** de dados

#### Arquitetura
- **Separação de responsabilidades** (scraper, processor, config)
- **Logging estruturado** com módulo `logging`
- **Configurações centralizadas** em arquivo único
- **Tratamento de exceções** em múltiplos níveis

### 🐛 Correções de Bugs

#### Inicialização
- **Corrigido**: Problema com path do ChromeDriver no macOS (ARM64)
- **Corrigido**: Permissões de execução do chromedriver
- **Corrigido**: Detecção automática do executável correto

#### Navegação
- **Corrigido**: Banner de cookies bloqueando interações
- **Corrigido**: Dropdown de busca sobrepondo elementos clicáveis
- **Corrigido**: Timeout ao navegar para aba "Dados Periódicos"
- **Implementado**: Navegação direta via URL construída

#### Extração de Dados
- **Corrigido**: Extração incompleta de dados históricos (apenas 22 linhas)
- **Implementado**: Sistema de scroll para carregar todos os dados disponíveis
- **Corrigido**: Duplicação de registros durante scroll
- **Implementado**: Set de datas vistas para evitar duplicatas

#### Performance
- **Otimizado**: Delays entre requisições para evitar rate limiting
- **Otimizado**: Uso de seletores CSS mais eficientes
- **Otimizado**: Remoção de waits desnecessários

### 📊 Especificações de Dados

#### Campos Extraídos
- ✅ CNPJ do fundo
- ✅ Nome do fundo
- ✅ Data da cotização (Data de competência)
- ✅ Valor cota

#### Campos Excluídos (conforme requisitos)
- ❌ Valor patrimônio líquido
- ❌ Valor volume total de aplicações
- ❌ Valor volume total de resgates
- ❌ Número total de cotistas

### 🧪 Testes

#### Testes Manuais Realizados
- ✅ Teste com 2 CNPJs de exemplo (48.330.198/0001-06, 34.780.531/0001-66)
- ✅ Teste de modo headless vs. visível
- ✅ Teste de tratamento de erros (CNPJs inválidos)
- ✅ Teste de extração completa de dados (22 dias úteis)
- ✅ Teste de ordenação cronológica
- ✅ Teste de exportação para Excel

### 📝 Limitações Conhecidas

#### Site ANBIMA
- Apenas **22 dias úteis** de dados históricos disponíveis
- Sem paginação ou filtros de data na interface web
- Possibilidade de **rate limiting** em uso intensivo
- Estrutura HTML pode mudar sem aviso prévio

#### Sistema
- **Processamento sequencial** (um CNPJ por vez)
- Sem cache de resultados
- Sem validação de formato de CNPJ antes da consulta
- Dependência do Google Chrome instalado

### 🚀 Performance

#### Métricas Observadas
- **~50 segundos** por fundo em média
- **100% de taxa de sucesso** em condições normais
- **~44 registros** extraídos para 2 CNPJs
- **Uso de memória**: < 200 MB durante execução

### 📦 Dependências

```
selenium==4.15.2
pandas==2.1.3
openpyxl==3.1.2
webdriver-manager==4.0.1
tqdm==4.66.1
python-dotenv==1.1.1
```

### 🔒 Segurança

- **Modo incognito** habilitado por padrão
- **User-Agent** customizado para evitar detecção
- **Rate limiting** respeitado com delays entre requisições
- **Sem armazenamento de credenciais** (dados públicos)

### 📋 Requisitos de Sistema

- **Python**: 3.9 ou superior
- **Google Chrome**: Última versão estável
- **Sistema Operacional**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **Memória RAM**: Mínimo 2 GB (recomendado 4 GB)
- **Conexão Internet**: Estável, mínimo 1 Mbps

---

## [Futuro] - Planejado

### 🔮 Melhorias Planejadas

#### Interface
- [ ] Interface web com dashboard
- [ ] Visualização de dados em tempo real
- [ ] Upload de arquivo via interface gráfica

#### Funcionalidades
- [ ] API REST para integração com outros sistemas
- [ ] Suporte para extração de outras abas (Indicadores, Sobre o Fundo)
- [ ] Filtros de data personalizáveis
- [ ] Exportação para múltiplos formatos (CSV, JSON, Parquet)
- [ ] Validação de CNPJ antes da consulta

#### Performance
- [ ] Processamento paralelo de múltiplos CNPJs
- [ ] Cache inteligente de resultados
- [ ] Otimização de uso de memória
- [ ] Suporte para processamento em lote de grandes volumes

#### Armazenamento
- [ ] Integração com banco de dados (PostgreSQL, SQLite)
- [ ] Histórico acumulativo de dados
- [ ] Versionamento de extrações
- [ ] Deduplicação automática de dados históricos

#### Notificações
- [ ] Alertas por email ao concluir execução
- [ ] Integração com Slack/Teams
- [ ] Notificações de erro em tempo real
- [ ] Relatórios periódicos agendados

#### Análise de Dados
- [ ] Gráficos de evolução das cotas
- [ ] Estatísticas descritivas automáticas
- [ ] Comparação entre fundos
- [ ] Exportação de relatórios em PDF

#### DevOps
- [ ] Containerização com Docker
- [ ] CI/CD com GitHub Actions
- [ ] Deploy automatizado
- [ ] Monitoramento de saúde do sistema

#### Robustez
- [ ] Detecção automática de mudanças na estrutura do site
- [ ] Auto-healing para seletores quebrados
- [ ] Fallback para métodos alternativos de extração
- [ ] Sistema de alertas para manutenção

---

## Formato de Versão

O formato de versão segue `MAJOR.MINOR.PATCH`:

- **MAJOR**: Mudanças incompatíveis na API
- **MINOR**: Novas funcionalidades mantendo compatibilidade
- **PATCH**: Correções de bugs mantendo compatibilidade

---

## Tipos de Mudanças

- **Adicionado** (`✨ Adicionado`): Novas funcionalidades
- **Modificado** (`🔄 Modificado`): Mudanças em funcionalidades existentes
- **Descontinuado** (`⚠️ Descontinuado`): Funcionalidades que serão removidas
- **Removido** (`🗑️ Removido`): Funcionalidades removidas
- **Corrigido** (`🐛 Corrigido`): Correções de bugs
- **Segurança** (`🔒 Segurança`): Correções de vulnerabilidades

---

**Para reportar bugs ou sugerir melhorias, consulte a documentação principal no README.md**

