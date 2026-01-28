"""
Scraper Service - Integrates ANBIMA scraper with web application
"""
import os
import sys
import time
import logging
import subprocess
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import pandas as pd

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from anbima_scraper import ANBIMAScraper
from data_processor import DataProcessor
from models import ScrapingJob, CNPJ, ScrapedData
import config

logger = logging.getLogger(__name__)


def clean_currency_value(value_str: str) -> float:
    """
    Clean currency string and convert to float
    
    Examples:
        "R$ 1,234567" -> 1.234567
        "R$ 1.234,56" -> 1234.56
        "1,23" -> 1.23
        "1.23" -> 1.23
    
    Args:
        value_str: Currency string to clean
        
    Returns:
        Float value
        
    Raises:
        ValueError: If value cannot be converted
    """
    if not value_str:
        raise ValueError("Empty value")
    
    # Remove currency symbol and spaces
    cleaned = value_str.replace('R$', '').replace(' ', '').strip()
    
    # Check if has both . and ,
    if '.' in cleaned and ',' in cleaned:
        # Format: 1.234,56 (BR format with thousands separator)
        cleaned = cleaned.replace('.', '').replace(',', '.')
    elif ',' in cleaned:
        # Format: 1,23 (decimal comma only)
        cleaned = cleaned.replace(',', '.')
    # else: Format is already 1.23 or 1234.56 (decimal point)
    
    return float(cleaned)


