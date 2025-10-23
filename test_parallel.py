"""
Test script for parallel scraping
Tests with a small set of CNPJs to validate functionality
"""

import time
from main_parallel import main_parallel
from main import main

# Test CNPJs (use the 2 that were working)
TEST_CNPJS = [
    "48.330.198/0001-06",
    "34.780.531/0001-66"
]

def create_test_input():
    """Create a test input file"""
    import pandas as pd
    df = pd.DataFrame({"CNPJ": TEST_CNPJS})
    df.to_excel("input_test.xlsx", index=False)
    print("✓ Created test input file with 2 CNPJs")

def test_sequential():
    """Test sequential (original) mode"""
    print("\n" + "="*80)
    print("TESTING SEQUENTIAL MODE (Original)")
    print("="*80)
    
    start = time.time()
    success = main(
        input_file="input_test.xlsx",
        output_file="output_test_sequential.xlsx",
        headless=True
    )
    elapsed = time.time() - start
    
    print(f"\n✓ Sequential mode completed in {elapsed:.2f} seconds")
    return success, elapsed

def test_parallel():
    """Test parallel mode"""
    print("\n" + "="*80)
    print("TESTING PARALLEL MODE (2 Workers)")
    print("="*80)
    
    start = time.time()
    success = main_parallel(
        input_file="input_test.xlsx",
        output_file="output_test_parallel.xlsx",
        headless=True,
        num_workers=2,  # Use 2 workers for 2 CNPJs
        skip_processed=False
    )
    elapsed = time.time() - start
    
    print(f"\n✓ Parallel mode completed in {elapsed:.2f} seconds")
    return success, elapsed

def compare_results():
    """Compare results between sequential and parallel modes"""
    import pandas as pd
    
    print("\n" + "="*80)
    print("COMPARING RESULTS")
    print("="*80)
    
    try:
        df_seq = pd.read_excel("output_test_sequential.xlsx")
        df_par = pd.read_excel("output_test_parallel.xlsx")
        
        print(f"Sequential output shape: {df_seq.shape}")
        print(f"Parallel output shape: {df_par.shape}")
        
        if df_seq.shape == df_par.shape:
            print("✓ Output shapes match!")
        else:
            print("⚠️  Output shapes differ!")
        
    except Exception as e:
        print(f"❌ Error comparing results: {e}")

if __name__ == "__main__":
    print("="*80)
    print("PARALLEL SCRAPING TEST")
    print("="*80)
    
    # Create test input
    create_test_input()
    
    # Test sequential mode
    seq_success, seq_time = test_sequential()
    
    # Test parallel mode
    par_success, par_time = test_parallel()
    
    # Compare results
    compare_results()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Sequential: {'✓ Success' if seq_success else '❌ Failed'} - {seq_time:.2f}s")
    print(f"Parallel:   {'✓ Success' if par_success else '❌ Failed'} - {par_time:.2f}s")
    
    if seq_success and par_success and seq_time > 0:
        speedup = seq_time / par_time
        print(f"\nSpeedup: {speedup:.2f}x faster")
        print(f"Time saved: {seq_time - par_time:.2f} seconds")
    
    print("="*80)

