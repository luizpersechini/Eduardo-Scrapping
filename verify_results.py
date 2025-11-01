#!/usr/bin/env python3
"""
Script de verificação final dos resultados do scraping
Verifica se todos os CNPJs foram processados e analisa os erros
"""
import pandas as pd
import os
import sys

def verify_results(input_file, output_file, log_file):
    """
    Verifica se todos os CNPJs foram processados corretamente
    
    Args:
        input_file: Arquivo de input com CNPJs
        output_file: Arquivo de output gerado
        log_file: Arquivo de log da execução
    """
    print("="*80)
    print("           VERIFICAÇÃO FINAL DOS RESULTADOS")
    print("="*80)
    
    # 1. Ler CNPJs do input
    print("\n📋 1. VERIFICANDO INPUT...")
    df_input = pd.read_excel(input_file)
    input_cnpjs = df_input['CNPJ'].astype(str).tolist()
    print(f"   Total de CNPJs no input: {len(input_cnpjs)}")
    
    # 2. Ler CNPJs do output
    print("\n📊 2. VERIFICANDO OUTPUT...")
    df_output = pd.read_excel(output_file, header=[0, 1])
    # Remove header duplicado se existir
    if df_output.iloc[0, 0] == 'Data da cotização':
        df_output = df_output.iloc[1:].reset_index(drop=True)
    
    output_cnpjs = []
    for col in df_output.columns[1:]:
        if len(col) == 2:
            cnpj, _ = col
            output_cnpjs.append(cnpj)
    
    print(f"   Total de CNPJs no output: {len(output_cnpjs)}")
    
    # 3. Analisar log para erros
    print("\n📄 3. ANALISANDO LOG...")
    with open(log_file, 'r') as f:
        log_content = f.read()
    
    # Extrair erros do log
    import re
    errors = {}
    failed_cnpjs = {}
    
    for line in log_content.split('\n'):
        if 'Failed to scrape' in line or 'WARNING' in line:
            # Extrair CNPJ e motivo do erro
            cnpj_match = re.search(r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', line)
            if cnpj_match:
                cnpj = cnpj_match.group(1)
                
                # Categorizar erro
                if 'not found' in line.lower() or 'no results' in line.lower():
                    error_type = 'CNPJ não encontrado na base ANBIMA'
                elif 'timeout' in line.lower():
                    error_type = 'Timeout (site ANBIMA lento)'
                elif 'no such window' in line.lower():
                    error_type = 'Browser crashou'
                elif 'Error processing table' in line:
                    error_type = 'Erro ao processar tabela'
                else:
                    error_type = 'Erro desconhecido'
                
                failed_cnpjs[cnpj] = error_type
                errors[error_type] = errors.get(error_type, 0) + 1
    
    print(f"   Total de erros detectados: {len(failed_cnpjs)}")
    
    # 4. Comparar input vs output
    print("\n🔍 4. COMPARANDO INPUT vs OUTPUT...")
    input_set = set(input_cnpjs)
    output_set = set(output_cnpjs)
    
    missing_cnpjs = input_set - output_set
    
    print(f"   CNPJs esperados: {len(input_set)}")
    print(f"   CNPJs obtidos: {len(output_set)}")
    print(f"   CNPJs faltando: {len(missing_cnpjs)}")
    
    # 5. Relatório final
    print("\n" + "="*80)
    print("           📊 RELATÓRIO FINAL")
    print("="*80)
    
    success_rate = (len(output_set) / len(input_set)) * 100
    print(f"\n✅ TAXA DE SUCESSO: {success_rate:.1f}% ({len(output_set)}/{len(input_set)})")
    
    if errors:
        print(f"\n❌ TIPOS DE ERROS ENCONTRADOS:")
        for error_type, count in sorted(errors.items(), key=lambda x: x[1], reverse=True):
            print(f"   • {error_type}: {count}")
    
    if missing_cnpjs:
        print(f"\n⚠️  CNPJs FALTANDO ({len(missing_cnpjs)}):")
        for i, cnpj in enumerate(sorted(missing_cnpjs), 1):
            error_reason = failed_cnpjs.get(cnpj, 'Motivo desconhecido')
            print(f"   {i:2d}. {cnpj} - {error_reason}")
    
    # 6. Análise de dados do output
    print(f"\n📈 ANÁLISE DOS DADOS EXTRAÍDOS:")
    total_values = 0
    funds_with_data = 0
    
    for col in df_output.columns[1:]:
        values = df_output[col].astype(str).str.replace('R$ ', '').str.replace(',', '.')
        values = pd.to_numeric(values, errors='coerce').dropna()
        if len(values) > 0:
            funds_with_data += 1
            total_values += len(values)
    
    if funds_with_data > 0:
        print(f"   Fundos com dados: {funds_with_data}/{len(output_set)}")
        print(f"   Total de valores de cotas: {total_values:,}")
        print(f"   Média por fundo: {total_values/funds_with_data:.1f} datas")
    
    # 7. Resumo dos workers
    print(f"\n👥 RESUMO DOS WORKERS:")
    for i in range(1, 5):
        worker_success = len(re.findall(rf'Worker {i}: ✓ Successfully scraped', log_content))
        worker_failed = len(re.findall(rf'Worker {i}:.*Failed to scrape', log_content))
        total = worker_success + worker_failed
        if total > 0:
            rate = (worker_success / total) * 100
            print(f"   Worker {i}: {worker_success}/{total} ({rate:.1f}% sucesso)")
    
    # 8. Status final
    print("\n" + "="*80)
    if len(missing_cnpjs) == 0:
        print("           🎉 SUCESSO TOTAL - TODOS OS CNPJs PROCESSADOS!")
    elif success_rate >= 99:
        print("           ✅ EXCELENTE - Taxa de sucesso acima de 99%")
    elif success_rate >= 95:
        print("           ✅ MUITO BOM - Taxa de sucesso acima de 95%")
    else:
        print("           ⚠️  ATENÇÃO - Taxa de sucesso abaixo de 95%")
    print("="*80 + "\n")
    
    return len(missing_cnpjs) == 0

if __name__ == "__main__":
    # Usar argumentos ou valores padrão
    input_file = sys.argv[1] if len(sys.argv) > 1 else "input_cnpjs_optimized.xlsx"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "output_test_4workers_final.xlsx"
    
    # Encontrar o log mais recente
    import glob
    log_files = glob.glob("logs/scraper_parallel_*.log")
    if log_files:
        log_file = max(log_files, key=os.path.getmtime)
    else:
        log_file = "logs/scraper_parallel.log"
    
    if os.path.exists(output_file):
        verify_results(input_file, output_file, log_file)
    else:
        print(f"❌ Arquivo de output não encontrado: {output_file}")
        sys.exit(1)

