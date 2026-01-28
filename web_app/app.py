"""
Flask Web Application for ANBIMA Scraper
Provides UI for uploading CNPJs, monitoring progress, and managing scraping jobs
"""
import os
import sys
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
import pandas as pd
from threading import Thread

# Add parent directory to path to import scraper modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db, ScrapingJob, CNPJ, ScrapedData
from scraper_service import ScraperService
from process_manager import ProcessManager
from chrome_monitor import ChromeMonitor
from recovery_service import RecoveryService
import config
import socket
import os

# Flask app configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = 'anbima-scraper-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///anbima_scraper.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['OUTPUT_FOLDER'] = os.path.join(os.path.dirname(__file__), 'outputs')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Initialize extensions
db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Setup structured logging with file rotation
import logging.handlers
from pathlib import Path

# Create logs directory
logs_dir = Path(__file__).parent / 'logs'
logs_dir.mkdir(exist_ok=True)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# File handler with rotation (10MB per file, keep 5 backups)
file_handler = logging.handlers.RotatingFileHandler(
    logs_dir / 'webapp.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] [%(name)s] PID:%(process)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(file_formatter)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')
console_handler.setFormatter(console_formatter)

# Add handlers
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# Separate logger for Chrome processes
chrome_logger = logging.getLogger('chrome')
chrome_file_handler = logging.handlers.RotatingFileHandler(
    logs_dir / 'chrome.log',
    maxBytes=10*1024*1024,
    backupCount=3,
    encoding='utf-8'
)
chrome_file_handler.setLevel(logging.INFO)
chrome_file_handler.setFormatter(file_formatter)
chrome_logger.addHandler(chrome_file_handler)

logger = logging.getLogger(__name__)

# Initialize database
with app.app_context():
    db.create_all()
    logger.info("Database tables created/verified")

# Initialize services
process_manager = None
chrome_monitor = None
recovery_service = None

def initialize_services():
    """Initialize all background services"""
    global process_manager, chrome_monitor, recovery_service
    
    # Process Manager for single instance
    try:
        process_manager = ProcessManager()
        if not process_manager.acquire_lock():
            logger.error("Another instance of the web app is already running!")
            sys.exit(1)
        logger.info("Process lock acquired")
    except Exception as e:
        logger.error(f"Failed to acquire process lock: {e}")
        sys.exit(1)
    
    # Chrome Monitor for orphan cleanup (disabled for now - too aggressive)
    chrome_monitor = ChromeMonitor(check_interval=300)  # 5 min to be less intrusive
    # chrome_monitor.start_monitor()  # Disabled temporarily
    logger.info("Chrome Monitor initialized (not started)")
    
    # Recovery Service for stuck jobs
    recovery_service = RecoveryService(db, app, check_interval=300)
    recovery_service.start_recovery()
    logger.info("Recovery Service started")

# Services will be initialized in __main__


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    """Get all scraping jobs"""
    jobs = ScrapingJob.query.order_by(ScrapingJob.created_at.desc()).all()
    return jsonify({
        'success': True,
        'jobs': [job.to_dict() for job in jobs]
    })


@app.route('/api/jobs/<int:job_id>', methods=['GET'])
def get_job(job_id):
    """Get specific job with its CNPJs"""
    job = ScrapingJob.query.get_or_404(job_id)
    cnpjs = CNPJ.query.filter_by(job_id=job_id).all()
    
    return jsonify({
        'success': True,
        'job': job.to_dict(),
        'cnpjs': [cnpj.to_dict() for cnpj in cnpjs]
    })


