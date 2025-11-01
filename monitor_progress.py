#!/usr/bin/env python3
"""
Monitor script to track parallel scraping progress
"""
import time
import os
import re
from datetime import datetime

def monitor_log(log_file, check_interval=300):
    """
    Monitor the scraping log file and report progress
    
    Args:
        log_file: Path to log file
        check_interval: Seconds between checks (default 5 minutes)
    """
    print(f"\n{'='*80}")
    print(f"  MONITORAMENTO INICIADO - {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*80}\n")
    
    last_check_time = time.time()
    last_success_count = 0
    start_time = time.time()
    
    while True:
        if not os.path.exists(log_file):
            print(f"⚠️  Log file not found: {log_file}")
            time.sleep(10)
            continue
        
        # Read log file
        with open(log_file, 'r') as f:
            content = f.read()
        
        # Count successes per worker
        worker1_success = len(re.findall(r'Worker 1: ✓ Successfully scraped', content))
        worker2_success = len(re.findall(r'Worker 2: ✓ Successfully scraped', content))
        worker3_success = len(re.findall(r'Worker 3: ✓ Successfully scraped', content))
        worker4_success = len(re.findall(r'Worker 4: ✓ Successfully scraped', content))
        total_success = worker1_success + worker2_success + worker3_success + worker4_success
        
        # Count failures
        total_failures = len(re.findall(r'Worker \d+:.*Failed to scrape', content))
        
        # Check if completed
        if 'Finished. Success:' in content:
            finished_matches = re.findall(r'Worker (\d+): Finished\. Success: (\d+), Failed: (\d+)', content)
            
            print(f"\n{'='*80}")
            print(f"  🎉 EXECUÇÃO COMPLETADA! - {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*80}\n")
            
            for worker_id, success, failed in finished_matches:
                print(f"  Worker {worker_id}: ✅ {success} sucessos, ❌ {failed} falhas")
            
            elapsed_time = time.time() - start_time
            print(f"\n  ⏱️  Tempo total: {elapsed_time/60:.2f} minutos")
            print(f"  📊 Total processado: {total_success} CNPJs")
            print(f"  🎯 Taxa média: {total_success/(elapsed_time/60):.2f} CNPJs/minuto")
            
            print(f"\n{'='*80}\n")
            break
        
        # Check for crashes
        crash_indicators = [
            'no such window: target window already closed',
            'ChromeDriver exited with status code -9',
            'Can not connect to the Service chromedriver'
        ]
        
        crashed = False
        for indicator in crash_indicators:
            if indicator in content:
                print(f"\n⚠️  CRASH DETECTADO: {indicator}")
                crashed = True
                break
        
        if crashed:
            print(f"\n  Worker 1: {worker1_success} sucessos")
            print(f"  Worker 2: {worker2_success} sucessos")
            print(f"  Worker 3: {worker3_success} sucessos")
            print(f"  Total: {total_success} CNPJs processados antes do crash")
            break
        
        # Periodic update
        current_time = time.time()
        if current_time - last_check_time >= check_interval:
            elapsed = current_time - start_time
            new_successes = total_success - last_success_count
            rate = new_successes / (check_interval / 60) if check_interval > 0 else 0
            
            print(f"\n{'─'*80}")
            print(f"  📊 CHECKPOINT - {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'─'*80}")
            print(f"  ⏱️  Tempo decorrido: {elapsed/60:.1f} minutos")
            print(f"  ✅ Worker 1: {worker1_success} sucessos")
            print(f"  ✅ Worker 2: {worker2_success} sucessos")
            print(f"  ✅ Worker 3: {worker3_success} sucessos")
            print(f"  ✅ Worker 4: {worker4_success} sucessos")
            print(f"  📈 Total: {total_success}/161 CNPJs ({total_success/161*100:.1f}%)")
            print(f"  ❌ Falhas: {total_failures}")
            print(f"  ⚡ Taxa: {rate:.2f} CNPJs/min (últimos 5 min)")
            
            remaining = 161 - total_success
            if rate > 0:
                eta = remaining / rate
                print(f"  🕐 Tempo estimado restante: {eta:.1f} minutos")
            
            print(f"{'─'*80}\n")
            
            last_check_time = current_time
            last_success_count = total_success
        
        time.sleep(30)  # Check every 30 seconds

if __name__ == "__main__":
    import sys
    log_file = sys.argv[1] if len(sys.argv) > 1 else "logs/scraper_parallel_20251024_184810.log"
    monitor_log(log_file, check_interval=300)  # Check every 5 minutes

