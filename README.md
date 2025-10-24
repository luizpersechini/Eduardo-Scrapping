# 📊 ANBIMA Data Scraper - Documentação Completa

Sistema automatizado para extração de dados periódicos de fundos de investimento do site da ANBIMA.

---

## 📑 Índice

1. [Visão Geral](#-visão-geral)
2. [Requisitos do Sistema](#-requisitos-do-sistema)
3. [Instalação](#-instalação)
4. [Configuração](#-configuração)
5. [Guia de Uso](#-guia-de-uso)
6. [Arquitetura do Sistema](#-arquitetura-do-sistema)
7. [Especificações Técnicas](#-especificações-técnicas)
8. [Dados Extraídos](#-dados-extraídos)
9. [Tratamento de Erros](#-tratamento-de-erros)
10. [Solução de Problemas](#-solução-de-problemas)
11. [Perguntas Frequentes](#-perguntas-frequentes)
12. [Limitações Conhecidas](#-limitações-conhecidas)
13. [Manutenção e Atualizações](#-manutenção-e-atualizações)

---

## 🎯 Visão Geral

### Descrição do Projeto

O **ANBIMA Data Scraper** é uma solução automatizada desenvolvida em Python para extração de dados históricos de fundos de investimento disponíveis publicamente no portal [ANBIMA Data](https://data.anbima.com.br/busca/fundos).

### Objetivo

Automatizar o processo de coleta de dados periódicos (Data da cotização e Valor da cota) de múltiplos fundos de investimento, eliminando a necessidade de consultas manuais e facilitando a análise histórica de dados.

### Principais Características

- ✅ **Automação Completa**: Processo end-to-end desde a leitura de CNPJs até a geração do arquivo Excel
- ✅ **Extração Seletiva**: Coleta apenas os campos específicos solicitados (Data e Valor da cota)
- ✅ **Organização Cronológica**: Dados ordenados automaticamente do mais antigo ao mais recente
- ✅ **Robustez**: Sistema de retry automático para requisições que falham
- ✅ **Rastreabilidade**: Logs detalhados de todas as operações
- ✅ **Interface Amigável**: Barra de progresso e relatórios de execução
- ✅ **Configurável**: Parâmetros ajustáveis para diferentes cenários de uso
- ⚡ **NOVO: Modo Paralelo**: Processa múltiplos CNPJs simultaneamente (até 75% mais rápido!)

### Fluxo de Trabalho

```
┌─────────────────┐
│  input_cnpjs    │
│   .xlsx         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  main.py        │
│  (Orquestrador) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│ anbima_scraper  │────▶│  Site ANBIMA     │
│   .py           │     │  (Selenium)      │
└────────┬────────┘     └──────────────────┘
         │
         ▼
┌─────────────────┐
│ data_processor  │
│   .py           │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│  output_*.xlsx  │     │  logs/*.log      │
└─────────────────┘     └──────────────────┘
```

---

## 💻 Requisitos do Sistema

### Hardware Mínimo

- **Processador**: 1 GHz ou superior
- **Memória RAM**: 2 GB (recomendado: 4 GB ou mais)
- **Espaço em Disco**: 500 MB livres
- **Conexão à Internet**: Estável, velocidade mínima de 1 Mbps

### Software Necessário

| Software | Versão Mínima | Versão Recomendada | Observações |
|----------|---------------|-------------------|-------------|
| Python | 3.9 | 3.10 ou superior | Obrigatório |
| Google Chrome | Última versão estável | Última versão | Obrigatório |
| Sistema Operacional | Windows 10 / macOS 10.14 / Ubuntu 18.04 | Versões mais recentes | - |

### Dependências Python

Todas as dependências são instaladas automaticamente via `requirements.txt`:

```
selenium==4.15.2        # Automação do navegador
pandas==2.1.3           # Manipulação de dados tabulares
openpyxl==3.1.2         # Leitura/escrita de arquivos Excel
webdriver-manager==4.0.1 # Gerenciamento automático do ChromeDriver
tqdm==4.66.1            # Barra de progresso
```

---

## 🔧 Instalação

### Instalação Rápida

1. **Clone ou faça download do projeto**

2. **Navegue até o diretório do projeto**
```bash
cd "/Users/LuizPersechini_1/Projects/Eduardo Scrapping"
```

3. **Instale as dependências**
```bash
pip3 install -r requirements.txt
```

### Instalação Detalhada

#### Passo 1: Verificar Python

```bash
python3 --version
```

Se não tiver Python instalado, baixe em [python.org](https://www.python.org/downloads/)

#### Passo 2: Verificar Google Chrome

O Google Chrome deve estar instalado no sistema. Baixe em [google.com/chrome](https://www.google.com/chrome/)

#### Passo 3: Criar Ambiente Virtual (Opcional mas Recomendado)

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# ou
venv\Scripts\activate  # Windows
```

#### Passo 4: Instalar Dependências

```bash
pip3 install -r requirements.txt
```

#### Passo 5: Verificar Instalação

```bash
python3 -c "import selenium, pandas, openpyxl; print('✓ Instalação bem-sucedida!')"
```

---

## ⚙️ Configuração

### Arquivo de Configuração (`config.py`)

O arquivo `config.py` contém todas as configurações do sistema:

#### URLs e Endpoints

```python
ANBIMA_BASE_URL = "https://data.anbima.com.br/busca/fundos"
```

#### Timeouts (em segundos)

```python
PAGE_LOAD_TIMEOUT = 30      # Tempo máximo para carregar página
ELEMENT_WAIT_TIMEOUT = 20   # Tempo máximo para encontrar elementos
IMPLICIT_WAIT = 10          # Espera implícita entre ações
SLEEP_BETWEEN_REQUESTS = 2  # Delay entre requisições
```

**Quando ajustar:**
- **Conexão lenta**: Aumente todos os timeouts em 50%
- **Conexão rápida**: Pode reduzir para acelerar o processo
- **Site sobrecarregado**: Aumente `SLEEP_BETWEEN_REQUESTS`

#### Sistema de Retry

```python
MAX_RETRIES = 3     # Número de tentativas em caso de falha
RETRY_DELAY = 5     # Segundos entre tentativas
```

#### Opções do Chrome

```python
CHROME_OPTIONS = [
    "--headless",                          # Execução em background
    "--no-sandbox",                        # Segurança
    "--disable-dev-shm-usage",            # Uso de memória
    "--disable-gpu",                       # GPU
    "--window-size=1920,1080",            # Resolução
    "--disable-blink-features=AutomationControlled",  # Anti-detecção
    "user-agent=Mozilla/5.0..."           # User agent
]
```

#### Estrutura de Dados

```python
OUTPUT_COLUMNS = [
    "CNPJ",
    "Nome do Fundo",
    "Data da cotização",
    "Valor cota",
    "Status"
]

INPUT_COLUMN_CNPJ = "CNPJ"
```

### Arquivo de Entrada (`input_cnpjs.xlsx`)

#### Formato Esperado

| CNPJ |
|------|
| 48.330.198/0001-06 |
| 34.780.531/0001-66 |
| ... |

#### Requisitos

- **Nome da coluna**: Exatamente "CNPJ" (case-sensitive)
- **Formato do CNPJ**: Com ou sem formatação (pontos, barras)
- **Extensão**: `.xlsx` (Excel 2007 ou superior)
- **Localização**: Raiz do projeto (ou especifique com `-i`)

#### Exemplo de Criação Manual

```python
import pandas as pd

cnpjs = ["48.330.198/0001-06", "34.780.531/0001-66"]
df = pd.DataFrame({"CNPJ": cnpjs})
df.to_excel("input_cnpjs.xlsx", index=False)
```

---

## 📖 Guia de Uso

### Uso Básico

#### 1. Modo Padrão (Headless)

```bash
python3 main.py
```

**Características:**
- Navegador invisível (background)
- Mais rápido
- Ideal para produção

#### 2. Modo Visível (Debug)

```bash
python3 main.py --no-headless
```

**Características:**
- Navegador visível
- Permite observar o processo
- Ideal para debug e testes

#### 3. Personalizar Arquivos

```bash
python3 main.py -i meus_fundos.xlsx -o resultados_outubro.xlsx
```

### ⚡ Modo Paralelo (NOVO!)

O modo paralelo permite processar múltiplos CNPJs simultaneamente, reduzindo o tempo total em até **75%**!

#### 1. Modo Paralelo Padrão (4 workers)

```bash
python3 main_parallel.py
```

**Características:**
- Processa 4 CNPJs simultaneamente
- ~75% mais rápido que o modo sequencial
- Ideal para listas grandes de CNPJs

#### 2. Modo Paralelo Personalizado

```bash
python3 main_parallel.py -i input_cnpjs.xlsx -o output.xlsx --workers 6
```

**Opções disponíveis:**
- `-w, --workers N`: Número de workers (padrão: 4, máximo recomendado: 8)
- `--skip-processed`: Pula CNPJs já processados no arquivo de saída

#### 3. Modo Paralelo com Skip

```bash
python3 main_parallel.py --skip-processed
```

**Útil para:**
- Continuar uma execução interrompida
- Adicionar novos CNPJs sem reprocessar os antigos
- Economizar tempo em re-execuções

#### Comparação de Performance

| Cenário | Modo Sequencial | Modo Paralelo (4 workers) | Modo Paralelo (5 workers) | Melhor Ganho |
|---------|----------------|---------------------------|---------------------------|--------------|
| 10 CNPJs | ~11 minutos | ~3 minutos | ~2 minutos | **82%** |
| 50 CNPJs | ~57 minutos | ~15 minutos | ~8 minutos | **86%** |
| 161 CNPJs | ~3h 25min | ~37 minutos | **27 minutos** ⭐ | **87%** |

**Tempo médio por CNPJ:**
- Sequencial: ~68 segundos
- Paralelo (4 workers): ~17 segundos por conjunto
- Paralelo (5 workers): **~10 segundos por conjunto** 🚀

**Resultados Reais (161 CNPJs)**:
- 5 workers: 27.23 minutos
- Taxa de sucesso: 95.7%
- Throughput: 354.71 CNPJs/hora

#### Quando Usar Cada Modo

| Situação | Modo Recomendado |
|----------|------------------|
| Primeira execução com muitos CNPJs (100+) | **Paralelo 5 workers** ⭐ |
| Listas médias (50-100 CNPJs) | Paralelo 4 workers |
| Listas pequenas (20-50 CNPJs) | Paralelo 2 workers |
| Debug ou desenvolvimento | Sequencial (--no-headless) |
| Poucos CNPJs (< 20) | Sequencial |
| Re-execução mensal (lista completa) | **Paralelo 5 workers** (--skip-processed) |
| Sistema com recursos limitados | Paralelo 2 workers |
| Teste de funcionalidade | Sequencial |

### Uso Avançado

#### Executar com Parâmetros Customizados

```bash
python3 main.py \
  --input fundos_renda_fixa.xlsx \
  --output relatorio_$(date +%Y%m%d).xlsx \
  --no-headless
```

#### Executar em Background (Linux/macOS)

```bash
nohup python3 main.py > execucao.log 2>&1 &
```

#### Agendar Execução (Cron - Linux/macOS)

```bash
# Editar crontab
crontab -e

# Executar todo dia às 18h
0 18 * * * cd /caminho/projeto && python3 main.py
```

#### Agendar Execução (Task Scheduler - Windows)

1. Abrir "Agendador de Tarefas"
2. Criar Tarefa Básica
3. Apontar para `python.exe` com argumentos: `main.py`
4. Definir diretório de trabalho: caminho do projeto

### Interpretando a Saída

#### Durante a Execução

```
✓ Found 2 CNPJ(s) to process
✓ Web scraper initialized successfully

🔍 Scraping data for 2 fund(s)...

Progress:  50%|█████     | 1/2 [00:57<00:57, 57.19s/fund]
```

#### Ao Final

```
================================================================================
SCRAPING SUMMARY
================================================================================
Total CNPJs processed: 2
Successful: 2 (100.0%)
Failed: 0

✓ Results saved to: output_anbima_data_20251023_110341.xlsx
✓ Log file saved to: logs/
================================================================================
```

### Arquivo de Saída

#### Estrutura

```
output_anbima_data_YYYYMMDD_HHMMSS.xlsx
```

#### Conteúdo

| CNPJ | Nome do Fundo | Data da cotização | Valor cota | Status |
|------|---------------|-------------------|------------|--------|
| 48.330.198/0001-06 | CLASSE ÚNICA... | 19/09/2025 | R$ 1,569379 | Success |
| 48.330.198/0001-06 | CLASSE ÚNICA... | 22/09/2025 | R$ 1,570331 | Success |

---

## 🏗️ Arquitetura do Sistema

### Componentes Principais

#### 1. `main.py` - Orquestrador

**Responsabilidades:**
- Inicialização do sistema
- Leitura de parâmetros CLI
- Coordenação entre módulos
- Tratamento de exceções globais
- Geração de relatórios

**Funções Principais:**
- `setup_logging()`: Configura sistema de logs
- `main()`: Função principal de execução

#### 2. `anbima_scraper.py` - Motor de Scraping

**Responsabilidades:**
- Automação do navegador via Selenium
- Navegação no site da ANBIMA
- Extração de dados das páginas
- Tratamento de erros de navegação

**Classe Principal: `ANBIMAScraper`**

```python
class ANBIMAScraper:
    def setup_driver(self) -> bool
    def search_fund(self, cnpj: str) -> Tuple[bool, str]
    def get_fund_name(self) -> Optional[str]
    def navigate_to_periodic_data(self) -> Tuple[bool, str]
    def extract_periodic_data(self) -> Tuple[bool, List[Dict], str]
    def scrape_fund_data(self, cnpj: str) -> Dict
    def close(self)
```

#### 3. `data_processor.py` - Processador de Dados

**Responsabilidades:**
- Leitura do arquivo Excel de entrada
- Transformação e limpeza de dados
- Exportação para Excel
- Geração de relatórios de resumo

**Classe Principal: `DataProcessor`**

```python
class DataProcessor:
    def read_cnpj_list(self, input_file: str) -> List[str]
    def process_scraped_data(self, results: List[Dict]) -> pd.DataFrame
    def save_results(self, df: pd.DataFrame, output_file: str)
    def create_summary_report(self, results: List[Dict]) -> Dict
```

#### 4. `config.py` - Configurações

**Conteúdo:**
- URLs e endpoints
- Timeouts e delays
- Seletores CSS/XPath
- Estrutura de dados
- Configurações do Chrome

### Fluxo de Dados

```
1. main.py lê input_cnpjs.xlsx
2. Para cada CNPJ:
   a. ANBIMAScraper.search_fund()
   b. ANBIMAScraper.get_fund_name()
   c. ANBIMAScraper.navigate_to_periodic_data()
   d. ANBIMAScraper.extract_periodic_data()
3. DataProcessor.process_scraped_data()
4. DataProcessor.save_results()
5. Gera logs e relatórios
```

---

## 🔬 Especificações Técnicas

### Algoritmo de Scraping

#### Etapa 1: Busca do Fundo

```python
1. Acessa https://data.anbima.com.br/busca/fundos
2. Aguarda carregamento completo (sleep 3s)
3. Fecha banner de cookies se presente
4. Localiza campo de busca por seletor CSS
5. Digita CNPJ
6. Aguarda dropdown de resultados (sleep 3s)
7. Clica no link "em fundos de investimento"
8. Aguarda página de resultados (sleep 2s)
9. Fecha dropdown se ainda aberto
10. Localiza e clica no primeiro resultado
```

#### Etapa 2: Extração de Dados

```python
1. Obtém nome do fundo da página de detalhes
2. Constrói URL de dados periódicos
3. Navega para /fundos/{CODE}/dados-periodicos
4. Aguarda carregamento da tabela (sleep 3s)
5. Identifica índices das colunas:
   - Data competência (índice 0)
   - Valor cota (índice 2)
6. Executa scroll para garantir todos os dados carregados
7. Extrai dados linha por linha
8. Remove duplicatas por data
9. Inverte ordem (mais antigo primeiro)
10. Retorna lista de dicionários
```

### Seletores Utilizados

#### CSS Selectors

```python
"input[placeholder*='Busque fundos']"  # Campo de busca
"article a[href*='/fundos/C']"         # Link do fundo
"table"                                 # Tabela de dados
"th, td"                                # Células de cabeçalho
```

#### XPath Selectors

```python
"//a[contains(@href, '/busca/fundos?q=')]"  # Link dropdown
"//button[contains(text(), 'Prosseguir')]"  # Aceitar cookies
```

### Estratégia de Waits

O sistema utiliza 3 tipos de waits:

1. **Explicit Wait** (WebDriverWait)
   ```python
   wait = WebDriverWait(driver, 20)
   element = wait.until(EC.presence_of_element_located((By.CSS, selector)))
   ```

2. **Implicit Wait**
   ```python
   driver.implicitly_wait(10)
   ```

3. **Sleep** (para carregamentos AJAX)
   ```python
   time.sleep(2)  # Aguarda AJAX completar
   ```

### Sistema de Retry

```python
max_retries = 3
for attempt in range(max_retries):
    try:
        result = scrape_fund_data(cnpj)
        if result['Status'] == 'Success':
            break
    except Exception:
        if attempt < max_retries - 1:
            time.sleep(RETRY_DELAY)
        else:
            result = {'Status': 'Error after max retries'}
```

---

## 📊 Dados Extraídos

### Campos Coletados

De acordo com as especificações do projeto, são extraídos **apenas** 2 campos:

| Campo | Tipo | Descrição | Exemplo |
|-------|------|-----------|---------|
| Data da cotização | String | Data de competência do valor da cota | 19/09/2025 |
| Valor cota | String | Valor da cota na data | R$ 1,569379 |

### Campos Excluídos

Os seguintes campos são **intencionalmente excluídos** da extração:

- ❌ Valor patrimônio líquido
- ❌ Valor volume total de aplicações
- ❌ Valor volume total de resgates
- ❌ Número total de cotistas

### Metadados Adicionados

O sistema adiciona os seguintes metadados:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| CNPJ | String | CNPJ do fundo consultado |
| Nome do Fundo | String | Nome completo do fundo |
| Status | String | Status da extração (Success/Error) |

### Organização dos Dados

- **Ordenação**: Cronológica ascendente (mais antigo → mais recente)
- **Agrupamento**: Por CNPJ
- **Formato de Saída**: Excel (.xlsx)

### Limitações de Dados

**Importante**: O site da ANBIMA exibe apenas os **últimos 22 dias úteis** de dados periódicos. Não há controles de paginação ou filtros de data disponíveis na interface web.

**Solução para histórico maior:**
- Executar o scraper periodicamente (diário, semanal ou mensal)
- Armazenar resultados em banco de dados
- Consolidar dados ao longo do tempo

---

## 🛡️ Tratamento de Erros

### Tipos de Erros

#### 1. Erros de Inicialização

**ChromeDriver não encontrado**
```
Erro: Failed to initialize WebDriver
Causa: Chrome não instalado ou ChromeDriver incompatível
Solução: Instalar Google Chrome / Limpar cache do webdriver-manager
```

**Arquivo de entrada não encontrado**
```
Erro: Input file not found
Causa: Arquivo input_cnpjs.xlsx não existe
Solução: Criar arquivo ou especificar caminho correto com -i
```

#### 2. Erros de Scraping

**Timeout de página**
```
Erro: Timeout: Page took too long to load
Causa: Conexão lenta ou site indisponível
Solução: Aumentar timeouts em config.py / Verificar conexão
```

**CNPJ não encontrado**
```
Erro: No fund found for this CNPJ
Causa: CNPJ não existe na base ANBIMA ou digitado incorretamente
Solução: Verificar CNPJ no site manualmente
```

**Elementos não localizados**
```
Erro: Could not find required columns in table
Causa: Estrutura da página mudou
Solução: Verificar seletores em config.py / Atualizar código
```

#### 3. Erros de Rede

**Bloqueio do site (HTTP 423)**
```
Erro: Server responded with status 423
Causa: Site bloqueou requisições (rate limiting)
Solução: Aumentar SLEEP_BETWEEN_REQUESTS / Executar em outro horário
```

**Sem conexão**
```
Erro: Connection refused
Causa: Sem internet ou site fora do ar
Solução: Verificar conexão / Aguardar site voltar
```

### Sistema de Logs

#### Níveis de Log

```python
logging.INFO    # Operações normais
logging.WARNING # Avisos (não impedem execução)
logging.ERROR   # Erros (podem impedir extração de um CNPJ)
```

#### Formato dos Logs

```
2025-10-23 11:03:41,543 - INFO - ANBIMA Fund Data Scraper Started
2025-10-23 11:03:41,611 - INFO - Found 2 CNPJs to process
2025-10-23 11:04:32,934 - INFO - ✓ Successfully scraped data for 48.330.198/0001-06
2025-10-23 11:05:22,121 - INFO - ANBIMA Fund Data Scraper Completed Successfully
```

#### Localização dos Logs

```
logs/
└── scraper_YYYYMMDD_HHMMSS.log
```

---

## 🔍 Solução de Problemas

### Problemas Comuns

#### 1. Scraper não encontra elementos

**Sintomas:**
- Erros de "element not found"
- Timeouts constantes

**Diagnóstico:**
```bash
python3 main.py --no-headless
```
Observe visualmente o que está acontecendo

**Soluções:**
1. Verificar se site mudou estrutura
2. Aumentar timeouts em `config.py`
3. Limpar cache do navegador:
```bash
rm -rf ~/.wdm/
```

#### 2. Resultados incompletos

**Sintomas:**
- Menos registros que esperado
- Dados faltando

**Diagnóstico:**
Verificar logs em `logs/scraper_*.log`

**Soluções:**
1. Aumentar `SLEEP_BETWEEN_REQUESTS`
2. Verificar conexão com internet
3. Executar em horário de menor tráfego

#### 3. Performance lenta

**Sintomas:**
- Scraper muito lento
- Timeouts frequentes

**Soluções:**
1. Verificar velocidade da internet
2. Fechar outras aplicações
3. Reduzir número de CNPJs por execução
4. Usar modo headless (mais rápido)

#### 4. Erros de memória

**Sintomas:**
- Scraper trava
- Sistema congela

**Soluções:**
1. Processar CNPJs em lotes menores
2. Aumentar swap/memória virtual
3. Fechar outras aplicações

### Debugging Avançado

#### Habilitar Logs Detalhados do Selenium

```python
# Em config.py, adicionar:
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Salvar Screenshots

```python
# Em anbima_scraper.py, adicionar:
driver.save_screenshot('debug_screenshot.png')
```

#### Salvar HTML da Página

```python
# Em anbima_scraper.py, adicionar:
with open('page_source.html', 'w') as f:
    f.write(driver.page_source)
```

---

## ❓ Perguntas Frequentes

### Geral

**P: O scraper funciona em Windows?**
R: Sim, funciona em Windows, macOS e Linux.

**P: Preciso de conhecimentos de programação para usar?**
R: Não, basta seguir o guia de instalação e uso.

**P: É legal fazer scraping do site da ANBIMA?**
R: Os dados são públicos, mas sempre respeite os termos de uso do site.

### Funcionalidades

**P: Quantos CNPJs posso processar de uma vez?**
R: Não há limite técnico, mas recomenda-se lotes de até 50 para evitar bloqueios.

**P: Posso agendar execuções automáticas?**
R: Sim, use cron (Linux/Mac) ou Task Scheduler (Windows).

**P: Como obter dados históricos de meses anteriores?**
R: O site mostra apenas 22 dias úteis. Para histórico maior, execute periodicamente e acumule os dados.

**P: Posso extrair outros campos além de Data e Valor da cota?**
R: Sim, modifique o código em `anbima_scraper.py` para incluir outros campos.

### Técnico

**P: Qual navegador é necessário?**
R: Google Chrome. O ChromeDriver é baixado automaticamente.

**P: Posso usar Firefox ou Edge?**
R: Sim, mas precisa modificar o código para usar GeckoDriver ou EdgeDriver.

**P: O scraper funciona com VPN?**
R: Sim, mas pode ser mais lento dependendo da VPN.

**P: Como acelerar o scraper?**
R: Use modo headless e reduza timeouts se sua conexão for rápida.

---

## ⚠️ Limitações Conhecidas

### Limitações do Site

1. **Dados Históricos**: Apenas 22 dias úteis disponíveis
2. **Sem API**: Não há API oficial da ANBIMA para este tipo de consulta
3. **Rate Limiting**: Site pode bloquear requisições excessivas
4. **Estrutura Dinâmica**: Site pode mudar estrutura HTML sem aviso

### Limitações Técnicas

1. **Dependência do Chrome**: Requer Google Chrome instalado
2. **JavaScript Obrigatório**: Site requer JavaScript habilitado
3. **Conexão Internet**: Necessária durante toda execução
4. **Performance**: ~50 segundos por fundo em média

### Limitações Funcionais

1. **Sem Validação de CNPJ**: Não valida formato antes de consultar
2. **Sem Cache**: Cada execução consulta o site novamente
3. **Sem Paralelização**: Processa um CNPJ por vez
4. **Sem Interface Gráfica**: Apenas linha de comando

---

## 🔄 Manutenção e Atualizações

### Verificando Atualizações

```bash
# Atualizar dependências
pip3 install --upgrade -r requirements.txt

# Verificar versões
pip3 list | grep -E "selenium|pandas|openpyxl"
```

### Backup de Dados

**Recomendado fazer backup de:**
- Arquivos de saída (`output_*.xlsx`)
- Logs (`logs/*.log`)
- Arquivo de entrada (`input_cnpjs.xlsx`)

```bash
# Exemplo de backup
mkdir backup_$(date +%Y%m%d)
cp output_*.xlsx logs/*.log backup_$(date +%Y%m%d)/
```

### Atualizações do Site ANBIMA

Se o site da ANBIMA mudar estrutura:

1. **Verificar seletores** em `config.py`
2. **Atualizar XPath/CSS** conforme necessário
3. **Testar com --no-headless** para debug visual
4. **Consultar logs** para identificar mudanças

### Roadmap de Melhorias

- [ ] **Interface Web**: Dashboard para executar e visualizar resultados
- [ ] **API REST**: Expor funcionalidades via API
- [ ] **Banco de Dados**: Armazenar histórico em PostgreSQL/SQLite
- [ ] **Paralelização**: Processar múltiplos CNPJs simultaneamente
- [ ] **Cache Inteligente**: Evitar consultas duplicadas
- [ ] **Notificações**: Email/Slack ao concluir execução
- [ ] **Análise de Dados**: Gráficos e estatísticas automáticas
- [ ] **Docker**: Containerização para fácil deploy

---

## 📞 Suporte e Contato

### Recursos de Ajuda

1. **Documentação**: Leia este arquivo completamente
2. **Logs**: Sempre verifique `logs/` para detalhes
3. **Debug Visual**: Use `--no-headless` para observar
4. **FAQ**: Consulte seção de Perguntas Frequentes

### Reportando Problemas

Ao reportar problemas, inclua:

1. **Versão do Python**: `python3 --version`
2. **Sistema Operacional**: Windows/macOS/Linux
3. **Arquivo de Log**: Último arquivo em `logs/`
4. **Mensagem de Erro**: Copiar mensagem completa
5. **Passos para Reproduzir**: O que você fez antes do erro

---

## 📄 Licença e Termos de Uso

### Licença

Este projeto é fornecido "como está", sem garantias de qualquer tipo.

### Termos de Uso

- ✅ Uso educacional e pesquisa
- ✅ Modificação do código-fonte
- ✅ Uso comercial interno
- ⚠️ Respeitar termos de uso da ANBIMA
- ⚠️ Não sobrecarregar servidores
- ❌ Revenda de dados sem autorização

### Aviso Legal

Os dados extraídos são de fontes públicas da ANBIMA. O usuário é responsável pelo uso adequado das informações.

---

## 🎓 Créditos e Agradecimentos

**Desenvolvido com:**
- Python 3.9+
- Selenium WebDriver
- Pandas
- OpenPyXL

**Inspirado em:**
- Necessidade de automação de coleta de dados financeiros
- Melhores práticas de web scraping
- Padrões de desenvolvimento Python

---

## 📊 Estatísticas do Projeto

- **Linhas de Código**: ~1.200
- **Módulos**: 4 principais
- **Funções**: 20+
- **Cobertura de Testes**: Manual
- **Tempo Médio de Execução**: ~50s por fundo
- **Taxa de Sucesso**: >95% (em condições normais)

---

**Versão da Documentação**: 1.0  
**Última Atualização**: 23 de Outubro de 2025  
**Compatibilidade**: Python 3.9+

---

**Para mais informações, consulte os comentários no código-fonte.**

