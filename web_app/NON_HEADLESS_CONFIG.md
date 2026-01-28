# Web App - Configuração NON-HEADLESS

## 📋 Resumo

A Web App foi configurada para rodar em **modo NON-headless** (janelas de Chrome visíveis) devido a problemas de detecção de bots e timeouts no modo headless.

---

## ✅ Mudanças Implementadas

### 1. **scraper_service.py**

Todas as instâncias do scraper foram configuradas com `headless=False`:

```python
# Linha 173 - Pre-inicialização
scraper = ANBIMAScraper(headless=False)

# Linha 187 - Teste de workers
scraper = ANBIMAScraper(headless=False)

# Linha 229 - Scraping individual
scraper = ANBIMAScraper(headless=False)
```

### 2. **config.py**

Configurações otimizadas para web app:

```python
DEFAULT_WORKERS = 2  # Reduzido para estabilidade com retries
MAX_WORKERS = 4      # Máximo permitido

PAGE_LOAD_TIMEOUT = 45
ELEMENT_WAIT_TIMEOUT = 30
IMPLICIT_WAIT = 10
SLEEP_BETWEEN_REQUESTS = 2
```

### 3. **Sistema de Retry**

- **2 tentativas** por CNPJ (`max_retries = 2`)
- **Driver reiniciado** entre tentativas
- **Delay de 3s** antes de retry
- **Delay de 2s** entre fechamento e próxima tentativa

---

## 🎯 Comportamento Esperado

### ✅ Sucesso
- Janelas de Chrome **visíveis** durante scraping
- **1ª tentativa** pode falhar com timeout
- **2ª tentativa** geralmente tem sucesso
- Taxa de sucesso: **~90%+** com retries

### ⏱️ Performance
- **1 CNPJ**: ~1-2 minutos (com retry)
- **10 CNPJs** (2 workers): ~5-10 minutos
- **50 CNPJs** (2 workers): ~25-50 minutos

### 👁️ Visual
- Você verá **múltiplas janelas** de Chrome abertas simultaneamente
- **Não feche** as janelas manualmente
- Sistema fecha automaticamente após scraping

---

## 🚀 Como Usar

### 1. Iniciar a Web App

```bash
cd web_app
python3 app.py
```

Ou use o script:

```bash
./start_web_app.sh
```

### 2. Acessar no Navegador

```
http://localhost:5001
```

### 3. Upload de Excel

- Arquivo deve conter coluna **CNPJ**
- Formato: `XX.XXX.XXX/XXXX-XX`

### 4. Configurar Workers

- **Recomendado**: 2 workers (padrão)
- **Máximo**: 4 workers

### 5. Iniciar Job

- Clique em "Iniciar Scraping"
- Acompanhe progresso em tempo real
- Janelas de Chrome aparecerão

### 6. Download de Resultados

- Após conclusão, baixe o Excel
- Formato pivot: Datas × CNPJs

---

## ⚠️ Importante

### ✅ FAÇA

- Deixe as janelas Chrome rodando
- Aguarde conclusão do job
- Use retry para CNPJs falhados

### ❌ NÃO FAÇA

- Não feche janelas Chrome manualmente
- Não inicie múltiplos jobs simultaneamente
- Não use mais de 4 workers

---

## 🐛 Troubleshooting

### Problema: Todos CNPJs falhando

**Causa**: Processos Chrome antigos ainda rodando

**Solução**:
```bash
# Mate todos processos Chrome
pkill -9 "Google Chrome"
pkill -9 chromedriver

# Reinicie a web app
cd web_app && python3 app.py
```

### Problema: Timeout na primeira tentativa

**Causa**: Normal, site ANBIMA pode ser lento

**Solução**: Sistema faz retry automático, aguarde

### Problema: Port 5001 em uso

**Causa**: Web app já rodando

**Solução**:
```bash
lsof -ti:5001 | xargs kill -9
```

---

## 📊 Comparação: CLI vs Web App

| Aspecto | Script CLI | Web App |
|---------|-----------|---------|
| Interface | Terminal | Browser |
| Feedback | Logs | Tempo real |
| Configuração | Linha de comando | Formulário |
| Histórico | Não | Sim (database) |
| Retry Manual | Não | Sim (botão) |
| Headless | ✅ Sim | ❌ Não |
| Recomendado para | Produção/batch | Testes/poucos CNPJs |

---

## 🔮 Futuro: Modo Headless

### Por que não funciona agora?

1. Site ANBIMA detecta bots em headless
2. Timeouts mais frequentes
3. Elementos não carregam corretamente

### Quando usar headless novamente?

- Quando site ANBIMA melhorar
- Com proxies rotativos
- Com user-agent melhor
- Com delays maiores

### Como ativar headless (quando funcionar)?

Mude em `web_app/scraper_service.py`:

```python
# Linhas 173, 187, 229
scraper = ANBIMAScraper(headless=True)  # Mudar False → True
```

---

## 📝 Notas Técnicas

- **Database**: SQLite (`web_app/scraping.db`)
- **Upload folder**: `web_app/uploads/`
- **Output folder**: `web_app/outputs/`
- **Socket.IO**: Real-time updates
- **Flask**: Development server (não produção)

---

## ✅ Status Atual

- ✅ CLI funcionando perfeitamente (headless)
- ✅ Web App funcionando (NON-headless)
- ✅ Sistema de retry implementado
- ✅ Real-time feedback
- ✅ Database persistente
- ⏳ Headless mode (futuro)

---

**Última atualização**: 2025-10-31
**Versão**: 1.0
**Modo**: NON-HEADLESS ativo






