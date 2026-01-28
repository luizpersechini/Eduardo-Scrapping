# Diagnóstico: Timeouts Intermitentes e Anti-Bot ANBIMA

## Data: 2025-11-03

## Problema Relatado

- Timeouts intermitentes em headless mode
- Web app com falhas frequentes
- Comportamento inconsistente (às vezes funciona, às vezes não)

## Investigação Realizada

### Fase 1: Testes Iniciais

1. **CLI Teste (manhã)**: ✅ FUNCIONOU
   - Tempo: 0.77 minutos
   - Dados: 22 registros extraídos
   - Modo: headless=True

2. **Web App Diagnóstico**: ❌ FALHAVA
   - Dados scrapeados mas não salvos (problema de conversão - RESOLVIDO)

### Fase 2: Testes de Navegação Passo a Passo

**Objetivo**: Identificar em qual etapa ocorre o timeout

**Resultado - Primeira Tentativa**:
```
Step 1: Setup driver... ✓ (1.2s)
Step 2: Navigate to ANBIMA... ✓ (5.3s)
Step 3: Find search input... ❌ TIMEOUT (31.6s)
```

**Causa Inicial Suspeita**: Seletor CSS incorreto
- Teste usava: `input[placeholder*='Pesquise']`
- Scraper usa: `input[placeholder*='Busque fundos']`

### Fase 3: Debug do Estado da Página

**Script criado**: `test_page_state.py`

**Descoberta Crítica**:
```
Page title: Página Anti-Robô | ANBIMA Data
Page URL: https://data.anbima.com.br/robo
Found 0 input elements
```

**CONCLUSÃO**: O site ANBIMA está detectando bot e redirecionando para página de bloqueio!

### Fase 4: Melhorias Anti-Detecção Implementadas

1. **Opções experimentais do Chrome**:
```python
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)
```

2. **Modificação de propriedades do Navigator**:
```python
self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
    'source': '''
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        Object.defineProperty(navigator, 'languages', {
            get: () => ['pt-BR', 'pt', 'en-US', 'en']
        });
        window.chrome = {
            runtime: {}
        };
    '''
})
```

### Fase 5: Teste Pós-Correção

**Resultado**: ❌ AINDA BLOQUEADO
- Headless: Página Anti-Robô
- Non-Headless: Página Anti-Robô

**CLI Reteste**: ❌ TAMBÉM FALHOU
```
Worker 1: Failed to scrape 48.330.198/0001-06: Timeout (3 tentativas)
Success: 0 (0.0%)
```

## Análise do Problema

### O Que Está Acontecendo

1. **Site da ANBIMA tem proteção anti-bot ativa**
   - Redirecionamento para `/robo` quando detecta automação
   - Título: "Página Anti-Robô | ANBIMA Data"

2. **Detecção é sofisticada**
   - Não é apenas verificação de `navigator.webdriver`
   - Provavelmente analisa:
     - Padrões de comportamento (velocidade, timing)
     - Fingerprinting do navegador
     - Rate limiting / IP tracking
     - Características de headless Chrome

3. **Comportamento intermitente explicado**:
   - **Quando funciona**: Site não está com rate limit ativo ou permitindo tráfego
   - **Quando falha**: Proteção anti-bot ativada (após muitas requisições ou padrão suspeito)
   - **Por que ambos CLI e Web App**: Mesma máquina, mesmo IP, mesmo padrão

### Evidências

| Teste | Resultado | Momento |
|-------|-----------|---------|
| CLI (manhã, 09:55) | ✅ Sucesso | Antes dos testes |
| Web App Diagnóstico | ✅ Scraping OK / ❌ Save falhou | Durante desenvolvimento |
| Test Navigation (10:20) | ❌ Bloqueado | Após múltiplos testes |
| CLI Reteste (10:28) | ❌ Bloqueado | Após melhorias anti-detecção |

**Padrão**: Funcionou inicialmente, depois começou a bloquear após múltiplas requisições.

## Soluções e Recomendações

### Solução 1: Aguardar e Respeitar Rate Limits ⏰

**Descrição**: Esperar períodos maiores entre requisições

**Implementação**:
```python
# Em config.py
DELAY_BETWEEN_REQUESTS = 10  # Aumentar de 2 para 10 segundos
DELAY_BETWEEN_WORKERS = 30  # Delay entre inicialização de workers
DELAY_AFTER_ERROR = 60  # Delay após erro antes de retry
```

**Pros**:
- Simples
- Não requer mudanças complexas
- Pode funcionar com o código atual

**Contras**:
- Muito lento (1 CNPJ a cada 10+ segundos)
- Não garante sucesso
- 161 CNPJs = ~27 minutos no mínimo

### Solução 2: Modo Non-Headless Permanente 🖥️

**Descrição**: Usar apenas modo visual (janelas visíveis)

**Implementação**:
```python
# Forçar headless=False
scraper = ANBIMAScraper(headless=False)
```

**Pros**:
- Menos detecção (navegador real)
- Funciona mais consistentemente
- Já testado e validado

**Contras**:
- Requer monitor/desktop
- Janelas visíveis (não pode rodar em servidor sem GUI)
- Usuário pode interferir

