"""
Recovery Service - Detects and recovers from stuck jobs and orphaned processes
"""
import logging
import time
from datetime import datetime, timedelta
from threading import Thread, Event

logger = logging.getLogger(__name__)


class RecoveryService:
    """Monitors and recovers from stuck jobs and system issues"""
    
    def __init__(self, db, app, check_interval=300):
        """
        Initialize Recovery Service
        
        Args:
            db: SQLAlchemy database instance
            app: Flask app instance for context
            check_interval: Seconds between checks (default: 300 = 5 min)
        """
        self.db = db
        self.app = app
        self.check_interval = check_interval
        self.stop_event = Event()
        self.recovery_thread = None
    
    def check_stuck_jobs(self):
        """
        Check for stuck jobs and recover them
        
        Returns:
            int: Number of jobs recovered
        """
        recovered = 0
        
        try:
            from models import ScrapingJob, CNPJ
            
            # Get all running jobs
            running_jobs = ScrapingJob.query.filter_by(status='running').all()
            
            for job in running_jobs:
                try:
                    # Check 1: Job with all CNPJs processed
                    total_cnpjs = CNPJ.query.filter_by(job_id=job.id).count()
                    processed_cnpjs = CNPJ.query.filter_by(job_id=job.id).filter(
                        CNPJ.status.in_(['success', 'failed', 'not_found', 'cancelled'])
                    ).count()
                    
                    if total_cnpjs > 0 and processed_cnpjs >= total_cnpjs:
                        # All CNPJs are done, mark job as completed
                        job.status = 'completed'
                        job.completed_at = datetime.utcnow()
                        logger.info(f"Recovered stuck job {job.id}: All CNPJs processed")
                        recovered += 1
                        continue
                    
                    # Check 2: Job exceeded timeout
                    if job.started_at:
                        elapsed = datetime.utcnow() - job.started_at
                        if elapsed.total_seconds() > job.timeout_seconds:
                            job.status = 'failed'
                            job.completed_at = datetime.utcnow()
                            logger.info(f"Recovered stuck job {job.id}: Timeout exceeded ({elapsed.total_seconds():.0f}s > {job.timeout_seconds}s)")
                            recovered += 1
                            continue
                    
                    # Check 3: Job with PID that no longer exists
                    if job.pid:
                        if not self._is_process_running(job.pid):
                            job.status = 'failed'
                            job.completed_at = datetime.utcnow()
                            logger.info(f"Recovered stuck job {job.id}: Process PID {job.pid} no longer exists")
                            recovered += 1
                            continue
                
                except Exception as e:
                    logger.error(f"Error checking job {job.id}: {e}")
                    continue
            
            # Commit all changes
            if recovered > 0:
                self.db.session.commit()
                logger.info(f"Recovery service recovered {recovered} stuck jobs")
        
        except Exception as e:
            logger.error(f"Error in recovery check: {e}")
            self.db.session.rollback()
        
        return recovered
    
    def _is_process_running(self, pid):
        """
        Check if a process is running
        
        Args:
            pid: Process ID
            
        Returns:
            bool: True if process exists and is running
        """
        import os
        import platform
        
        try:
            if platform.system() == 'Windows':
                # Check on Windows
                import subprocess
                result = subprocess.run(
                    ['tasklist', '/FI', f'PID eq {pid}'],
                    capture_output=True,
                    text=True
                )
                return str(pid) in result.stdout
            else:
                # Check on Unix-like systems
                os.kill(pid, 0)  # Doesn't kill, just checks existence
                return True
        except (OSError, ProcessLookupError, subprocess.CalledProcessError):
            return False
    
    def start_recovery(self):
        """Start background recovery thread"""
        if self.recovery_thread and self.recovery_thread.is_alive():
            logger.warning("Recovery service already running")
            return
        
        self.stop_event.clear()
        self.recovery_thread = Thread(target=self._recovery_loop, daemon=True)
        self.recovery_thread.start()
        logger.info(f"Recovery Service started (check interval: {self.check_interval}s)")
    
    def stop_recovery(self):
        """Stop background recovery thread"""
        if self.recovery_thread and self.recovery_thread.is_alive():
            self.stop_event.set()
            self.recovery_thread.join(timeout=2)
            logger.info("Recovery Service stopped")
    
    def _recovery_loop(self):
        """Background recovery loop"""
        while not self.stop_event.is_set():
            try:
                with self.app.app_context():
                    self.check_stuck_jobs()
            except Exception as e:
                logger.error(f"Error in recovery loop: {e}")
            
            # Wait for next check or stop signal
            self.stop_event.wait(self.check_interval)
    
    def run_manual_recovery(self):
        """
        Run recovery check manually (from API)
        
        Returns:
            dict: Recovery results
        """
        try:
            recovered = self.check_stuck_jobs()
            return {
                'success': True,
                'recovered_jobs': recovered
            }
        except Exception as e:
            logger.error(f"Error in manual recovery: {e}")
            return {
                'success': False,
                'error': str(e)
            }

