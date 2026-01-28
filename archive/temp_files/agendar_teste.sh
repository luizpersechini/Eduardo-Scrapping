#!/bin/bash

# Script para agendar teste de scraping após 2 horas
# Criado: 2025-11-03

echo "================================================"
echo "AGENDAMENTO DE TESTE DE SCRAPING"
echo "================================================"
echo ""
echo "Tempo de espera: 2 horas (7200 segundos)"
echo "Iniciando contagem regressiva..."
echo ""
echo "Pressione Ctrl+C para cancelar"
echo ""

# Contador regressivo
for i in {7200..1..300}; do
    minutes=$((i / 60))
    printf "\rRestam %d minutos... (%d segundos)  " $minutes $i
    sleep 300  # Sleep 5 minutos e atualiza
done
printf "\rRestam 0 minutos. Iniciando teste...                           \n"
echo ""

echo "================================================"
echo "INICIANDO TESTE"
echo "================================================"
echo ""

# Criar arquivo de teste se não existir
if [ ! -f "input_test_cli.xlsx" ]; then
    echo "Criando arquivo de teste..."
    python3 << 'PYEOF'
import pandas as pd
df = pd.DataFrame({'CNPJ': ['48.330.198/0001-06']})
df.to_excel('input_test_cli.xlsx', index=False)
print("✓ Arquivo input_test_cli.xlsx criado")
PYEOF
fi

# Teste 1: Navigation Steps (rápido)
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TESTE 1: Navigation Steps (RÁPIDO)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 << 'PYEOF'
from test_navigation_steps import test_navigation_steps

print("\n🧪 HEADLESS MODE:")
try:
    test_navigation_steps(headless=True)
    print("✅ HEADLESS: PASSOU")
except Exception as e:
    print(f"❌ HEADLESS: FALHOU - {str(e)[:100]}")

print("\n🧪 NON-HEADLESS MODE:")
try:
    test_navigation_steps(headless=False)
    print("✅ NON-HEADLESS: PASSOU")
except Exception as e:
    print(f"❌ NON-HEADLESS: FALHOU - {str(e)[:100]}")
PYEOF

# Teste 2: Page State (verifica se ainda está bloqueado)
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TESTE 2: Page State Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 << 'PYEOF'
from test_page_state import debug_page_state
import time

for mode in [True, False]:
    mode_name = "HEADLESS" if mode else "NON-HEADLESS"
    print(f"\n--- Testing {mode_name} ---")
    try:
        debug_page_state(headless=mode)
        time.sleep(2)
    except Exception as e:
        print(f"ERROR: {e}")
PYEOF

# Teste 3: CLI Full Test (scraping completo)
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TESTE 3: CLI Full Scraping"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

timestamp=$(date +%Y%m%d_%H%M%S)
log_file="teste_agendado_${timestamp}.log"

echo "Log: $log_file"
echo ""

python3 main_parallel.py -i input_test_cli.xlsx -o output_test_${timestamp}.xlsx -w 1 2>&1 | tee "$log_file"

# Verificar resultado
if [ -f "output_test_${timestamp}.xlsx" ]; then
    row_count=$(python3 << PYEOF
import pandas as pd
try:
    df = pd.read_excel('output_test_${timestamp}.xlsx')
    print(len(df))
except:
    print(0)
PYEOF
)
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "RESULTADO FINAL"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    if [ "$row_count" -gt 0 ]; then
        echo "✅ SUCESSO! Arquivo gerado com $row_count linhas"
        echo ""
        echo "O site está acessível! Você pode:"
        echo "  • Processar lista completa"
        echo "  • Usar 2 workers com segurança"
        echo "  • Aumentar velocidade"
    else
        echo "⚠️  Arquivo vazio ou erro no scraping"
        echo ""
        echo "O site pode ainda estar bloqueando. Verifique o log:"
        echo "  tail -50 $log_file"
    fi
else
    echo "❌ Nenhum arquivo foi gerado"
fi

echo ""
echo "================================================"
echo "TESTE CONCLUÍDO"
echo "================================================"
echo ""
echo "Arquivos gerados:"
echo "  • $log_file"
echo "  • output_test_${timestamp}.xlsx (se criado)"
echo "  • debug_page_*.png (screenshots)"
echo ""






