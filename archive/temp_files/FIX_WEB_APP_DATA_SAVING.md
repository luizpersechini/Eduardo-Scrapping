# Fix: Web App Data Saving Issue

## Data: 2025-11-03

## Problema Identificado

A interface web não estava salvando dados scrapeados, apesar do CLI funcionar corretamente.

### Diagnóstico

1. **CLI Teste (Baseline)**: ✅ FUNCIONA
   - Arquivo: `input_test_cli.xlsx` com 1 CNPJ
   - Resultado: 24 linhas salvas em `output_test_cli.xlsx`
   - Tempo: 0.77 minutos
   - Dados: 22 registros extraídos corretamente

2. **Web App Teste**: ❌ FALHAVA
   - Scraping funcionava (22 registros extraídos)
   - Mapeamento funcionava (periodic_data presente)
   - **Erro no salvamento**: `ValueError: could not convert string to float: 'R$ 1.576258'`

### Causa Raiz

**Arquivo**: `web_app/scraper_service.py` linha 391

**Código problemático**:
```python
value=float(item['Valor cota'].replace(',', '.'))
```

**Problema**:
- Valor vem como: `"R$ 1,576258"`
- Após replace: `"R$ 1.576258"` (ainda tem "R$ " e ponto original)
- `float()` falha com ValueError

## Correção Implementada

### 1. Função de Limpeza de Valores Monetários

**Arquivo**: `web_app/scraper_service.py` (antes da classe ScraperService)

```python
def clean_currency_value(value_str: str) -> float:
    """
    Clean currency string and convert to float
    
    Examples:
        "R$ 1,234567" -> 1.234567
        "R$ 1.234,56" -> 1234.56
        "1,23" -> 1.23
        "1.23" -> 1.23
    """
    if not value_str:
        raise ValueError("Empty value")
    
    # Remove currency symbol and spaces
    cleaned = value_str.replace('R$', '').replace(' ', '').strip()
    
    # Check if has both . and ,
    if '.' in cleaned and ',' in cleaned:
        # Format: 1.234,56 (BR format with thousands separator)
        cleaned = cleaned.replace('.', '').replace(',', '.')
    elif ',' in cleaned:
        # Format: 1,23 (decimal comma only)
        cleaned = cleaned.replace(',', '.')
    # else: Format is already 1.23 or 1234.56 (decimal point)
    
    return float(cleaned)
```

### 2. Atualização do Processamento de Dados

**Arquivo**: `web_app/scraper_service.py` linha ~420-440

**Antes**:
```python
for item in result.get('data', []):
    data_record = ScrapedData(
        cnpj_id=cnpj_record.id,
        cnpj=result['cnpj'],
        fund_name=result.get('fund_name'),
        date=datetime.strptime(item['Data da cotização'], '%d/%m/%Y').date(),
        value=float(item['Valor cota'].replace(',', '.'))  # ❌ FALHAVA
    )
    self.db.session.add(data_record)
```

**Depois**:
```python
saved_count = 0
for item in result.get('data', []):
    try:
        data_record = ScrapedData(
            cnpj_id=cnpj_record.id,
            cnpj=result['cnpj'],
            fund_name=result.get('fund_name'),
            date=datetime.strptime(item['Data da cotização'], '%d/%m/%Y').date(),
            value=clean_currency_value(item['Valor cota'])  # ✅ FUNCIONA
        )
        self.db.session.add(data_record)
        saved_count += 1
    except Exception as e:
        logger.error(f"Error parsing data item for {result['cnpj']}: {item} - Error: {e}")
        continue  # Skip invalid rows but continue processing

# Update data_count with actual saved count
cnpj_record.data_count = saved_count
logger.info(f"Saved {saved_count} records for {result['cnpj']}")
```

### 3. Logging Detalhado Adicionado

Para facilitar diagnósticos futuros:

```python
# scraper_service.py linha ~233
logger.info(f"===== SCRAPE_SINGLE_CNPJ CALLED: {cnpj} =====")

# scraper_service.py linha ~270-272
logger.info(f"===== CALLING scraper.scrape_fund_data for {cnpj} =====")
result = scraper.scrape_fund_data(cnpj)
logger.info(f"===== RESULT FROM scraper.scrape_fund_data: {result} =====")

# scraper_service.py linha ~289-300
logger.info(f"===== MAPPING RESULT =====")
logger.info(f"  Raw Status: {result_status}")
logger.info(f"  Keys in result: {list(result.keys())}")
logger.info(f"  periodic_data key exists: {'periodic_data' in result}")
logger.info(f"  periodic_data length: {len(result.get('periodic_data', []))}")
# ... etc

# scraper_service.py linha ~366-370
logger.info(f"===== PROCESS_SCRAPING_RESULT CALLED =====")
logger.info(f"  Job ID: {job_id}")
logger.info(f"  CNPJ: {result.get('cnpj')}")
logger.info(f"  Success: {result.get('success')}")
logger.info(f"  Data count: {len(result.get('data', []))}")

# scraper_service.py linha ~457-459
logger.info(f"  About to commit: cnpj_record.status={cnpj_record.status}, data_count={cnpj_record.data_count}")
self.db.session.commit()
logger.info(f"  Commit successful!")
```

