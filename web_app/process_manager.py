"""
Process Manager - Ensures single instance of web application
"""
import os
import sys
import signal
import atexit
import logging
import socket
import json
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class ProcessManager:
    """Manages process lock to ensure single instance of web app"""
    
    def __init__(self, pid_file=None):
        """
        Initialize Process Manager
        
        Args:
            pid_file: Path to PID file (default: instance/.webapp.pid)
        """
        if pid_file is None:
            # Get instance directory
            instance_dir = Path(__file__).parent.parent / 'web_app' / 'instance'
            instance_dir.mkdir(parents=True, exist_ok=True)
            pid_file = instance_dir / '.webapp.pid'
        
        self.pid_file = Path(pid_file)
        self.lock_data = None
        
    def acquire_lock(self):
        """
        Acquire process lock by creating PID file
        
        Returns:
            bool: True if lock acquired, False if another instance is running
            
        Raises:
            RuntimeError: If unable to create PID file
        """
        try:
            # Check if already running
            if self.check_running():
                logger.warning("Another instance is already running")
                return False
            
            # Clean up stale lock
            self.cleanup_stale_lock()
            
            # Get current PID and hostname
            current_pid = os.getpid()
            hostname = socket.gethostname()
            port = self._get_free_port()
            
            # Create lock data
            self.lock_data = {
                'pid': current_pid,
                'hostname': hostname,
                'port': port,
                'started_at': datetime.utcnow().isoformat()
            }
            
            # Write PID file
            with open(self.pid_file, 'w') as f:
                json.dump(self.lock_data, f, indent=2)
            
            logger.info(f"Process lock acquired: PID={current_pid}, hostname={hostname}, port={port}")
            
            # Register cleanup handlers
            atexit.register(self.release_lock)
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to acquire lock: {e}")
            raise RuntimeError(f"Cannot create PID file: {e}")
    
    def release_lock(self):
        """Release process lock by removing PID file"""
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
                logger.info("Process lock released")
        except Exception as e:
            logger.error(f"Failed to release lock: {e}")
    
    def check_running(self):
        """
        Check if another instance is running
        
        Returns:
            bool: True if another instance exists and is running
        """
        if not self.pid_file.exists():
            return False
        
        try:
            # Read PID file
            with open(self.pid_file, 'r') as f:
                data = json.load(f)
            
            pid = data.get('pid')
            if not pid:
                return False
            
            # Check if process exists
            try:
                # On Unix systems, signal 0 doesn't send anything but raises OSError if process doesn't exist
                os.kill(pid, 0)
                return True
            except (OSError, ProcessLookupError):
                # Process doesn't exist
                logger.warning(f"Stale PID file found: process {pid} no longer exists")
                return False
                
        except Exception as e:
            logger.error(f"Error checking running instance: {e}")
            return False
    
    def cleanup_stale_lock(self):
        """Remove PID file if process doesn't exist"""
        if not self.pid_file.exists():
            return
        
        try:
            if not self.check_running():
                self.pid_file.unlink()
                logger.info("Removed stale PID file")
        except Exception as e:
            logger.error(f"Error cleaning up stale lock: {e}")
    
    def _get_free_port(self):
        """
        Get a free port for the application
        
        Returns:
            int: Port number
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', 0))
                return s.getsockname()[1]
        except Exception as e:
            logger.error(f"Failed to get free port: {e}")
            return 5001  # Default port
    
    def _signal_handler(self, signum, frame):
        """Handle termination signals"""
        logger.info(f"Received signal {signum}, releasing lock and exiting")
        self.release_lock()
        sys.exit(0)