class ScraperService:
    """Service to run scraping jobs and emit real-time updates"""
    
    def __init__(self, app, db, socketio):
        self.app = app
        self.db = db
        self.socketio = socketio
        self.lock = Lock()
    
    def run_scraping_job(self, job_id):
        """Run a complete scraping job"""
        with self.app.app_context():
            try:
                logger.info(f"Starting scraping job {job_id}")
                
                # Get job
                job = ScrapingJob.query.get(job_id)
                if not job:
                    logger.error(f"Job {job_id} not found")
                    return
                
                # Get pending CNPJs
                cnpjs_to_scrape = CNPJ.query.filter_by(
                    job_id=job_id,
                    status='pending'
                ).all()
                
                if not cnpjs_to_scrape:
                    logger.warning(f"No pending CNPJs for job {job_id}")
                    job.status = 'completed'
                    job.completed_at = datetime.utcnow()
                    self.db.session.commit()
                    return
                
                # Emit job started
                self.emit_job_update(job_id, {
                    'status': 'running',
                    'message': f'Starting scraping with {job.workers} workers...',
                    'progress': 0
                })
                
                # Pre-initialize ChromeDriver
                self.emit_job_update(job_id, {
                    'message': 'Pre-initializing ChromeDriver...',
                    'phase': 'initialization'
                })
                
                if not self.preinitialize_chromedriver(job.use_stealth):
                    job.status = 'failed'
                    job.completed_at = datetime.utcnow()
                    self.db.session.commit()
                    self.emit_job_update(job_id, {
                        'status': 'failed',
                        'message': 'Failed to initialize ChromeDriver'
                    })
                    return
                
                # Test workers
                self.emit_job_update(job_id, {
                    'message': f'Testing {job.workers} workers...',
                    'phase': 'worker_testing'
                })
                
                if not self.test_workers(job.workers, job.use_stealth):
                    job.status = 'failed'
                    job.completed_at = datetime.utcnow()
                    self.db.session.commit()
                    self.emit_job_update(job_id, {
                        'status': 'failed',
                        'message': 'Worker initialization failed'
                    })
                    return
                
                # Start scraping
                self.emit_job_update(job_id, {
                    'message': 'All workers ready! Starting scraping...',
                    'phase': 'scraping'
                })
                
                start_time = time.time()
                
                # Use ThreadPoolExecutor for parallel scraping
                with ThreadPoolExecutor(max_workers=job.workers) as executor:
                    futures = {}
                    
                    for cnpj_record in cnpjs_to_scrape:
                        # Check if job was cancelled
                        job = ScrapingJob.query.get(job_id)
                        if job.status == 'cancelled':
                            logger.info(f"Job {job_id} was cancelled, stopping submission of new tasks")
                            break
                            
                        future = executor.submit(
                            self.scrape_single_cnpj,
                            job_id,
                            cnpj_record.id,
                            cnpj_record.cnpj
                        )
                        futures[future] = cnpj_record.cnpj
                    
                    # Process results as they complete
                    for future in as_completed(futures):
                        # Check if job was cancelled
                        job = ScrapingJob.query.get(job_id)
                        if job.status == 'cancelled':
                            logger.info(f"Job {job_id} was cancelled, stopping processing")
                            # Kill any remaining Chrome processes
                            self._kill_chrome_processes()
                            break
                            
                        cnpj = futures[future]
                        try:
                            result = future.result()
                            self.process_scraping_result(job_id, result)
                        except Exception as e:
                            logger.error(f"Error processing result for {cnpj}: {e}")
                
                # Calculate execution time
                execution_time = time.time() - start_time
                
                # Check if job was cancelled
                job = ScrapingJob.query.get(job_id)
                if job.status == 'cancelled':
                    logger.info(f"Job {job_id} was cancelled")
                    # Kill any remaining Chrome processes
                    self._kill_chrome_processes()
                    self.emit_job_update(job_id, {
                        'status': 'cancelled',
                        'message': 'Job cancelled by user',
                        'phase': 'cancelled'
                    })
                    return
                
                # Generate output file
                self.emit_job_update(job_id, {
                    'message': 'Generating output file...',
                    'phase': 'finalizing'
                })
                
                output_file = self.generate_output_file(job_id)
                
                # Update job status
                job = ScrapingJob.query.get(job_id)
                job.status = 'completed'
                job.completed_at = datetime.utcnow()
                job.output_file = output_file
                self.db.session.commit()
                
                # Emit completion
                self.emit_job_update(job_id, {
                    'status': 'completed',
                    'message': f'Job completed in {execution_time/60:.1f} minutes!',
                    'progress': 100,
                    'output_file': output_file
                })
                
                logger.info(f"Job {job_id} completed successfully")
                
            except Exception as e:
                logger.error(f"Error in scraping job {job_id}: {e}", exc_info=True)
                
                # Update job status to failed
                job = ScrapingJob.query.get(job_id)
                if job:
                    job.status = 'failed'
                    job.completed_at = datetime.utcnow()
                    self.db.session.commit()
                
                self.emit_job_update(job_id, {
                    'status': 'failed',
                    'message': f'Job failed: {str(e)}'
                })
    
    def preinitialize_chromedriver(self, use_stealth=False):
        """Pre-initialize ChromeDriver to avoid race condition"""
        try:
            if hasattr(config, 'USE_PARSE_BOT') and config.USE_PARSE_BOT:
                from parse_bot_scraper import ParseBotScraper
                scraper = ParseBotScraper(headless=False)
            elif use_stealth:
                from stealth_scraper import StealthANBIMAScraper
                scraper = StealthANBIMAScraper(headless=False)
            else:
                scraper = ANBIMAScraper(headless=False)
            
            if scraper.setup_driver():
                scraper.close()
                return True
            return False
        except Exception as e:
            logger.error(f"ChromeDriver pre-initialization failed: {e}")
            return False
    
    def test_workers(self, num_workers, use_stealth=False):
        """Test if all workers can initialize"""
        try:
            scrapers = []
            for i in range(num_workers):
                if hasattr(config, 'USE_PARSE_BOT') and config.USE_PARSE_BOT:
                    from parse_bot_scraper import ParseBotScraper
                    scraper = ParseBotScraper(headless=False)
                elif use_stealth:
                    from stealth_scraper import StealthANBIMAScraper
                    scraper = StealthANBIMAScraper(headless=False)
                else:
                    scraper = ANBIMAScraper(headless=False)
                
                if scraper.setup_driver():
                    scrapers.append(scraper)
                    time.sleep(0.5)
                else:
                    # Cleanup
                    for s in scrapers:
                        s.close()
                    return False
            
            # Cleanup
            for scraper in scrapers:
                scraper.close()
            
            time.sleep(2)
            return True
            
        except Exception as e:
            logger.error(f"Worker testing failed: {e}")
            return False
    
    def scrape_single_cnpj(self, job_id, cnpj_id, cnpj):
        """Scrape a single CNPJ with retry and driver restart"""
        logger.info(f"===== SCRAPE_SINGLE_CNPJ CALLED: {cnpj} =====")
        with self.app.app_context():
            scraper = None
            max_retries = 2
            
            # Get job to check stealth mode
            job = ScrapingJob.query.get(job_id)
            use_stealth = job.use_stealth if job else False
            
            try:
                # Update status to processing
                cnpj_record = CNPJ.query.get(cnpj_id)
                cnpj_record.status = 'processing'
                self.db.session.commit()
                
                # Emit update with detail
                self.emit_cnpj_update(job_id, cnpj, 'processing', 'Iniciando scraping...')
                
                # Try up to max_retries times with driver restart
                for attempt in range(max_retries):
                    # Check if job was cancelled
                    job = ScrapingJob.query.get(job_id)
                    if job and job.status == 'cancelled':
                        logger.info(f"Job {job_id} was cancelled during scraping of {cnpj}")
                        return {
                            'cnpj_id': cnpj_id,
                            'cnpj': cnpj,
                            'success': False,
                            'status': 'cancelled',
                            'error': 'Job cancelled'
                        }
                    
                    scraper = None
                    
                    try:
                        # Emit: Initializing driver
                        self.emit_cnpj_update(job_id, cnpj, 'processing', '🔧 Inicializando navegador...')
                        
                        # Setup scraper (fresh driver each attempt)
                        if hasattr(config, 'USE_PARSE_BOT') and config.USE_PARSE_BOT:
                            from parse_bot_scraper import ParseBotScraper
                            scraper = ParseBotScraper(headless=False)
                        elif use_stealth:
                            from stealth_scraper import StealthANBIMAScraper
                            scraper = StealthANBIMAScraper(headless=False)
                        else:
                            scraper = ANBIMAScraper(headless=False)
                        
                        if not scraper.setup_driver():
                            raise Exception("Failed to setup driver")
                        
                        # Add delay before scraping (especially on retry)
                        if attempt > 0:
                            time.sleep(3)
                            logger.info(f"Retry {attempt + 1}/{max_retries} for {cnpj}")
                            self.emit_cnpj_update(job_id, cnpj, 'processing', f'🔄 Tentativa {attempt + 1}/{max_retries}...')
                        
                        # Emit: Navigating
                        self.emit_cnpj_update(job_id, cnpj, 'processing', '🌐 Navegando para ANBIMA...')
                        
                        # Scrape
                        logger.info(f"===== CALLING scraper.scrape_fund_data for {cnpj} =====")
                        result = scraper.scrape_fund_data(cnpj)
                        logger.info(f"===== RESULT FROM scraper.scrape_fund_data: {result} =====")
                        
                        # Emit: Extracting data
                        self.emit_cnpj_update(job_id, cnpj, 'processing', '📊 Extraindo dados...')
                        
                        # Close scraper
                        scraper.close()
                        scraper = None
                        
                        # Map the result to our expected format
                        status_map = {
                            'Success': 'success',
                            'Not found': 'not_found',
                            'Timeout': 'failed'
                        }
                        
                        result_status = result.get('Status', 'failed')
                        logger.info(f"===== MAPPING RESULT =====")
                        logger.info(f"  Raw Status: {result_status}")
                        logger.info(f"  Keys in result: {list(result.keys())}")
                        logger.info(f"  periodic_data key exists: {'periodic_data' in result}")
                        logger.info(f"  periodic_data length: {len(result.get('periodic_data', []))}")
                        logger.info(f"  Nome do Fundo: {result.get('Nome do Fundo')}")
                        
                        is_success = result_status == 'Success'
                        mapped_status = status_map.get(result_status, 'failed')
                        
                        logger.info(f"  is_success: {is_success}")
                        logger.info(f"  mapped_status: {mapped_status}")
                        
                        # If success or not found, return immediately (no retry needed)
                        if is_success or 'Not found' in result_status:
                            return {
                                'cnpj_id': cnpj_id,
                                'cnpj': cnpj,
                                'success': is_success,
                                'status': mapped_status,
                                'data': result.get('periodic_data', []),
                                'fund_name': result.get('Nome do Fundo'),
                                'error': result_status if not is_success else None
                            }
                        
                        # If timeout/error and not last attempt, continue to retry
                        if attempt < max_retries - 1:
                            logger.warning(f"Attempt {attempt + 1} failed for {cnpj}: {result_status}. Retrying...")
                            time.sleep(2)  # Wait before retry
                            continue
                        else:
                            # Last attempt failed
                            return {
                                'cnpj_id': cnpj_id,
                                'cnpj': cnpj,
                                'success': False,
                                'status': mapped_status,
                                'data': [],
                                'fund_name': None,
                                'error': result_status
                            }
                    
                    except Exception as e:
                        logger.error(f"Error on attempt {attempt + 1} for {cnpj}: {e}")
                        if scraper:
                            try:
                                scraper.close()
                            except:
                                pass
                            scraper = None
                        
                        # If not last attempt, retry
                        if attempt < max_retries - 1:
                            time.sleep(2)
                            continue
                        else:
                            # Last attempt failed with exception
                            return {
                                'cnpj_id': cnpj_id,
                                'cnpj': cnpj,
                                'success': False,
                                'status': 'failed',
                                'error': str(e)
                            }
                
            except Exception as e:
                logger.error(f"Fatal error scraping {cnpj}: {e}")
                return {
                    'cnpj_id': cnpj_id,
                    'cnpj': cnpj,
                    'success': False,
                    'status': 'failed',
                    'error': str(e)
                }
    
    def process_scraping_result(self, job_id, result):
        """Process the result of a single CNPJ scraping"""
        logger.info(f"===== PROCESS_SCRAPING_RESULT CALLED =====")
        logger.info(f"  Job ID: {job_id}")
        logger.info(f"  CNPJ: {result.get('cnpj')}")
        logger.info(f"  Success: {result.get('success')}")
        logger.info(f"  Data count: {len(result.get('data', []))}")
        
        with self.app.app_context():
            try:
                cnpj_record = CNPJ.query.get(result['cnpj_id'])
                logger.info(f"  Found CNPJ record: {cnpj_record.cnpj}")
                
                if result['success']:
                    # Update CNPJ record
                    logger.info(f"  Setting CNPJ status to 'success'")
                    cnpj_record.status = 'success'
                    cnpj_record.fund_name = result.get('fund_name')
                    cnpj_record.scraped_at = datetime.utcnow()
                    logger.info(f"  CNPJ record after update: status={cnpj_record.status}, data_count will be={len(result.get('data', []))}")
                    
                    # Save scraped data
                    saved_count = 0
                    for item in result.get('data', []):
                        try:
                            data_record = ScrapedData(
                                cnpj_id=cnpj_record.id,
                                cnpj=result['cnpj'],
                                fund_name=result.get('fund_name'),
                                date=datetime.strptime(item['Data da cotização'], '%d/%m/%Y').date(),
                                value=clean_currency_value(item['Valor cota'])
                            )
                            self.db.session.add(data_record)
                            saved_count += 1
                        except Exception as e:
                            logger.error(f"Error parsing data item for {result['cnpj']}: {item} - Error: {e}")
                            continue  # Skip invalid rows but continue processing
                    
                    # Update data_count with actual saved count
                    cnpj_record.data_count = saved_count
                    logger.info(f"Saved {saved_count} records for {result['cnpj']}")
                    
                    # Update job success count
                    job = ScrapingJob.query.get(job_id)
                    job.successful_cnpjs += 1
                    
                else:
                    # Update CNPJ record as failed
                    cnpj_record.status = result['status']  # 'failed' or 'not_found'
                    cnpj_record.error_message = result.get('error')
                    cnpj_record.retry_count += 1
                    
                    # Update job failed count
                    job = ScrapingJob.query.get(job_id)
                    job.failed_cnpjs += 1
                
                logger.info(f"  About to commit: cnpj_record.status={cnpj_record.status}, data_count={cnpj_record.data_count}")
                self.db.session.commit()
                logger.info(f"  Commit successful!")
                
                # Emit update
                self.emit_cnpj_update(job_id, result['cnpj'], cnpj_record.status)
                
                # Emit progress update
                job = ScrapingJob.query.get(job_id)
                progress = round((job.successful_cnpjs + job.failed_cnpjs) / job.total_cnpjs * 100, 1)
                self.emit_job_update(job_id, {
                    'progress': progress,
                    'successful': job.successful_cnpjs,
                    'failed': job.failed_cnpjs,
                    'message': f'Processed {job.successful_cnpjs + job.failed_cnpjs}/{job.total_cnpjs} CNPJs'
                })
                
            except Exception as e:
                logger.error(f"Error processing result: {e}", exc_info=True)
    
    def generate_output_file(self, job_id):
        """Generate Excel output file with results"""
        with self.app.app_context():
            try:
                # Get all scraped data for this job
                cnpjs = CNPJ.query.filter_by(job_id=job_id).all()
                cnpj_ids = [c.id for c in cnpjs]
                
                scraped_data = ScrapedData.query.filter(
                    ScrapedData.cnpj_id.in_(cnpj_ids)
                ).all()
                
                if not scraped_data:
                    logger.warning(f"No data to export for job {job_id}")
                    return None
                
                # Create DataFrame
                data_list = []
                for data in scraped_data:
                    data_list.append({
                        'CNPJ': data.cnpj,
                        'Nome do Fundo': data.fund_name,
                        'Data': data.date,
                        'Valor': data.value
                    })
                
                df = pd.DataFrame(data_list)
                
                # Create pivot table
                pivot = df.pivot_table(
                    index='Data',
                    columns='CNPJ',
                    values='Valor',
                    aggfunc='first'
                )
                
                # Sort by date descending
                pivot = pivot.sort_index(ascending=False)
                
                # Save to Excel
                output_filename = f'anbima_results_job_{job_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
                output_path = os.path.join(
                    self.app.config['OUTPUT_FOLDER'],
                    output_filename
                )
                
                pivot.to_excel(output_path)
                
                logger.info(f"Output file generated: {output_path}")
                return output_path
                
            except Exception as e:
                logger.error(f"Error generating output file: {e}", exc_info=True)
                return None
    
    def emit_job_update(self, job_id, data):
        """Emit job update via SocketIO"""
        try:
            data['job_id'] = job_id
            data['timestamp'] = datetime.utcnow().isoformat()
            self.socketio.emit('job_update', data)
        except Exception as e:
            logger.error(f"Error emitting job update: {e}")
    
    def emit_cnpj_update(self, job_id, cnpj, status, detail=None):
        """Emit CNPJ update via SocketIO"""
        try:
            data = {
                'job_id': job_id,
                'cnpj': cnpj,
                'status': status,
                'timestamp': datetime.utcnow().isoformat()
            }
            if detail:
                data['detail'] = detail
            self.socketio.emit('cnpj_update', data)
        except Exception as e:
            logger.error(f"Error emitting CNPJ update: {e}")
    
    def _kill_chrome_processes(self):
        """Kill all Chrome and chromedriver processes"""
        try:
            import platform
            if platform.system() == 'Darwin':  # macOS
                subprocess.run(['pkill', '-9', 'chromedriver'], capture_output=True)
                subprocess.run(['pkill', '-9', 'Google Chrome'], capture_output=True)
            elif platform.system() == 'Linux':
                subprocess.run(['pkill', '-9', 'chromedriver'], capture_output=True)
                subprocess.run(['pkill', '-9', 'chromium-browser'], capture_output=True)
                subprocess.run(['pkill', '-9', 'google-chrome'], capture_output=True)
            else:  # Windows
                subprocess.run(['taskkill', '/F', '/IM', 'chromedriver.exe'], capture_output=True)
                subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], capture_output=True)
            logger.info("Killed all Chrome processes")
        except Exception as e:
            logger.error(f"Error killing Chrome processes: {e}")

``