@app.route('/api/jobs/<int:job_id>/failed', methods=['GET'])
def get_failed_cnpjs(job_id):
    """Get failed CNPJs for a job"""
    job = ScrapingJob.query.get_or_404(job_id)
    failed_cnpjs = CNPJ.query.filter_by(
        job_id=job_id
    ).filter(
        CNPJ.status.in_(['failed', 'not_found'])
    ).all()
    
    return jsonify({
        'success': True,
        'job_id': job_id,
        'failed_cnpjs': [cnpj.to_dict() for cnpj in failed_cnpjs]
    })


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload Excel file with CNPJs"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'success': False, 'error': 'File must be Excel (.xlsx or .xls)'}), 400
    
    try:
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Read CNPJs from Excel
        df = pd.read_excel(filepath)
        
        # Auto-detect CNPJ column
        cnpj_column = None
        for col in df.columns:
            if 'cnpj' in str(col).lower() or df[col].astype(str).str.match(r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$').any():
                cnpj_column = col
                break
        
        if cnpj_column is None:
            return jsonify({'success': False, 'error': 'Could not find CNPJ column'}), 400
        
        # Get CNPJs
        cnpjs = df[cnpj_column].dropna().unique().tolist()
        
        if len(cnpjs) == 0:
            return jsonify({'success': False, 'error': 'No valid CNPJs found'}), 400
        
        # Get workers from request
        workers = int(request.form.get('workers', config.DEFAULT_WORKERS))
        workers = min(max(workers, 1), config.MAX_WORKERS)
        
        # Get stealth mode flag (checkboxes send 'on' when checked)
        use_stealth_raw = request.form.get('use_stealth', '')
        use_stealth = use_stealth_raw in ('true', 'on')
        logger.info(f"Upload request - use_stealth flag received: {use_stealth_raw}, parsed as: {use_stealth}")
        
        # Create job in database
        job = ScrapingJob(
            filename=filename,
            total_cnpjs=len(cnpjs),
            workers=workers,
            use_stealth=use_stealth,
            status='pending'
        )
        db.session.add(job)
        db.session.commit()
        
        # Create CNPJ records
        for cnpj in cnpjs:
            cnpj_record = CNPJ(
                job_id=job.id,
                cnpj=str(cnpj),
                status='pending'
            )
            db.session.add(cnpj_record)
        db.session.commit()
        
        logger.info(f"Job {job.id} created with {len(cnpjs)} CNPJs")
        
        return jsonify({
            'success': True,
            'job_id': job.id,
            'total_cnpjs': len(cnpjs),
            'workers': workers
        })
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/jobs/<int:job_id>/start', methods=['POST'])
def start_job(job_id):
    """Start scraping job"""
    job = ScrapingJob.query.get_or_404(job_id)
    
    if job.status == 'running':
        return jsonify({'success': False, 'error': 'Job is already running'}), 400
    
    # Update job status
    job.status = 'running'
    job.started_at = datetime.utcnow()
    db.session.commit()
    
    # Start scraping in background thread
    scraper_service = ScraperService(app, db, socketio)
    thread = Thread(target=scraper_service.run_scraping_job, args=(job_id,))
    thread.daemon = True
    thread.start()
    
    logger.info(f"Started scraping job {job_id}")
    
    return jsonify({'success': True, 'message': 'Job started'})


@app.route('/api/jobs/<int:job_id>/stop', methods=['POST'])
def stop_job(job_id):
    """Stop a running job"""
    job = ScrapingJob.query.get_or_404(job_id)
    
    if job.status != 'running':
        return jsonify({'success': False, 'error': 'Job is not running'}), 400
    
    # Set job status to cancelled
    job.status = 'cancelled'
    job.completed_at = datetime.utcnow()
    db.session.commit()
    
    logger.info(f"Job {job_id} cancelled by user")
    
    return jsonify({
        'success': True,
        'message': 'Job stopped successfully'
    })


@app.route('/api/jobs/<int:job_id>/retry', methods=['POST'])
def retry_failed(job_id):
    """Retry failed CNPJs for a job"""
    job = ScrapingJob.query.get_or_404(job_id)
    
    if job.status == 'running':
        return jsonify({'success': False, 'error': 'Job is currently running'}), 400
    
    # Get failed CNPJs
    failed_cnpjs = CNPJ.query.filter_by(
        job_id=job_id
    ).filter(
        CNPJ.status.in_(['failed'])  # Only retry 'failed', not 'not_found'
    ).all()
    
    if not failed_cnpjs:
        return jsonify({'success': False, 'error': 'No failed CNPJs to retry'}), 400
    
    # Reset failed CNPJs status
    for cnpj in failed_cnpjs:
        cnpj.status = 'pending'
        cnpj.error_message = None
    
    # Update job status
    job.status = 'running'
    job.started_at = datetime.utcnow()
    job.failed_cnpjs = 0
    db.session.commit()
    
    # Start retry in background thread
    scraper_service = ScraperService(app, db, socketio)
    thread = Thread(target=scraper_service.run_scraping_job, args=(job_id,))
    thread.daemon = True
    thread.start()
    
    logger.info(f"Retrying {len(failed_cnpjs)} failed CNPJs for job {job_id}")
    
    return jsonify({
        'success': True,
        'message': f'Retrying {len(failed_cnpjs)} failed CNPJs'
    })


@app.route('/api/jobs/<int:job_id>/download', methods=['GET'])
def download_results(job_id):
    """Download results Excel file"""
    job = ScrapingJob.query.get_or_404(job_id)
    
    if not job.output_file or not os.path.exists(job.output_file):
        return jsonify({'success': False, 'error': 'Output file not found'}), 404
    
    return send_file(
        job.output_file,
        as_attachment=True,
        download_name=f'anbima_results_{job_id}.xlsx'
    )


@app.route('/api/jobs/fix-stuck', methods=['POST'])
def fix_stuck_jobs():
    """Fix jobs that are stuck in 'running' status"""
    try:
        fixed_jobs = []
        
        # Get all running jobs
        running_jobs = ScrapingJob.query.filter_by(status='running').all()
        
        for job in running_jobs:
            # Count CNPJs in each status
            total_cnpjs = CNPJ.query.filter_by(job_id=job.id).count()
            processed_cnpjs = CNPJ.query.filter_by(job_id=job.id).filter(
                CNPJ.status.in_(['success', 'failed', 'not_found'])
            ).count()
            
            # If all CNPJs are processed, mark job as completed
            if total_cnpjs > 0 and processed_cnpjs >= total_cnpjs:
                job.status = 'completed'
                job.completed_at = datetime.utcnow()
                fixed_jobs.append(job.id)
                logger.info(f"Fixed stuck job {job.id} - all CNPJs processed")
            
            # If job started more than 2 hours ago, mark as failed
            elif job.started_at:
                elapsed = datetime.utcnow() - job.started_at
                if elapsed.total_seconds() > 7200:  # 2 hours
                    job.status = 'failed'
                    job.completed_at = datetime.utcnow()
                    fixed_jobs.append(job.id)
                    logger.info(f"Fixed stuck job {job.id} - timed out")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'fixed_jobs': fixed_jobs,
            'message': f'Fixed {len(fixed_jobs)} stuck jobs'
        })
        
    except Exception as e:
        logger.error(f"Error fixing stuck jobs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get overall statistics"""
    total_jobs = ScrapingJob.query.count()
    completed_jobs = ScrapingJob.query.filter_by(status='completed').count()
    running_jobs = ScrapingJob.query.filter_by(status='running').count()
    total_cnpjs_scraped = db.session.query(db.func.sum(ScrapingJob.successful_cnpjs)).scalar() or 0
    
    return jsonify({
        'success': True,
        'stats': {
            'total_jobs': total_jobs,
            'completed_jobs': completed_jobs,
            'running_jobs': running_jobs,
            'total_cnpjs_scraped': total_cnpjs_scraped
        }
    })


@app.route('/api/health', methods=['GET'])
def get_health():
    """Get system health metrics"""
    from datetime import datetime
    import time
    
    uptime = None
    if process_manager and process_manager.lock_data:
        started = datetime.fromisoformat(process_manager.lock_data['started_at'])
        uptime = (datetime.utcnow() - started).total_seconds()
    
    # Get active jobs with PIDs
    running_jobs = ScrapingJob.query.filter_by(status='running').all()
    active_jobs = [
        {'id': job.id, 'pid': job.pid}
        for job in running_jobs
    ]
    
    # Get Chrome process count
    chrome_count = 0
    if chrome_monitor:
        orphans = chrome_monitor.scan_orphan_processes()
        chrome_count = len(orphans)
    
    last_cleanup = None
    if chrome_monitor and chrome_monitor.last_cleanup:
        last_cleanup = chrome_monitor.last_cleanup.isoformat()
    
    return jsonify({
        'success': True,
        'health': {
            'pid': os.getpid(),
            'hostname': socket.gethostname(),
            'uptime_seconds': uptime,
            'active_jobs': active_jobs,
            'chrome_orphans_detected': chrome_count,
            'last_orphan_cleanup': last_cleanup
        }
    })


@app.route('/api/cleanup-chrome', methods=['POST'])
def cleanup_chrome():
    """Manually trigger Chrome cleanup"""
    if not chrome_monitor:
        return jsonify({'success': False, 'error': 'Chrome monitor not initialized'}), 500
    
    cleaned = chrome_monitor.cleanup_orphans()
    return jsonify({
        'success': True,
        'cleaned_processes': cleaned
    })


@app.route('/api/recover', methods=['POST'])
def manual_recovery():
    """Manually trigger recovery service"""
    if not recovery_service:
        return jsonify({'success': False, 'error': 'Recovery service not initialized'}), 500
    
    result = recovery_service.run_manual_recovery()
    return jsonify(result)


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info('Client connected')
    emit('connected', {'message': 'Connected to ANBIMA Scraper'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info('Client disconnected')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # Initialize services
    initialize_services()
    
    # Run with SocketIO
    socketio.run(
        app,
        host='0.0.0.0',
        port=5001,  # Changed from 5000 (macOS AirPlay uses 5000)
        debug=True,
        use_reloader=False,  # Disable reloader to avoid issues with threads
        allow_unsafe_werkzeug=True  # Allow for development
    )