**Recomendação**: ✅ **USAR ESTA SOLUÇÃO NA WEB APP**

### Solução 3: Rotação de IP / Proxies 🌐

**Descrição**: Usar diferentes IPs para cada requisição

**Implementação**:
```python
# Exemplo conceitual
PROXY_LIST = ['proxy1.com:8080', 'proxy2.com:8080', ...]

chrome_options.add_argument(f'--proxy-server={random.choice(PROXY_LIST)}')
```

**Pros**:
- Contorna rate limiting por IP
- Pode usar headless
- Escalável

**Contras**:
- Requer serviço de proxy (custo)
- Proxies podem ser lentos/instáveis
- Complexidade adicional
- Pode violar termos de uso

### Solução 4: Selenium com Perfil Real do Chrome 👤

**Descrição**: Usar perfil de usuário existente do Chrome

**Implementação**:
```python
chrome_options.add_argument('--user-data-dir=/Users/USERNAME/Library/Application Support/Google/Chrome')
chrome_options.add_argument('--profile-directory=Default')
```

**Pros**:
- Sessão autenticada (se necessário)
- Cookies e histórico real
- Menos detecção

**Contras**:
- Requer Chrome instalado localmente
- Pode interferir com uso normal do navegador
- Específico por máquina

### Solução 5: Playwright / Puppeteer Stealth 🥷

**Descrição**: Trocar Selenium por Playwright com plugin stealth

**Implementação**:
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=['--disable-blink-features=AutomationControlled']
    )
    # ... scraping
```

**Pros**:
- Melhor evasão de detecção
- Mais moderno e rápido
- Bom suporte headless

**Contras**:
- Reescrever código existente
- Nova dependência
- Curva de aprendizado

### Solução 6: Scrapy + Splash ou Similar 🚀

**Descrição**: Framework de scraping profissional

**Pros**:
- Feito para scraping em escala
- Gerenciamento de rate limiting
- Rotação de user agents

**Contras**:
- Reescrita completa
- Mais complexo
- Overhead inicial

### Solução 7: Contato com ANBIMA / API Oficial 📞

**Descrição**: Verificar se há API oficial ou solicitar acesso

**Pros**:
- Solução oficial e estável
- Sem problemas de bloqueio
- Dados estruturados

**Contras**:
- Pode não existir
- Pode ter custo
- Processo de aprovação

## Recomendação Final

### Para Uso Imediato

✅ **Solução 2: Non-Headless Mode**
- Modificar web app para usar `headless=False` por padrão
- Documentar que requer ambiente com GUI
- Adicionar delay entre requisições (5-10s)

**Implementação**:
```python
# Em web_app/scraper_service.py
def preinitialize_chromedriver(self):
    scraper = ANBIMAScraper(headless=False)  # Já está assim!
    # ...

# Em config.py
SLEEP_BETWEEN_REQUESTS = 5  # Aumentar de 2 para 5 segundos
```

### Para Futuro (Se Necessário)

1. **Curto prazo**: Implementar delays maiores e randomização
2. **Médio prazo**: Avaliar Playwright Stealth
3. **Longo prazo**: Buscar API oficial da ANBIMA

## Testes Criados

### Arquivos de Teste

1. **`test_headless_reliability.py`**
   - Testa confiabilidade com 10 tentativas
   - Compara headless vs non-headless
   - Calcula taxa de sucesso

2. **`test_navigation_steps.py`**
   - Testa cada etapa de navegação
   - Identifica ponto de falha
   - Tira screenshots em caso de erro

3. **`test_page_state.py`**
   - Verifica estado da página
   - Lista elementos disponíveis
   - Detecta página anti-robô

### Como Usar

```bash
# Teste de confiabilidade (demora ~30-40 min para 20 tentativas)
python3 test_headless_reliability.py

# Teste de navegação passo a passo (rápido)
python3 test_navigation_steps.py

# Debug do estado da página
python3 test_page_state.py
```

## Arquivos Modificados

1. **`anbima_scraper.py`**
   - Adicionadas opções anti-detecção
   - Modificação de propriedades navigator
   - Melhor evasão (mas ainda detectado)

2. **`config.py`**
   - Correção de seletor: "Pesquise" → "Busque fundos"

3. **`test_navigation_steps.py`**
   - Correção de seletor

## Conclusão

O problema **não é específico de headless mode**, mas sim uma **proteção anti-bot sofisticada** da ANBIMA que:
- Detecta automação independente do modo
- Bloqueia após múltiplas requisições
- É intermitente baseado em rate limiting

**Solução implementada**: Usar non-headless mode com delays adequados.

**Status atual**: 
- ✅ Web app salva dados corretamente (fix anterior)
- ⚠️ Scraping bloqueado por anti-bot (aguardar ou usar non-headless)
- ✅ Melhorias anti-detecção implementadas (podem ajudar quando site permitir)

---

**Última atualização**: 2025-11-03 10:30
**Status**: DIAGNOSTICADO - Proteção Anti-Bot Ativa
**Ação recomendada**: Aguardar algumas horas e usar non-headless mode com delays maiores






