"""
Test stealth_scraper.py in isolation
"""
import logging
from stealth_scraper import StealthANBIMAScraper

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_stealth_scraper():
    """Test stealth scraper with 1 CNPJ"""
    test_cnpj = '48.330.198/0001-06'
    
    print("\n" + "="*80)
    print("TESTE ISOLADO: Stealth Scraper")
    print("="*80)
    print(f"CNPJ de teste: {test_cnpj}")
    print(f"Modo: NON-HEADLESS (para observar)")
    print()
    
    scraper = None
    
    try:
        # Initialize scraper
        print("1. Inicializando Stealth Scraper...")
        scraper = StealthANBIMAScraper(headless=False)
        
        print("2. Setup do driver...")
        if not scraper.setup_driver():
            print("❌ Falha ao inicializar driver")
            return
        
        print("✓ Driver inicializado com sucesso")
        print()
        
        # Test scraping
        print("3. Iniciando scraping...")
        result = scraper.scrape_fund_data(test_cnpj)
        
        print()
        print("="*80)
        print("RESULTADO")
        print("="*80)
        
        print(f"CNPJ: {result['CNPJ']}")
        print(f"Status: {result['Status']}")
        print(f"Nome do Fundo: {result.get('Nome do Fundo', 'N/A')}")
        print(f"Registros extraídos: {len(result.get('periodic_data', []))}")
        
        if result['Status'] == 'Success':
            print("\n✅ SUCESSO! Stealth scraper funcionou!")
            
            # Show first 3 records
            if result.get('periodic_data'):
                print("\nPrimeiros 3 registros:")
                for i, record in enumerate(result['periodic_data'][:3], 1):
                    print(f"  {i}. {record['Data da cotização']}: {record['Valor cota']}")
        else:
            print(f"\n❌ FALHOU: {result['Status']}")
        
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        if scraper:
            print("\nFechando scraper...")
            scraper.close()
        print("Teste concluído!")

if __name__ == '__main__':
    test_stealth_scraper()






