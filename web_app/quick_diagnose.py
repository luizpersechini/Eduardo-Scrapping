"""Quick diagnosis of web app scraping"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import ScrapingJob, CNPJ, ScrapedData
from scraper_service import ScraperService
from socketio import Server

def test_single_cnpj():
    """Test scraping 1 CNPJ directly"""
    with app.app_context():
        # Create mock job and CNPJ
        job = ScrapingJob(
            filename='test.xlsx',
            total_cnpjs=1,
            workers=1,
            status='running'
        )
        db.session.add(job)
        db.session.commit()
        
        cnpj_record = CNPJ(
            job_id=job.id,
            cnpj='48.330.198/0001-06',
            status='pending'
        )
        db.session.add(cnpj_record)
        db.session.commit()
        
        print(f"\n{'='*80}")
        print(f"QUICK DIAGNOSIS - WEB APP SCRAPING")
        print(f"{'='*80}\n")
        print(f"Created Job #{job.id} with CNPJ #{cnpj_record.id}")
        
        # Create scraper service
        sio = Server(async_mode='threading')
        service = ScraperService(app, db, sio)
        
        # Scrape
        print("\nStarting scrape...")
        print("-" * 80)
        result = service.scrape_single_cnpj(job.id, cnpj_record.id, cnpj_record.cnpj)
        print("-" * 80)
        
        print(f"\nResult:")
        print(f"  Success: {result.get('success')}")
        print(f"  Status: {result.get('status')}")
        print(f"  Data count: {len(result.get('data', []))}")
        print(f"  Fund name: {result.get('fund_name')}")
        
        if result.get('data'):
            print(f"\n  First data item: {result.get('data')[0]}")
        
        # Process result
        print("\nProcessing result...")
        print("-" * 80)
        service.process_scraping_result(job.id, result)
        print("-" * 80)
        
        # Check database (refresh to get latest data from DB)
        db.session.expire_all()  # Force refresh from database
        cnpj_record = CNPJ.query.get(cnpj_record.id)
        data_count = ScrapedData.query.filter_by(cnpj_id=cnpj_record.id).count()
        
        print(f"\nDatabase after processing:")
        print(f"  CNPJ status: {cnpj_record.status}")
        print(f"  CNPJ data_count: {cnpj_record.data_count}")
        print(f"  ScrapedData records: {data_count}")
        
        print(f"\n{'='*80}")
        if cnpj_record.status == 'success' and data_count == 0:
            print("⚠️  PROBLEM: Marked success but no data saved!")
            print("="*80 + "\n")
        elif cnpj_record.status == 'success' and data_count > 0:
            print("✓ SUCCESS: Data saved correctly!")
            print("="*80 + "\n")
        else:
            print(f"✗ FAILED: Status is {cnpj_record.status}")
            print("="*80 + "\n")

if __name__ == '__main__':
    test_single_cnpj()