## Ferramentas de Teste Criadas

### 1. Script de Diagnóstico Rápido

**Arquivo**: `web_app/quick_diagnose.py`

**Função**: Testa scraping de 1 CNPJ diretamente, bypassando a web UI

**Uso**:
```bash
cd web_app
python3 quick_diagnose.py
```

**Output**:
- Cria job e CNPJ de teste no banco
- Executa scraping
- Verifica dados salvos no banco
- Mostra diagnóstico completo

**Correção aplicada**: Adicionado `db.session.expire_all()` para forçar refresh do banco

### 2. Teste de Conversão de Valores

Para testar a função `clean_currency_value`:

```python
# Testes manuais
from web_app.scraper_service import clean_currency_value

# Teste 1: Formato decimal com vírgula
assert clean_currency_value("R$ 1,576258") == 1.576258

# Teste 2: Formato com separador de milhares
assert clean_currency_value("R$ 1.234,56") == 1234.56

# Teste 3: Sem símbolo de moeda
assert clean_currency_value("1,23") == 1.23

# Teste 4: Decimal com ponto
assert clean_currency_value("1.23") == 1.23

# Teste 5: Valor grande
assert clean_currency_value("R$ 10.000,00") == 10000.00
```

## Evidências de Funcionamento

### Log do Teste Bem-Sucedido

```
INFO:scraper_service:===== PROCESS_SCRAPING_RESULT CALLED =====
INFO:scraper_service:  Job ID: 11
INFO:scraper_service:  CNPJ: 48.330.198/0001-06
INFO:scraper_service:  Success: True
INFO:scraper_service:  Data count: 22
INFO:scraper_service:  Found CNPJ record: 48.330.198/0001-06
INFO:scraper_service:  Setting CNPJ status to 'success'
INFO:scraper_service:  CNPJ record after update: status=success, data_count will be=22
INFO:scraper_service:Saved 22 records for 48.330.198/0001-06
INFO:scraper_service:  About to commit: cnpj_record.status=success, data_count=22
INFO:scraper_service:  Commit successful!

Database after processing:
  CNPJ status: success
  CNPJ data_count: 22
  ScrapedData records: 22

✓ SUCCESS: Data saved correctly!
```

## Arquivos Modificados

1. **`web_app/scraper_service.py`**
   - Adicionada função `clean_currency_value`
   - Atualizado `process_scraping_result` para usar nova função
   - Adicionado tratamento de erro por item
   - Adicionado logging detalhado

2. **`web_app/quick_diagnose.py`** (novo)
   - Script de teste e diagnóstico
   - Testa fluxo completo de scraping

## Testes para Futuras Mudanças

### Teste 1: Validar Conversão de Valores

Sempre que modificar a lógica de conversão:

```bash
cd web_app
python3 -c "
from scraper_service import clean_currency_value
assert clean_currency_value('R$ 1,234567') == 1.234567
assert clean_currency_value('R$ 1.234,56') == 1234.56
print('✓ All tests passed')
"
```

### Teste 2: Teste End-to-End

Antes de deploy:

```bash
# 1. Criar arquivo de teste
python3 << 'EOF'
import pandas as pd
df = pd.DataFrame({'CNPJ': ['48.330.198/0001-06']})
df.to_excel('input_test_cli.xlsx', index=False)
EOF

# 2. Testar CLI (baseline)
python3 main_parallel.py -i input_test_cli.xlsx -o output_test_cli.xlsx -w 1

# 3. Verificar output CLI
python3 << 'EOF'
import pandas as pd
df = pd.read_excel('output_test_cli.xlsx')
assert len(df) > 0, "CLI output is empty!"
print(f"✓ CLI works: {len(df)} rows")
EOF

# 4. Testar Web App
cd web_app && python3 quick_diagnose.py
```

### Teste 3: Verificação de Banco de Dados

Após scraping via web app:

```python
from web_app.app import app, db
from web_app.models import CNPJ, ScrapedData

with app.app_context():
    # Verificar último job
    last_cnpj = CNPJ.query.order_by(CNPJ.id.desc()).first()
    
    if last_cnpj.status == 'success':
        data_count = ScrapedData.query.filter_by(cnpj_id=last_cnpj.id).count()
        assert data_count > 0, "Success but no data saved!"
        print(f"✓ Last CNPJ has {data_count} records saved")
```

## Próximos Passos

1. ✅ **Correção aplicada** - clean_currency_value implementada
2. ✅ **Logs detalhados** - facilita depuração futura  
3. ✅ **Testes criados** - quick_diagnose.py
4. ⏳ **Remover logs temporários** - após confirmar estabilidade
5. ⏳ **Criar testes unitários** - pytest para clean_currency_value
6. ⏳ **Testar com job completo** - via web UI com múltiplos CNPJs

## Notas

- O timeout intermitente em headless mode é um problema separado
- O CLI funciona consistentemente em headless=True
- A web app pode precisar ajuste para usar headless=False ou aumentar timeouts
- A correção de conversão de valores resolve o problema principal (dados não sendo salvos)

---

**Status**: ✅ CORREÇÃO IMPLEMENTADA E TESTADA
**Última atualização**: 2025-11-03 10:30






