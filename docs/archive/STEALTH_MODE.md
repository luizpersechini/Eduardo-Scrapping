# Modo Stealth - Undetected ChromeDriver

## O que é?

O **Modo Stealth** usa a biblioteca `undetected-chromedriver` para evitar que sites detectem automação. É útil quando você encontra:
- Página "Anti-Robô"
- Bloqueios de bot
- reCAPTCHA aparecendo frequentemente
- Timeouts intermitentes

## Como Funciona?

O undetected-chromedriver:
1. Modifica o ChromeDriver para remover indicadores de automação
2. Simula comportamento humano (delays aleatórios, movimentos de mouse)
3. Mascara propriedades JavaScript que revelam bot
4. Usa um navegador mais "realista"

## ⚠️ AVISOS LEGAIS IMPORTANTES

**LEIA ANTES DE USAR:**

1. **Respeito Legal**: 
   - Verifique os **Termos de Uso da ANBIMA**
   - Scraping pode violar políticas do site
   - Use responsavelmente e por sua própria conta e risco

2. **API Oficial**:
   - A ANBIMA oferece **ANBIMA Feed** - uma API oficial
   - Considere solicitar acesso autorizado antes de usar scraping

3. **Fins Educacionais**:
   - Este modo é para fins educacionais e de pesquisa
   - Não use para finalidades comerciais sem autorização

**Ao usar este modo, você assume total responsabilidade legal pelo uso.**

## Como Usar?

### CLI (Linha de Comando)

```bash
# Usar modo stealth
python3 main_parallel.py -i input_cnpjs.xlsx -o output.xlsx --stealth

# Combinar com outras opções
python3 main_parallel.py -i input.xlsx -o output.xlsx -w 2 --stealth --no-headless
```

**Opções:**
- `--stealth`: Ativa modo stealth
- `-w N`: Número de workers (recomendado: 1-2 com stealth)
- `--no-headless`: Ver navegador (útil para debug)

### Web App

1. Acesse http://localhost:5001
2. Faça upload do arquivo Excel
3. Marque checkbox "Usar Modo Stealth"
4. Clique em "Upload e Criar Job"

**Observação**: Modo stealth é **mais lento** (3-7s de delays entre ações)

## Configurações

Arquivo: `config.py`

```python
# Stealth mode settings
STEALTH_MODE = False  # Default
STEALTH_MIN_DELAY = 3.0  # Delay mínimo (segundos)
STEALTH_MAX_DELAY = 7.0  # Delay máximo (segundos)
STEALTH_MOUSE_MOVEMENTS = True  # Simular mouse
```

**Ajustar Delays:**
- Maior delay = menos chance de detecção, mais lento
- Menor delay = mais rápido, maior risco
- Recomendado: 3-7s para bom equilíbrio

## Limitações

### ❌ Não Faz:

- **Não resolve CAPTCHA automaticamente**
  - Se CAPTCHA aparecer, você precisará resolver manualmente
  - Considere usar serviços pagos (2captcha, anticaptcha)
  
- **Não garante 100% de sucesso**
  - Depende de quão sofisticada é a detecção do site
  - Taxa de sucesso: ~60-80% dependendo do site

### ✅ Faz:

- **Evita detecção básica**:
  - Remove `navigator.webdriver`
  - Oculta propriedades de automação
  - Simula comportamento humano
  
- **Funciona melhor que Selenium puro**:
  - Menos bloqueios
  - Mais estável com delays apropriados

## Performance

### Comparação

| Método | Velocidade | Taxa de Sucesso | Bloqueios |
|--------|-----------|-----------------|-----------|
| Selenium Normal | ⚡⚡⚡ Rápido | ~30-50% | Frequentes |
| Selenium Anti-Detection | ⚡⚡ Médio | ~50-70% | Às vezes |
| **Stealth Mode** | ⚡ Lento | **~60-80%** | Raros |
| Manual | 🐌 Muito Lento | 100% | Nunca |

