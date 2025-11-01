#!/usr/bin/env python3
"""
Monitora a execução e executa verificação final automaticamente
"""
import time
import os
import subprocess
import glob

def monitor_execution():
    print("="*80)
    print("  MONITORAMENTO AUTOMÁTICO - 4 WORKERS")
    print("="*80)
    print("\n⏳ Aguardando início da execução...")
    
    # Aguardar log ser criado
    while True:
        log_files = glob.glob("logs/scraper_parallel_*.log")
        if log_files:
            log_file = max(log_files, key=os.path.getmtime)
            # Verificar se o log é recente (últimos 2 minutos)
            if time.time() - os.path.getmtime(log_file) < 120:
                break
        time.sleep(5)
    
    print(f"✅ Execução detectada: {os.path.basename(log_file)}")
    print(f"\n📊 Monitorando progresso...\n")
    
    last_check = time.time()
    check_interval = 120  # 2 minutos
    
    while True:
        with open(log_file, 'r') as f:
            content = f.read()
        
        # Verificar se completou
        if 'PARALLEL MODE Completed Successfully' in content or 'SUMMARY' in content:
            print("\n✅ EXECUÇÃO COMPLETADA!")
            break
        
        # Checkpoint periódico
        if time.time() - last_check >= check_interval:
            import re
            success_count = len(re.findall(r'✓ Successfully scraped', content))
            failed_count = len(re.findall(r'Failed to scrape', content))
            
            print(f"  [{time.strftime('%H:%M:%S')}] Progresso: {success_count} sucessos, {failed_count} falhas")
            last_check = time.time()
        
        time.sleep(10)
    
    # Aguardar um pouco para garantir que tudo foi salvo
    time.sleep(5)
    
    # Executar verificação final
    print("\n" + "="*80)
    print("  EXECUTANDO VERIFICAÇÃO FINAL")
    print("="*80 + "\n")
    
    try:
        subprocess.run([
            "python3", "verify_results.py",
            "input_cnpjs_optimized.xlsx",
            "output_test_4workers_final.xlsx"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro na verificação: {e}")
    except FileNotFoundError:
        print("❌ Script de verificação não encontrado")

if __name__ == "__main__":
    try:
        monitor_execution()
    except KeyboardInterrupt:
        print("\n\n⚠️  Monitoramento interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro no monitoramento: {e}")

