# 🔧 Guia de Troubleshooting - ANBIMA Data Scraper

Guia completo para diagnóstico e solução de problemas.

---

## 📑 Índice

1. [Problemas de Instalação](#problemas-de-instalação)
2. [Problemas com WebDriver](#problemas-com-webdriver)
3. [Problemas de Scraping](#problemas-de-scraping)
4. [Problemas de Rede](#problemas-de-rede)
5. [Problemas com Dados](#problemas-com-dados)
6. [Problemas de Performance](#problemas-de-performance)
7. [Ferramentas de Diagnóstico](#ferramentas-de-diagnóstico)
8. [Logs e Como Interpretá-los](#logs-e-como-interpretá-los)

---

## 🔧 Problemas de Instalação

### Erro: `ModuleNotFoundError: No module named 'selenium'`

**Sintoma**:
```
Traceback (most recent call last):
  File "main.py", line 3, in <module>
    from selenium import webdriver
ModuleNotFoundError: No module named 'selenium'
```

**Causa**: Dependências não instaladas

**Solução**:
```bash
# Instalar todas as dependências
pip3 install -r requirements.txt

# Verificar instalação
pip3 list | grep selenium
```

---

### Erro: `pip: command not found`

**Sintoma**:
```bash
$ pip install selenium
-bash: pip: command not found
```

**Causa**: pip não instalado ou não no PATH

**Solução**:

**macOS/Linux**:
```bash
# Usar pip3
pip3 install -r requirements.txt

# Ou instalar pip
python3 -m ensurepip --upgrade
```

**Windows**:
```cmd
# Reinstalar Python marcando "Add to PATH"
# Ou usar:
python -m pip install -r requirements.txt
```

---

### Erro: `Permission denied` ao instalar pacotes

**Sintoma**:
```
ERROR: Could not install packages due to an OSError: [Errno 13] Permission denied
```

**Causa**: Tentativa de instalar em diretório do sistema

**Solução**:

**Opção 1 - User Install (Recomendado)**:
```bash
pip3 install --user -r requirements.txt
```

**Opção 2 - Virtual Environment**:
```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

**Opção 3 - sudo (Não Recomendado)**:
```bash
sudo pip3 install -r requirements.txt
```

---

## 🚗 Problemas com WebDriver

### Erro: `Failed to initialize WebDriver: [Errno 8] Exec format error`

**Sintoma**:
```
Failed to initialize WebDriver: [Errno 8] Exec format error: '/Users/.../chromedriver-mac-arm64/THIRD_PARTY_NOTICES.chromedriver'
```

**Causa**: ChromeDriver path incorreto (bug do webdriver-manager no macOS ARM64)

**Solução**: Já implementada no código, mas se persistir:

```bash
# Limpar cache do webdriver-manager
rm -rf ~/.wdm/

# Executar novamente
python3 main.py
```

**Verificação Manual**:
```bash
# Encontrar chromedriver
find ~/.wdm -name "chromedriver" -type f

# Dar permissão de execução
chmod +x /caminho/para/chromedriver

# Testar execução
/caminho/para/chromedriver --version
```

---

### Erro: `This version of ChromeDriver only supports Chrome version XX`

**Sintoma**:
```
SessionNotCreatedException: Message: session not created: This version of ChromeDriver only supports Chrome version 141
```

**Causa**: Incompatibilidade entre Chrome e ChromeDriver

**Solução**:

**Opção 1 - Atualizar Chrome**:
```
1. Abrir Google Chrome
2. Menu → Ajuda → Sobre o Google Chrome
3. Aguardar atualização automática
4. Reiniciar navegador
```

**Opção 2 - Limpar cache do ChromeDriver**:
```bash
rm -rf ~/.wdm/
python3 main.py
```

**Opção 3 - Versão específica**:
```python
# Em anbima_scraper.py
from webdriver_manager.chrome import ChromeDriverManager

driver_path = ChromeDriverManager(version="141.0.7390.122").install()
```

---

### Erro: `Chrome binary not found`

**Sintoma**:
```
WebDriverException: Message: unknown error: cannot find Chrome binary
```

**Causa**: Google Chrome não instalado

**Solução**:

**macOS**:
```bash
# Verificar se Chrome está instalado
ls /Applications/Google\ Chrome.app/

# Se não estiver, baixar de:
open https://www.google.com/chrome/

# Instalar e executar novamente
```

**Linux**:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install google-chrome-stable

# Fedora
sudo dnf install google-chrome-stable
```

**Windows**:
```
1. Baixar de https://www.google.com/chrome/
2. Instalar normalmente
3. Executar novamente
```

---

### Erro: `DevToolsActivePort file doesn't exist`

**Sintoma**:
```
WebDriverException: Message: unknown error: DevToolsActivePort file doesn't exist
```

**Causa**: Chrome não consegue iniciar (geralmente em modo headless)

**Solução**:

**Teste sem headless**:
```bash
python3 main.py --no-headless
```

**Se funcionar, problema é com headless. Adicionar opções**:
```python
# Em config.py, adicionar:
"--disable-dev-shm-usage",
"--no-sandbox",
"--disable-setuid-sandbox"
```

**Linux específico**:
```bash
# Instalar dependências
sudo apt install -y xvfb

# Executar com display virtual
xvfb-run python3 main.py
```

---

## 🕷️ Problemas de Scraping

### Erro: `TimeoutException: Message: timeout: Timed out receiving message from renderer`

**Sintoma**:
```
selenium.common.exceptions.TimeoutException: Message: timeout: Timed out receiving message from renderer: XX.XXX
```

**Causa**: Página demorou muito para carregar

**Diagnóstico**:
```bash
# 1. Testar internet
ping google.com

# 2. Testar site ANBIMA
curl -I https://data.anbima.com.br/busca/fundos

# 3. Executar com modo visível
python3 main.py --no-headless
```

**Solução**:

**Aumentar timeouts**:
```python
# Em config.py
PAGE_LOAD_TIMEOUT = 60  # Era 30
EXPLICIT_WAIT_LONG = 40  # Era 20
```

**Verificar conexão**:
```bash
# Testar velocidade
speedtest-cli  # Instalar com: pip install speedtest-cli
```

---

### Erro: `NoSuchElementException: Message: no such element: Unable to locate element`

**Sintoma**:
```
selenium.common.exceptions.NoSuchElementException: Message: no such element: Unable to locate element: {"method":"css selector","selector":"input[placeholder*='Busque fundos']"}
```

**Causa**: 
1. Seletor mudou (site foi atualizado)
2. Elemento não carregou ainda
3. Elemento está em iframe

**Diagnóstico**:

**Teste 1 - Modo visível**:
```bash
python3 main.py --no-headless
# Observe se elementos aparecem
```

**Teste 2 - Verificar HTML**:
```python
# Adicionar em anbima_scraper.py temporariamente
with open('page_debug.html', 'w', encoding='utf-8') as f:
    f.write(driver.page_source)
```

**Teste 3 - Screenshot**:
```python
# Adicionar em anbima_scraper.py
driver.save_screenshot('debug_screenshot.png')
```

**Solução**:

**Aumentar waits**:
```python
# Adicionar antes de localizar elemento
time.sleep(5)  # Espera fixa

# Ou usar explicit wait
wait = WebDriverWait(driver, 30)
element = wait.until(
    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
)
```

**Atualizar seletores**:
```python
# Testar seletores alternativos
selectors = [
    "input[placeholder*='Busque']",
    "input.search-input",
    "#searchInput"
]

for sel in selectors:
    try:
        element = driver.find_element(By.CSS_SELECTOR, sel)
        break
    except:
        continue
```

---

### Erro: `StaleElementReferenceException`

**Sintoma**:
```
selenium.common.exceptions.StaleElementReferenceException: Message: stale element reference: element is not attached to the page document
```

**Causa**: Elemento foi removido/recriado no DOM (comum com scroll/AJAX)

**Solução**:

**Re-localizar elemento**:
```python
# RUIM
element = driver.find_element(By.ID, "myId")
time.sleep(5)
element.click()  # Pode falhar se DOM mudou

# BOM
def click_element_safe(driver, by, selector):
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            element = driver.find_element(by, selector)
            element.click()
            return True
        except StaleElementReferenceException:
            if attempt < max_attempts - 1:
                time.sleep(1)
            else:
                raise
```

---

### Problema: Dados incompletos extraídos (apenas 22 linhas)

**Sintoma**: Excel tem menos registros que o esperado

**Diagnóstico**:
```bash
# 1. Verificar logs
cat logs/scraper_*.log | grep "Found.*rows"

# 2. Executar com modo visível
python3 main.py --no-headless
# Observar se scroll está funcionando
```

**Causa Provável**: 
- Site mudou mecanismo de lazy loading
- Scroll não está carregando mais dados
- Limite de dados no site (22 dias úteis é o máximo)

**Solução**:

**Aumentar scrolls**:
```python
# Em anbima_scraper.py, método extract_periodic_data
max_scrolls = 100  # Era 50
```

**Aumentar delay entre scrolls**:
```python
time.sleep(2)  # Era 1s
```

**Verificar se há paginação**:
```python
# Procurar por botões de paginação
try:
    next_button = driver.find_element(By.CSS_SELECTOR, "button.next")
    while next_button:
        next_button.click()
        time.sleep(2)
        # Extrair dados da nova página
except:
    pass  # Sem paginação
```

---

## 🌐 Problemas de Rede

### Erro: `ConnectionRefusedError` ou `Connection refused`

**Sintoma**:
```
requests.exceptions.ConnectionError: HTTPConnectionPool(host='127.0.0.1', port=XXXXX): Max retries exceeded
```

**Causa**: 
1. Sem internet
2. Site fora do ar
3. Firewall bloqueando

**Diagnóstico**:
```bash
# 1. Testar internet
ping 8.8.8.8

# 2. Testar DNS
nslookup data.anbima.com.br

# 3. Testar site
curl -I https://data.anbima.com.br/busca/fundos

# 4. Verificar firewall
# macOS
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# Linux
sudo ufw status
```

**Solução**:

**Aguardar site voltar**:
```bash
# Monitorar site
while true; do
    curl -I https://data.anbima.com.br/busca/fundos && break
    sleep 10
done
```

**Verificar proxy/VPN**:
```bash
# Desabilitar temporariamente
# Testar novamente
```

---

### Erro: HTTP 423 (Locked) ou 429 (Too Many Requests)

**Sintoma**:
```
Server responded with status 423: Locked
```

**Causa**: Site bloqueou requisições (rate limiting)

**Diagnóstico**:
```bash
# Verificar logs para ver quantas requisições foram feitas
grep "Searching for CNPJ" logs/scraper_*.log | wc -l
```

**Solução**:

**Aumentar delay entre requisições**:
```python
# Em config.py (criar variável se não existe)
SLEEP_BETWEEN_REQUESTS = 5  # Era 2

# Em main.py, adicionar no loop:
for cnpj in cnpjs:
    result = scraper.scrape_fund_data(cnpj)
    time.sleep(SLEEP_BETWEEN_REQUESTS)
```

**Executar em outro horário**:
```bash
# Executar de madrugada (menos tráfego)
crontab -e
# Adicionar:
0 3 * * * cd /caminho/projeto && python3 main.py
```

**Reduzir volume**:
```bash
# Processar em lotes menores
# Dividir input_cnpjs.xlsx em múltiplos arquivos
```

---

### Erro: `SSLError` ou `Certificate verify failed`

**Sintoma**:
```
ssl.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed
```

**Causa**: Problema com certificado SSL do site

**Solução**:

**Atualizar certificados**:
```bash
# macOS
/Applications/Python\ 3.X/Install\ Certificates.command

# Linux
sudo update-ca-certificates

# Windows
# Reinstalar Python com opção "Install certificates"
```

**Workaround (não recomendado)**:
```python
# Apenas para debug, NUNCA em produção
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
```

---

## 📊 Problemas com Dados

### Erro: `No CNPJs found in input file`

**Sintoma**:
```
ERROR - No CNPJs found in input file: input_cnpjs.xlsx
```

**Causa**: 
1. Arquivo não tem coluna "CNPJ"
2. Coluna está vazia
3. Nome da coluna está errado

**Diagnóstico**:
```python
# Verificar estrutura do Excel
import pandas as pd
df = pd.read_excel('input_cnpjs.xlsx')
print(df.columns.tolist())  # Ver nomes das colunas
print(df.head())  # Ver primeiras linhas
```

**Solução**:

**Corrigir nome da coluna**:
```
Deve ser exatamente: CNPJ
Não: cnpj, Cnpj, CNPJ:, CNPJ , etc.
```

**Verificar formato**:
```python
# Criar arquivo correto
import pandas as pd
df = pd.DataFrame({
    "CNPJ": ["48.330.198/0001-06", "34.780.531/0001-66"]
})
df.to_excel("input_cnpjs.xlsx", index=False)
```

---

### Problema: CNPJs válidos retornam "No fund found"

**Sintoma**: Excel mostra Status = "No fund found for this CNPJ"

**Diagnóstico**:

**Teste 1 - Verificar CNPJ manualmente**:
```
1. Abrir https://data.anbima.com.br/busca/fundos
2. Buscar CNPJ manualmente
3. Verificar se aparece resultado
```

**Teste 2 - Verificar formatação**:
```python
# CNPJ deve estar como string
cnpj = "48.330.198/0001-06"  # BOM
# ou
cnpj = "48330198000106"  # BOM (sem formatação)

# NÃO como número
cnpj = 48330198000106  # RUIM (perde zeros à esquerda)
```

**Solução**:

**Garantir formato correto**:
```python
# Em data_processor.py
def read_cnpj_list(self, input_file: str) -> List[str]:
    df = pd.read_excel(input_file, dtype={'CNPJ': str})  # Força string
    cnpjs = df['CNPJ'].astype(str).tolist()
    return cnpjs
```

**Limpar formatação**:
```python
# Se CNPJ vier sem formatação, adicionar
def format_cnpj(cnpj: str) -> str:
    cnpj = re.sub(r'\D', '', cnpj)  # Remove não-dígitos
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:14]}"
```

---

### Problema: Valores de cota estão como texto, não número

**Sintoma**: Excel mostra "R$ 1,569379" em formato texto

**Causa**: Dados vêm formatados como string do site

**Solução**:

**Converter para número**:
```python
# Em data_processor.py, adicionar método
def clean_currency(value: str) -> float:
    """
    Converte 'R$ 1,569379' para 1.569379
    """
    # Remove R$ e espaços
    value = value.replace('R$', '').strip()
    # Troca vírgula por ponto
    value = value.replace(',', '.')
    # Remove pontos de milhares
    parts = value.split('.')
    if len(parts) > 2:
        value = ''.join(parts[:-1]) + '.' + parts[-1]
    return float(value)

# Aplicar na extração
df['Valor cota'] = df['Valor cota'].apply(clean_currency)
```

---

## ⚡ Problemas de Performance

### Problema: Scraper muito lento (>2 min por fundo)

**Diagnóstico**:
```bash
# 1. Verificar velocidade de internet
speedtest-cli

# 2. Ver onde está demorando (adicionar timers)
```

**Solução**:

**Reduzir waits desnecessários**:
```python
# Revisar todos os time.sleep()
# Reduzir onde possível
time.sleep(1)  # Ao invés de 3
```

**Usar modo headless**:
```bash
# Sempre mais rápido
python3 main.py  # headless por padrão
```

**Desabilitar imagens**:
```python
# Em config.py, CHROME_OPTIONS adicionar:
prefs = {
    "profile.managed_default_content_settings.images": 2,
    "profile.default_content_setting_values.notifications": 2,
}
chrome_options.add_experimental_option("prefs", prefs)
```

---

### Problema: Consumo alto de memória (>1 GB)

**Diagnóstico**:
```bash
# Monitorar uso de memória
top -pid $(pgrep -f "python3 main.py")

# Ou
ps aux | grep python
```

**Solução**:

**Processar em lotes**:
```bash
# Dividir CNPJs em múltiplos arquivos
# Processar um por vez
for file in batch_*.xlsx; do
    python3 main.py -i "$file"
done
```

**Limpar variáveis**:
```python
# Após processar cada CNPJ
import gc
gc.collect()  # Força garbage collection
```

**Fechar driver entre fundos**:
```python
# Se memória crítica
for cnpj in cnpjs:
    scraper = ANBIMAScraper(logger)
    result = scraper.scrape_fund_data(cnpj)
    scraper.close()
    # Recria para próximo
```

---

## 🛠️ Ferramentas de Diagnóstico

### 1. Modo Debug Visível

```bash
python3 main.py --no-headless
```

**O que observar**:
- Navegador abre e você vê o que está acontecendo
- Identifica exatamente onde falha
- Verifica se elementos carregam

### 2. Salvar Screenshot

```python
# Adicionar em anbima_scraper.py onde falha
def save_debug_screenshot(self, name="debug"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_{timestamp}.png"
    self.driver.save_screenshot(filename)
    self.logger.info(f"Screenshot saved: {filename}")
```

### 3. Salvar HTML da Página

```python
def save_page_source(self, name="page"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_{timestamp}.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(self.driver.page_source)
    self.logger.info(f"Page source saved: {filename}")
```

### 4. Logging Detalhado

```python
# Em config.py ou main.py
import logging
logging.basicConfig(
    level=logging.DEBUG,  # Mais verboso
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 5. Console do Navegador

```python
# Capturar erros JavaScript
logs = driver.get_log('browser')
for log in logs:
    print(log)
```

### 6. Network Monitor

```python
# Capturar requisições de rede
caps = DesiredCapabilities.CHROME.copy()
caps['goog:loggingPrefs'] = {'performance': 'ALL'}
driver = webdriver.Chrome(desired_capabilities=caps)

# Depois
logs = driver.get_log('performance')
for log in logs:
    print(log['message'])
```

---

## 📋 Logs e Como Interpretá-los

### Estrutura do Log

```
TIMESTAMP - NIVEL - MENSAGEM
```

**Exemplo**:
```
2025-10-23 11:03:41,543 - INFO - ANBIMA Fund Data Scraper Started
```

### Níveis de Log

- **DEBUG**: Informações detalhadas para diagnóstico
- **INFO**: Confirmação de operações normais
- **WARNING**: Algo inesperado, mas não impede execução
- **ERROR**: Erro sério, pode impedir funcionalidade
- **CRITICAL**: Erro muito grave, sistema não pode continuar

### Mensagens Comuns

#### ✅ Sucesso

```
INFO - WebDriver initialized successfully
INFO - Found 2 CNPJs to process
INFO - Successfully extracted 22 records
INFO - ✓ Successfully scraped data for 48.330.198/0001-06
```

#### ⚠️ Avisos

```
WARNING - Timeout while searching for CNPJ, retrying...
WARNING - Could not find fund name, using default
WARNING - Error processing row: stale element
```

#### ❌ Erros

```
ERROR - Failed to initialize WebDriver: [Errno 8] Exec format error
ERROR - Timeout: Page took too long to load
ERROR - No fund found for this CNPJ: 12.345.678/0001-00
ERROR - Could not find required columns in table
```

### Analisando Logs de Erro

**Exemplo de log de erro**:
```
2025-10-23 11:04:15,234 - ERROR - Error searching for fund 48.330.198/0001-06: Message: timeout: Timed out receiving message from renderer: 20.000
Stacktrace:
    ... [stack trace completo]
```

**Análise**:
1. **Timestamp**: 11:04:15 (quando aconteceu)
2. **Nível**: ERROR (erro sério)
3. **Operação**: Busca de fundo
4. **CNPJ**: 48.330.198/0001-06
5. **Erro específico**: Timeout de 20s
6. **Causa provável**: Página demorou >20s para carregar

**Ação**: Aumentar timeout ou verificar conexão

### Filtrar Logs

```bash
# Ver apenas erros
grep "ERROR" logs/scraper_*.log

# Ver sucessos
grep "Successfully" logs/scraper_*.log

# Ver específico CNPJ
grep "48.330.198" logs/scraper_*.log

# Contar erros
grep -c "ERROR" logs/scraper_*.log
```

---

## 🆘 Quando Pedir Ajuda

Se após seguir este guia o problema persistir, abra uma issue incluindo:

### Checklist de Informações

- [ ] **Versão do Python**: `python3 --version`
- [ ] **Sistema Operacional**: macOS/Windows/Linux + versão
- [ ] **Versão do Chrome**: Menu → Sobre
- [ ] **Comando exato** que foi executado
- [ ] **Mensagem de erro completa** (copiar tudo)
- [ ] **Últimas 50 linhas do log**:
  ```bash
  tail -50 logs/scraper_*.log
  ```
- [ ] **Arquivo de entrada** (primeiras linhas):
  ```python
  import pandas as pd
  print(pd.read_excel('input_cnpjs.xlsx').head())
  ```
- [ ] **Screenshot** (se modo visível)
- [ ] **Passos já tentados** deste guia

---

## 📞 Recursos Adicionais

- **Documentação Principal**: [README.md](README.md)
- **Arquitetura**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Contribuindo**: [CONTRIBUTING.md](CONTRIBUTING.md)
- **Selenium Docs**: https://selenium-python.readthedocs.io/
- **Stack Overflow**: https://stackoverflow.com/questions/tagged/selenium

---

**Última Atualização**: 23 de Outubro de 2025  
**Versão**: 1.0

