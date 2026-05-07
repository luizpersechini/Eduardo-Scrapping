# Como Testar o Scraping

## Guia de Testes Rápidos

### 🚀 Iniciar Teste Agendado (2 horas)

```bash
cd "/Users/LuizPersechini_1/Projects/Eduardo Scrapping"
./agendar_teste.sh
```

**O que faz**:
1. ⏳ Aguarda 2 horas (com contador)
2. 🧪 Testa navegação em headless e non-headless
3. 🔍 Verifica estado da página
4. 📊 Executa scraping completo de 1 CNPJ
5. ✅ Mostra resultado

**Pressione Ctrl+C para cancelar**

---

### ⚡ Teste Rápido Imediato (5 min)

Se quiser testar AGORA sem esperar:

```bash
cd "/Users/LuizPersechini_1/Projects/Eduardo Scrapping"

# 1. Verificar estado da página
python3 test_page_state.py

# 2. Se página OK, teste scraping
python3 main_parallel.py -i input_test_cli.xlsx -o output_test_rapido.xlsx -w 1
```

---

### 🔬 Teste de Confiabilidade (30-40 min)

Para estatísticas completas:

```bash
python3 test_headless_reliability.py
```

**O que faz**:
- 10 tentativas em headless mode
- 10 tentativas em non-headless mode
- Mostra taxa de sucesso

---

### 📋 Interpretação dos Resultados

#### ✅ SUCESSO - Página Carregou

```
Page title: Busca de Fundos | ANBIMA Data
Found X input elements
```

**Ação**: Site acessível! Pode processar lista completa.

#### ❌ BLOQUEADO - Anti-Robô

```
Page title: Página Anti-Robô | ANBIMA Data
Found 0 input elements
```

**Ação**: Aguardar mais tempo ou usar non-headless com delays maiores.

#### ⚠️ TIMEOUT - Timeout na Navegação

```
Timeout while searching for CNPJ
```

**Ação**: 
- Verificar screenshot gerado
- Tentar aumentar timeouts
- Verificar logs

---

### 🛠️ Limpeza de Testes Anteriores

```bash
# Limpar screenshots antigos
rm debug_page_*.png 2>/dev/null

# Limpar logs antigos
rm teste_agendado_*.log 2>/dev/null

# Limpar outputs de teste
rm output_test_*.xlsx 2>/dev/null

# Matar processos Chrome antigos
pkill -9 "Google Chrome"
pkill -9 chromedriver
```

---

### 📊 Verificar Resultado do Teste

```bash
# Ver últimas linhas do log
tail -50 teste_agendado_*.log

# Ver conteúdo do Excel gerado
python3 << 'EOF'
import pandas as pd
df = pd.read_excel('output_test_rapido.xlsx')
print(f"Linhas: {len(df)}")
print(df.head())
EOF

# Ver estatísticas
grep -E "(Success|Failed|Timeout)" teste_agendado_*.log
```

---

### 🎯 Próximos Passos Baseados no Resultado

#### Se TESTE SUCEDEU ✅

```bash
# Processar lista completa com 2 workers
python3 main_parallel.py -i input_cnpjs_optimized.xlsx -o output_final.xlsx -w 2
```

#### Se TESTE FALHOU ❌

```bash
# Opção 1: Aguardar mais e tentar novamente
sleep 3600  # 1 hora
./agendar_teste.sh  # Rodar novamente

# Opção 2: Usar modos não testados
# Modificar config.py:
# - Aumentar PAGE_LOAD_TIMEOUT para 60
# - Aumentar SLEEP_BETWEEN_REQUESTS para 10

# Opção 3: Contatar suporte ANBIMA sobre API oficial
```

---

### 📞 Troubleshooting

#### "Page Anti-Robô"

**Solução**: Aguardar 2-4 horas, limpar cache Chrome, tentar de outro IP

#### "Timeout"

**Solução**: Aumentar timeouts em `config.py`, usar non-headless

#### "No such file: input_test_cli.xlsx"

**Solução**:
```bash
python3 << 'EOF'
import pandas as pd
df = pd.DataFrame({'CNPJ': ['48.330.198/0001-06']})
df.to_excel('input_test_cli.xlsx', index=False)
print("Criado")
EOF
```

#### "Permission denied: agendar_teste.sh"

**Solução**: 
```bash
chmod +x agendar_teste.sh
```

---

### 📖 Arquivos de Referência

- `HEADLESS_MODE_DIAGNOSIS.md` - Diagnóstico completo
- `FIX_WEB_APP_DATA_SAVING.md` - Correção de salvamento
- `test_*.py` - Scripts de teste
- Screenshots `debug_page_*.png` - Estado da página

---

**Última atualização**: 2025-11-03