### Velocidade Estimada

- **Normal**: ~5-10 segundos por CNPJ
- **Stealth**: ~15-30 segundos por CNPJ

Para 161 CNPJs:
- Normal: ~13-27 minutos (se não bloquear)
- Stealth: ~40-80 minutos (mais estável)

## Quando Usar?

### ✅ Use Stealth Mode Quando:

1. Site bloquear frequentemente
2. Aparecer página "anti-robô"
3. Precisar de **estabilidade** acima de velocidade
4. Rate limiting ativo
5. Sem acesso a API oficial

### ❌ NÃO Use Stealth Quando:

1. Site está acessível normalmente
2. Prioridade é **velocidade**
3. Nunca teve problemas de bloqueio
4. Tem acesso a API oficial

## Troubleshooting

### "Página Anti-Robô" Ainda Aparece

**Possíveis causas:**
1. **Rate limiting muito agressivo**
   - Solução: Aumentar delays (5-10s)
   - Usar apenas 1 worker por vez
   - Aguardar 1-2 horas antes de tentar novamente

2. **Detecção muito sofisticada**
   - Solução: Stealth não é suficiente
   - Considere: API oficial ou serviços pagos de proxy

3. **ChromeDriver desatualizado**
   - Solução: Deixe undetected-chromedriver baixar automaticamente

### Timeout Frequente

**Causa**: Delays muito longos em stealth mode

**Solução**:
```python
# Em config.py - reduzir delays
STEALTH_MIN_DELAY = 2.0  # De 3.0
STEALTH_MAX_DELAY = 5.0  # De 7.0
```

### Erro ao Instalar

```bash
pip3 install "undetected-chromedriver>=3.5.4"
```

Se falhar, atualize pip:
```bash
python3 -m pip install --upgrade pip
```

## Testes

### Teste Rápido

```bash
# Criar arquivo de teste
python3 << 'EOF'
import pandas as pd
df = pd.DataFrame({'CNPJ': ['48.330.198/0001-06']})
df.to_excel('test_stealth.xlsx', index=False)
print("Arquivo criado")
EOF

# Testar stealth
python3 main_parallel.py -i test_stealth.xlsx -o output_test.xlsx --stealth --no-headless
```

### Scripts de Teste Disponíveis

1. **test_stealth_isolated.py**: Testa scraper isoladamente
2. **test_stealth_page_state.py**: Verifica acesso à página
3. **test_navigation_steps.py**: Testa navegação passo a passo

## Alternativas

Se stealth mode não funcionar, considere:

1. **API ANBIMA Feed**
   - Contatar ANBIMA: https://data.anbima.com.br
   - Acesso oficial e autorizado

2. **Serviços Pagos de Proxies**
   - Rotating proxies residenciais
   - Custam ~$50-200/mês

3. **Serviços de Resolução de CAPTCHA**
   - 2captcha, anticaptcha
   - ~$2-3 por 1000 CAPTCHAs

4. **Playwright Stealth**
   - Mais moderno que Selenium
   - Requer reescrita do código

## Logs

Quando usar stealth mode, logs mostrarão:

```
Stealth mode: True
PRE-INITIALIZATION: Downloading ChromeDriver (STEALTH mode)
Stealth WebDriver initialized successfully
```

Procure por "Stealth" nos logs para confirmar uso.

## Suporte

- **Issues**: Verifique `HEADLESS_MODE_DIAGNOSIS.md` para troubleshooting
- **Documentação**: Leia `COMO_TESTAR.md` para testes
- **Legal**: Consulte `LICENSE.md` e `README.md`

## Licença

Veja `LICENSE.md` para detalhes completos.

**Resumo**: MIT License - use por sua própria responsabilidade.

---

**Última atualização**: 2025-11-03  
**Versão**: 1.0  
**Compatibilidade**: Python 3.9+, Chrome 141+






