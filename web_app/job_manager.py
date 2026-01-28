"""
Job Process Manager - Manages scraping jobs using multiprocessing
"""
import os
import sys
import logging
import multiprocessing
from multiprocessing import Process, Event
from datetime import datetime
import socket

logger = logging.getLogger(__name__)


def run_job_process(job_id, db_uri, secret_key):
    """
    Worker function to run scraping job in separate process
    
    Args:
        job_id: Job ID to run
        db_uri: Database URI
        secret_key: Flask secret key
    """
    # Import inside function to avoid circular imports
    from app import app, db
    from scraper_service import ScraperService
    
    # Configure app for this process
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SECRET_KEY'] = secret_key
    
    # Re-initialize database for this process
    db.init_app(app)
    
    # Run the job
    scraper_service = ScraperService(app, db, None)  # No socketio in subprocess
    scraper_service.run_scraping_job(job_id)


class JobProcessManager:
    """Manages active scraping job processes"""
    
    def __init__(self):
        # Use Manager for shared dict across processes
        self._manager = multiprocessing.Manager()
        self._active_processes = self._manager.dict()
        self._pid_map = self._manager.dict()  # job_id -> process PID
        self._lock = multiprocessing.Lock()
    
    def start_job(self, job_id, db_uri, secret_key):
        """
        Start a scraping job in a new process
        
        Args:
            job_id: Job ID to start
            db_uri: Database URI
            secret_key: Flask secret key
            
        Returns:
            bool: True if job started successfully
        """
        with self._lock:
            if job_id in self._active_processes:
                logger.warning(f"Job {job_id} is already running")
                return False
            
            # Create and start process
            process = Process(
                target=run_job_process,
                args=(job_id, db_uri, secret_key),
                daemon=False  # Not daemon so parent waits for it
            )
            process.start()
            
            # Track process
            self._active_processes[job_id] = process
            self._pid_map[job_id] = process.pid
            
            logger.info(f"Started job {job_id} in process PID {process.pid}")
            return True
    
    def stop_job(self, job_id):
        """
        Stop a running job process
        
        Args:
            job_id: Job ID to stop
            
        Returns:
            bool: True if job was stopped
        """
        with self._lock:
            if job_id not in self._active_processes:
                logger.warning(f"Job {job_id} is not running")
                return False
            
            process = self._active_processes[job_id]
            
            # Terminate process
            if process.is_alive():
                logger.info(f"Terminating process {process.pid} for job {job_id}")
                process.terminate()
                process.join(timeout=5)  # Wait 5 seconds for graceful exit
                
                if process.is_alive():
                    # Force kill if still alive
                    logger.warning(f"Force killing process {process.pid} for job {job_id}")
                    process.kill()
                    process.join()
            
            # Remove from tracking
            del self._active_processes[job_id]
            if job_id in self._pid_map:
                del self._pid_map[job_id]
            
            logger.info(f"Stopped job {job_id}")
            return True
    
    def get_active_processes(self):
        """
        Get all active job processes
        
        Returns:
            dict: {job_id: process} of active jobs
        """
        with self._lock:
            return dict(self._active_processes)
    
    def cleanup_finished(self):
        """
        Remove finished processes from tracking
        
        Returns:
            list: Job IDs that were cleaned up
        """
        with self._lock:
            finished_jobs = []
            for job_id, process in list(self._active_processes.items()):
                if not process.is_alive():
                    logger.debug(f"Cleaning up finished process for job {job_id}")
                    del self._active_processes[job_id]
                    if job_id in self._pid_map:
                        del self._pid_map[job_id]
                    finished_jobs.append(job_id)
            return finished_jobs
    
    def get_job_pid(self, job_id):
        """
        Get PID of process running a job
        
        Args:
            job_id: Job ID
            
        Returns:
            int or None: Process PID if running
        """
        with self._lock:
            return self._pid_map.get(job_id)
    
    def is_job_running(self, job_id):
        """
        Check if a job is currently running
        
        Args:
            job_id: Job ID
            
        Returns:
            bool: True if job is running
        """
        with self._lock:
            if job_id not in self._active_processes:
                return False
            process = self._active_processes[job_id]
            return process.is_alive()





