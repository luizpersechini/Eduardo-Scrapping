# 🏗️ Arquitetura Técnica - ANBIMA Data Scraper

Documentação técnica detalhada da arquitetura e implementação do sistema.

---

## 📑 Índice

1. [Visão Geral da Arquitetura](#visão-geral-da-arquitetura)
2. [Componentes do Sistema](#componentes-do-sistema)
3. [Fluxo de Dados](#fluxo-de-dados)
4. [Estrutura de Classes](#estrutura-de-classes)
5. [Decisões de Design](#decisões-de-design)
6. [Padrões Utilizados](#padrões-utilizados)
7. [Estratégias de Web Scraping](#estratégias-de-web-scraping)
8. [Tratamento de Erros](#tratamento-de-erros)
9. [Performance e Otimização](#performance-e-otimização)
10. [Segurança](#segurança)

---

## 🎯 Visão Geral da Arquitetura

### Arquitetura em Camadas

O sistema segue uma arquitetura em camadas com separação clara de responsabilidades:

```
┌─────────────────────────────────────────────────────────┐
│                    CAMADA DE APRESENTAÇÃO                │
│                       (main.py)                          │
│  - CLI Interface                                         │
│  - Logging Setup                                         │
│  - Orchestration                                         │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│                   CAMADA DE NEGÓCIO                      │
│                                                          │
│  ┌──────────────────────┐    ┌──────────────────────┐  │
│  │  anbima_scraper.py   │    │  data_processor.py   │  │
│  │  - Web Automation    │    │  - Data Transform    │  │
│  │  - Data Extraction   │    │  - Excel I/O         │  │
│  │  - Error Handling    │    │  - Validation        │  │
│  └──────────────────────┘    └──────────────────────┘  │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│                  CAMADA DE INFRAESTRUTURA                │
│                                                          │
│  ┌──────────────────────┐    ┌──────────────────────┐  │
│  │     config.py        │    │   Selenium Driver    │  │
│  │  - Constants         │    │   Pandas/OpenPyXL    │  │
│  │  - Settings          │    │   File System        │  │
│  └──────────────────────┘    └──────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### Princípios de Design

1. **Separation of Concerns**: Cada módulo tem uma responsabilidade específica
2. **Single Responsibility**: Cada classe/função faz apenas uma coisa
3. **DRY (Don't Repeat Yourself)**: Evita duplicação de código
4. **Configuration over Code**: Configurações externalizadas em `config.py`
5. **Fail Fast**: Erros são detectados e reportados o mais cedo possível

---

## 🔧 Componentes do Sistema

### 1. main.py - Orquestrador Principal

**Responsabilidade**: Coordenar o fluxo completo da aplicação

**Componentes**:

```python
def setup_logging(output_dir: str) -> logging.Logger
    """
    Configura o sistema de logging
    
    - Cria diretório de logs se não existir
    - Configura handlers (file e console)
    - Define formato de log
    - Retorna logger configurado
    """

def parse_arguments() -> argparse.Namespace
    """
    Processa argumentos da linha de comando
    
    Args suportados:
    - -i, --input: Arquivo Excel de entrada
    - -o, --output: Arquivo Excel de saída
    - --no-headless: Modo visível do navegador
    """

def main()
    """
    Função principal de execução
    
    Fluxo:
    1. Parse de argumentos
    2. Setup de logging
    3. Leitura de CNPJs (via DataProcessor)
    4. Inicialização do scraper (ANBIMAScraper)
    5. Loop de scraping para cada CNPJ
    6. Processamento de resultados
    7. Salvamento em Excel
    8. Geração de relatório
    9. Cleanup de recursos
    """
```

**Dependências**:
- `argparse`: Parsing de CLI
- `logging`: Sistema de logs
- `tqdm`: Barra de progresso
- `anbima_scraper.ANBIMAScraper`
- `data_processor.DataProcessor`

---

### 2. anbima_scraper.py - Motor de Web Scraping

**Responsabilidade**: Automação do navegador e extração de dados

#### Classe: ANBIMAScraper

```python
class ANBIMAScraper:
    """
    Scraper principal para o site da ANBIMA
    
    Attributes:
        driver: WebDriver do Selenium
        wait: WebDriverWait para explicit waits
        logger: Logger para tracking de operações
        headless: Flag para modo headless
    """
    
    def __init__(self, logger: logging.Logger, headless: bool = True)
        """
        Inicializa o scraper
        
        Args:
            logger: Logger para tracking
            headless: Se True, executa navegador invisível
        """
    
    def setup_driver(self) -> bool
        """
        Configura o WebDriver do Chrome
        
        Processo:
        1. Baixa ChromeDriver via webdriver-manager
        2. Corrige path do executable (macOS ARM64)
        3. Define permissões de execução (chmod 755)
        4. Aplica opções do Chrome (config.CHROME_OPTIONS)
        5. Configura timeouts
        6. Cria WebDriverWait
        
        Returns:
            True se sucesso, False se falha
        """
    
    def search_fund(self, cnpj: str) -> Tuple[bool, str]
        """
        Busca fundo por CNPJ no site da ANBIMA
        
        Algoritmo:
        1. Navega para ANBIMA_BASE_URL
        2. Aguarda carregamento (sleep 3s)
        3. Fecha banner de cookies (se presente)
        4. Localiza input de busca
        5. Digita CNPJ
        6. Aguarda dropdown (sleep 3s)
        7. Clica em link do dropdown
        8. Aguarda resultados (sleep 2s)
        9. Fecha dropdown se necessário
        10. Clica no primeiro resultado
        
        Args:
            cnpj: CNPJ formatado ou não
            
        Returns:
            Tuple[sucesso: bool, mensagem: str]
            
        Raises:
            TimeoutException: Se elementos não forem encontrados
        """
    
    def get_fund_name(self) -> Optional[str]
        """
        Extrai nome do fundo da página de detalhes
        
        Seletores tentados (em ordem):
        1. h1 (título principal)
        2. .fund-name (classe específica)
        3. #fundName (ID)
        
        Returns:
            Nome do fundo ou None se não encontrado
        """
    
    def navigate_to_periodic_data(self) -> Tuple[bool, str]
        """
        Navega para aba "Dados Periódicos"
        
        Estratégia:
        - Construção direta de URL
        - Formato: {base_url}/fundos/{fund_code}/dados-periodicos
        - Evita problemas com cliques em elementos
        
        Returns:
            Tuple[sucesso: bool, mensagem: str]
        """
    
    def extract_periodic_data(self) -> Tuple[bool, List[Dict], str]
        """
        Extrai dados periódicos da tabela
        
        Algoritmo:
        1. Aguarda tabela (sleep 3s)
        2. Localiza <table>
        3. Extrai headers (<thead>)
        4. Identifica índices das colunas:
           - "Data competência" → date_idx
           - "Valor cota" → cota_idx
        5. Executa scroll infinito:
           - Scroll até final da página
           - Aguarda 1s
           - Verifica se altura mudou
           - Repete até altura estabilizar (3x igual)
           - Máximo de 50 scrolls
        6. Extrai dados do <tbody>
        7. Remove duplicatas (via set de datas)
        8. Inverte ordem (mais antigo primeiro)
        
        Returns:
            Tuple[sucesso: bool, dados: List[Dict], mensagem: str]
            
        Data Format:
            {
                "Data da cotização": "19/09/2025",
                "Valor cota": "R$ 1,569379"
            }
        """
    
    def scrape_fund_data(self, cnpj: str) -> Dict
        """
        Orquestra extração completa de um fundo
        
        Fluxo:
        1. search_fund(cnpj)
        2. get_fund_name()
        3. navigate_to_periodic_data()
        4. extract_periodic_data()
        5. Compila resultado
        
        Returns:
            {
                "CNPJ": str,
                "Nome do Fundo": str,
                "Dados Periódicos": List[Dict],
                "Status": str
            }
        """
    
    def close(self)
        """
        Cleanup: Fecha navegador e libera recursos
        """
```

**Seletores CSS/XPath**:

```python
# Input de busca
"input[placeholder*='Busque fundos']"

# Link dropdown
"//a[contains(@href, '/busca/fundos?q=')]"

# Botão de cookies
"//button[contains(text(), 'Prosseguir')]"

# Link do fundo nos resultados
"article a[href*='/fundos/C']"

# Tabela de dados
"table"

# Headers
"th, td"
```

---

### 3. data_processor.py - Processador de Dados

**Responsabilidade**: Manipulação de dados e I/O de Excel

#### Classe: DataProcessor

```python
class DataProcessor:
    """
    Processa dados de entrada/saída
    
    Attributes:
        logger: Logger para tracking
    """
    
    def read_cnpj_list(self, input_file: str) -> List[str]
        """
        Lê CNPJs do arquivo Excel
        
        Processo:
        1. Verifica existência do arquivo
        2. Lê com pandas.read_excel()
        3. Procura coluna "CNPJ"
        4. Remove valores nulos
        5. Converte para string
        6. Retorna lista
        
        Args:
            input_file: Caminho do arquivo .xlsx
            
        Returns:
            Lista de CNPJs como strings
            
        Raises:
            FileNotFoundError: Se arquivo não existir
            ValueError: Se coluna CNPJ não existir
        """
    
    def process_scraped_data(self, results: List[Dict]) -> pd.DataFrame
        """
        Transforma resultados em DataFrame
        
        Processo:
        1. Para cada resultado:
           a. Expande dados periódicos
           b. Replica CNPJ e Nome para cada linha
           c. Extrai Data e Valor
        2. Cria DataFrame com colunas:
           - CNPJ
           - Nome do Fundo
           - Data da cotização
           - Valor cota
           - Status
        3. Ordena por CNPJ, depois por Data
        
        Args:
            results: Lista de dicionários de scraping
            
        Returns:
            DataFrame formatado
        """
    
    def save_results(self, df: pd.DataFrame, output_file: str)
        """
        Salva DataFrame em Excel
        
        Processo:
        1. Cria diretório se necessário
        2. Salva com pandas.to_excel()
        3. Usa openpyxl engine
        4. index=False
        
        Args:
            df: DataFrame a salvar
            output_file: Caminho do arquivo de saída
        """
    
    def create_summary_report(self, results: List[Dict]) -> Dict
        """
        Gera relatório de resumo
        
        Calcula:
        - Total de CNPJs processados
        - Sucessos
        - Falhas
        - Taxa de sucesso (%)
        - Tempo total
        
        Returns:
            Dicionário com estatísticas
        """
```

**Estrutura de Dados**:

```python
# Input Excel
{
    "CNPJ": ["48.330.198/0001-06", "34.780.531/0001-66"]
}

# Resultado do Scraper
{
    "CNPJ": "48.330.198/0001-06",
    "Nome do Fundo": "CLASSE ÚNICA...",
    "Dados Periódicos": [
        {"Data da cotização": "19/09/2025", "Valor cota": "R$ 1,569379"},
        {"Data da cotização": "22/09/2025", "Valor cota": "R$ 1,570331"}
    ],
    "Status": "Success"
}

# Output DataFrame
| CNPJ | Nome do Fundo | Data da cotização | Valor cota | Status |
|------|---------------|-------------------|------------|--------|
| ...  | ...           | ...               | ...        | ...    |
```

---

### 4. config.py - Configurações

**Responsabilidade**: Centralizar todas as configurações

```python
# URLs
ANBIMA_BASE_URL = "https://data.anbima.com.br/busca/fundos"

# Timeouts (segundos)
PAGE_LOAD_TIMEOUT = 30
IMPLICIT_WAIT = 10
EXPLICIT_WAIT_LONG = 20
EXPLICIT_WAIT_SHORT = 5

# Retry
RETRY_ATTEMPTS = 3
RETRY_DELAY = 5

# Chrome Options
CHROME_OPTIONS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--window-size=1920,1080",
    "--disable-gpu",
    "--incognito",
    "--disable-extensions",
    "--start-maximized",
    "--disable-infobars",
    "--disable-notifications",
    "--disable-popup-blocking",
    "--disable-logging",
    "--log-level=3"
]

# Paths
INPUT_FILE = "input_cnpjs.xlsx"
OUTPUT_DIR = "output"
LOG_DIR = "logs"

# Excel Schema
INPUT_CNPJ_COLUMN = "CNPJ"
OUTPUT_COLUMNS = [
    "CNPJ",
    "Nome do Fundo",
    "Data da cotização",
    "Valor cota",
    "Status"
]
```

---

## 🔄 Fluxo de Dados

### Fluxo Completo de Execução

```
┌─────────────────────────────────────────────────────┐
│ 1. INICIALIZAÇÃO                                    │
├─────────────────────────────────────────────────────┤
│ main.py                                             │
│   ├─ parse_arguments()                              │
│   ├─ setup_logging()                                │
│   └─ Cria instâncias (Scraper, Processor)          │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│ 2. LEITURA DE ENTRADA                               │
├─────────────────────────────────────────────────────┤
│ DataProcessor.read_cnpj_list()                      │
│   ├─ Lê input_cnpjs.xlsx                            │
│   ├─ Valida estrutura                               │
│   └─ Retorna List[str]                              │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│ 3. SETUP DO SCRAPER                                 │
├─────────────────────────────────────────────────────┤
│ ANBIMAScraper.setup_driver()                        │
│   ├─ Download ChromeDriver                          │
│   ├─ Configura opções                               │
│   └─ Inicializa WebDriver                           │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│ 4. LOOP DE SCRAPING (Para cada CNPJ)                │
├─────────────────────────────────────────────────────┤
│ ANBIMAScraper.scrape_fund_data(cnpj)                │
│   │                                                  │
│   ├─ 4.1. BUSCA                                     │
│   │   └─ search_fund(cnpj)                          │
│   │       ├─ Navega para site                       │
│   │       ├─ Fecha cookies                          │
│   │       ├─ Preenche busca                         │
│   │       └─ Clica em resultado                     │
│   │                                                  │
│   ├─ 4.2. NOME DO FUNDO                             │
│   │   └─ get_fund_name()                            │
│   │       └─ Extrai <h1>                            │
│   │                                                  │
│   ├─ 4.3. NAVEGAÇÃO                                 │
│   │   └─ navigate_to_periodic_data()                │
│   │       └─ Constrói URL /dados-periodicos         │
│   │                                                  │
│   └─ 4.4. EXTRAÇÃO                                  │
│       └─ extract_periodic_data()                    │
│           ├─ Localiza tabela                        │
│           ├─ Identifica colunas                     │
│           ├─ Scroll infinito                        │
│           ├─ Extrai dados                           │
│           └─ Remove duplicatas                      │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│ 5. PROCESSAMENTO                                    │
├─────────────────────────────────────────────────────┤
│ DataProcessor.process_scraped_data(results)         │
│   ├─ Expande dados periódicos                       │
│   ├─ Cria DataFrame                                 │
│   └─ Ordena cronologicamente                        │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│ 6. SAÍDA                                            │
├─────────────────────────────────────────────────────┤
│ DataProcessor.save_results(df, output_file)         │
│   └─ Salva output_*.xlsx                            │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│ 7. RELATÓRIO                                        │
├─────────────────────────────────────────────────────┤
│ DataProcessor.create_summary_report(results)        │
│   └─ Imprime estatísticas                           │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│ 8. CLEANUP                                          │
├─────────────────────────────────────────────────────┤
│ ANBIMAScraper.close()                               │
│   └─ driver.quit()                                  │
└─────────────────────────────────────────────────────┘
```

---

## 🎨 Decisões de Design

### 1. Por que Selenium e não Requests/BeautifulSoup?

**Decisão**: Usar Selenium WebDriver

**Razões**:
- Site ANBIMA é **JavaScript-heavy** (React/Next.js)
- Dados carregam **dinamicamente** (AJAX)
- Necessário **simular interação** (cliques, scroll)
- **Lazy loading** de dados históricos
- Requests/BS4 não conseguem executar JavaScript

**Trade-offs**:
- ✅ Acesso a conteúdo dinâmico
- ✅ Simulação realista de usuário
- ❌ Mais lento que requests
- ❌ Maior consumo de recursos

### 2. Por que ChromeDriver e não Firefox/Edge?

**Decisão**: Chrome como navegador padrão

**Razões**:
- **Mais popular** e testado
- **Melhor documentação** e suporte
- **webdriver-manager** funciona bem com Chrome
- **Melhor performance** em headless mode

**Flexibilidade**: Código permite adaptação para outros browsers

### 3. Por que Pandas para Excel e não xlrd/xlwt direto?

**Decisão**: Usar Pandas + OpenPyXL

**Razões**:
- **API mais simples** e intuitiva
- **Transformações de dados** facilitadas
- **OpenPyXL** suporta .xlsx moderno
- **Integração** com resto do ecossistema de dados

### 4. Por que Configuração Centralizada?

**Decisão**: Todas configs em `config.py`

**Razões**:
- **Single source of truth**
- Fácil ajuste sem modificar código
- Facilita **testes** e **manutenção**
- Permite **environment-specific configs**

### 5. Por que Logging ao invés de Print?

**Decisão**: Uso de módulo `logging`

**Razões**:
- **Níveis de log** (INFO, WARNING, ERROR)
- **Persistência** em arquivos
- **Timestamps** automáticos
- **Controle de verbosidade**
- **Production-ready**

---

## 🛠️ Padrões Utilizados

### 1. Dependency Injection

```python
class ANBIMAScraper:
    def __init__(self, logger: logging.Logger, headless: bool = True):
        self.logger = logger  # Injected dependency
```

**Benefícios**:
- Testabilidade
- Flexibilidade
- Desacoplamento

### 2. Single Responsibility Principle

Cada classe tem uma responsabilidade:
- `ANBIMAScraper`: Web scraping
- `DataProcessor`: Data I/O
- `main.py`: Orchestration
- `config.py`: Configuration

### 3. Configuration Object Pattern

```python
# config.py centraliza todas as configurações
from config import ANBIMA_BASE_URL, PAGE_LOAD_TIMEOUT
```

### 4. Error Handling com Try-Except-Finally

```python
try:
    driver = setup_driver()
    result = scrape_data()
except TimeoutException as e:
    logger.error(f"Timeout: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
finally:
    driver.quit()  # Sempre executa cleanup
```

### 5. Context Manager (Implícito)

```python
# Pandas usa context managers internamente
df.to_excel(filename)  # File handle é fechado automaticamente
```

### 6. Factory Pattern (ChromeDriver)

```python
def setup_driver(self):
    driver_path = ChromeDriverManager().install()  # Factory
    driver = webdriver.Chrome(service=Service(driver_path))
    return driver
```

---

## 🕷️ Estratégias de Web Scraping

### 1. Waits Strategy

#### Explicit Waits (Preferencial)
```python
wait = WebDriverWait(driver, 20)
element = wait.until(
    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
)
```

**Quando usar**: Elementos específicos que podem demorar

#### Implicit Waits
```python
driver.implicitly_wait(10)
```

**Quando usar**: Configuração global de base

#### Sleep (Último Recurso)
```python
time.sleep(3)
```

**Quando usar**: AJAX conhecidamente lento, animações

### 2. Scroll Infinito

```python
last_height = 0
same_height_count = 0
max_scrolls = 50

while scroll_count < max_scrolls:
    # Scroll to bottom
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)
    
    # Check if height changed
    new_height = driver.execute_script("return document.body.scrollHeight")
    
    if new_height == last_height:
        same_height_count += 1
        if same_height_count >= 3:
            break  # 3 scrolls sem mudança = fim
    else:
        same_height_count = 0
    
    last_height = new_height
    scroll_count += 1
```

**Por que 3 scrolls estáveis?**: Garantir que não há mais dados carregando

### 3. Deduplicação

```python
seen_dates = set()
for row in rows:
    date = extract_date(row)
    if date not in seen_dates:
        data.append(row_data)
        seen_dates.add(date)
```

**Por que?**: Scroll pode duplicar elementos do DOM

### 4. Seletor Robusto

```python
# Tenta múltiplos seletores
selectors = [
    "h1",
    ".fund-name",
    "#fundName"
]

for selector in selectors:
    try:
        element = driver.find_element(By.CSS_SELECTOR, selector)
        if element.text:
            return element.text
    except:
        continue
```

### 5. URL Construction

```python
# Ao invés de clicar em tab (pode falhar)
current_url = driver.current_url
fund_code = extract_code(current_url)
periodic_url = f"{base}/fundos/{fund_code}/dados-periodicos"
driver.get(periodic_url)  # Navegação direta mais confiável
```

---

## 🛡️ Tratamento de Erros

### Hierarquia de Exceções

```
Exception
├── TimeoutException (Selenium)
│   └── Elemento não encontrado em tempo
├── NoSuchElementException (Selenium)
│   └── Elemento não existe no DOM
├── StaleElementReferenceException (Selenium)
│   └── Elemento removido do DOM após referência
├── FileNotFoundError (Python)
│   └── Arquivo de entrada não existe
└── ValueError (Python)
    └── Dados inválidos ou coluna CNPJ ausente
```

### Estratégia de Retry

```python
max_retries = 3
for attempt in range(max_retries):
    try:
        result = risky_operation()
        break  # Sucesso, sai do loop
    except (TimeoutException, NoSuchElementException) as e:
        logger.warning(f"Attempt {attempt + 1} failed: {e}")
        if attempt < max_retries - 1:
            time.sleep(RETRY_DELAY)
        else:
            logger.error("Max retries reached")
            result = {'Status': 'Failed'}
```

### Graceful Degradation

```python
def get_fund_name(self):
    try:
        return self._extract_from_h1()
    except:
        try:
            return self._extract_from_title()
        except:
            return "Unknown Fund"  # Fallback
```

---

## ⚡ Performance e Otimização

### Bottlenecks Identificados

1. **Page Load**: 3-5s por página
2. **Scroll**: 1s por scroll × ~10 scrolls = 10s
3. **Network Latency**: 2-3s por requisição
4. **Total**: ~50s por fundo

### Otimizações Implementadas

#### 1. Headless Mode
```python
chrome_options.add_argument("--headless")
```
**Ganho**: ~20% mais rápido

#### 2. Disable Images/CSS (Opcional)
```python
prefs = {
    "profile.managed_default_content_settings.images": 2,
    "profile.managed_default_content_settings.stylesheets": 2
}
chrome_options.add_experimental_option("prefs", prefs)
```
**Ganho**: ~30% mais rápido, mas pode quebrar seletores

#### 3. Minimal Waits
```python
# Apenas waits necessários
time.sleep(1)  # Ao invés de 3s
```

#### 4. Smart Scrolling
```python
# Para ao detectar estabilidade
if same_height_count >= 3:
    break
```

### Otimizações Futuras

#### Paralelização
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(scrape_fund, cnpj) for cnpj in cnpjs]
    results = [f.result() for f in futures]
```

**Ganho Potencial**: 5x para 5 workers

**Trade-off**: Mais carga no site (respeitar rate limits)

---

## 🔒 Segurança

### 1. Anti-Detection

```python
# User Agent realista
"user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)..."

# Disable automation flags
"--disable-blink-features=AutomationControlled"

# Incognito mode
"--incognito"
```

### 2. Rate Limiting

```python
time.sleep(2)  # Entre requisições
```

### 3. Sanitização de Entrada

```python
def sanitize_cnpj(cnpj: str) -> str:
    """Remove caracteres especiais"""
    return re.sub(r'[^\d]', '', cnpj)
```

### 4. Validation

```python
if not cnpj or len(cnpj) < 14:
    raise ValueError("Invalid CNPJ")
```

---

## 📊 Métricas e Monitoramento

### Logs Estruturados

```python
logger.info(f"Processing CNPJ: {cnpj}")
logger.info(f"Extracted {len(data)} records")
logger.error(f"Failed: {error_msg}")
```

### Métricas Coletadas

- Total de CNPJs processados
- Taxa de sucesso (%)
- Tempo médio por fundo
- Erros por tipo
- Registros extraídos

### Exemplo de Log

```
2025-10-23 11:03:41,543 - INFO - ANBIMA Fund Data Scraper Started
2025-10-23 11:03:41,611 - INFO - Found 2 CNPJs to process
2025-10-23 11:03:45,221 - INFO - WebDriver initialized successfully
2025-10-23 11:04:32,934 - INFO - Successfully extracted 22 records for 48.330.198/0001-06
2025-10-23 11:05:22,121 - INFO - Scraping completed - Success: 2/2 (100.0%)
```

---

## 🔮 Roadmap Técnico

### Curto Prazo
- [ ] Testes unitários com pytest
- [ ] CI/CD com GitHub Actions
- [ ] Type checking com mypy

### Médio Prazo
- [ ] API REST com FastAPI
- [ ] PostgreSQL para armazenamento
- [ ] Docker containerization

### Longo Prazo
- [ ] Dashboard web com React
- [ ] Processamento distribuído
- [ ] Machine learning para detecção de mudanças no site

---

**Versão da Documentação**: 1.0  
**Última Atualização**: 23 de Outubro de 2025  
**Compatibilidade**: Python 3.9+

