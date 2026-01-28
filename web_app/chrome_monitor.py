"""
Chrome Process Monitor - Detects and cleans up orphaned Chrome/chromedriver processes
"""
import os
import sys
import platform
import subprocess
import logging
import time
from threading import Thread, Event
from datetime import datetime

logger = logging.getLogger(__name__)


class ChromeMonitor:
    """Monitors and cleans up orphan Chrome/chromedriver processes"""
    
    def __init__(self, check_interval=30):
        """
        Initialize Chrome Monitor
        
        Args:
            check_interval: Seconds between checks (default: 30)
        """
        self.check_interval = check_interval
        self.stop_event = Event()
        self.monitor_thread = None
        self.last_cleanup = None
        self.chrome_logger = logging.getLogger('chrome')
        self._process_name = self._get_process_name()
    
    def _get_process_name(self):
        """Get process name based on platform"""
        if platform.system() == 'Darwin':  # macOS
            return 'Google Chrome'
        elif platform.system() == 'Linux':
            return 'google-chrome'
        else:  # Windows
            return 'chrome.exe'
    
    def scan_orphan_processes(self):
        """
        Scan for orphaned Chrome/chromedriver processes
        
        Returns:
            list: List of orphan process PIDs
        """
        orphans = []
        
        try:
            if platform.system() == 'Darwin' or platform.system() == 'Linux':
                # Find chromedriver processes
                try:
                    result = subprocess.run(
                        ['ps', 'aux'],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    
                    for line in result.stdout.split('\n'):
                        if 'chromedriver' in line.lower() and 'grep' not in line:
                            parts = line.split()
                            if len(parts) >= 2:
                                try:
                                    pid = int(parts[1])
                                    # Check if it's an orphan (no parent Python process)
                                    if self._is_orphan(pid):
                                        orphans.append(('chromedriver', pid))
                                except ValueError:
                                    pass
                    
                    # Find Chrome processes with webdriver flags
                    for line in result.stdout.split('\n'):
                        if self._process_name.lower() in line.lower() and 'grep' not in line:
                            if 'test-type=webdriver' in line or '--remote-debugging-port' in line:
                                parts = line.split()
                                if len(parts) >= 2:
                                    try:
                                        pid = int(parts[1])
                                        if self._is_orphan(pid):
                                            orphans.append(('chrome', pid))
                                    except ValueError:
                                        pass
                except subprocess.CalledProcessError:
                    pass
            else:
                # Windows
                try:
                    # Find chromedriver.exe
                    result = subprocess.run(
                        ['tasklist', '/FI', 'IMAGENAME eq chromedriver.exe', '/FO', 'CSV'],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    # Parse CSV and check for orphans
                    for line in result.stdout.split('\n')[1:]:  # Skip header
                        if line.strip():
                            parts = line.split('","')
                            if len(parts) >= 2:
                                try:
                                    pid = int(parts[1].strip('"'))
                                    if self._is_orphan(pid):
                                        orphans.append(('chromedriver', pid))
                                except ValueError:
                                    pass
                except subprocess.CalledProcessError:
                    pass
        
        except Exception as e:
            logger.error(f"Error scanning orphan processes: {e}")
        
        return orphans
    
    def _is_orphan(self, pid):
        """
        Check if a process is an orphan (has no parent Python process)
        
        Args:
            pid: Process PID
            
        Returns:
            bool: True if orphan
        """
        try:
            if platform.system() == 'Darwin' or platform.system() == 'Linux':
                # Get parent PID
                try:
                    result = subprocess.run(
                        ['ps', '-o', 'ppid=', '-p', str(pid)],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    ppid = int(result.stdout.strip())
                    
                    # Check if parent is a Python process
                    parent_result = subprocess.run(
                        ['ps', '-p', str(ppid), '-o', 'command='],
                        capture_output=True,
                        text=True
                    )
                    parent_cmd = parent_result.stdout.strip().lower()
                    
                    # Orphan if parent is not Python or if parent is init/systemd
                    return 'python' not in parent_cmd or ppid == 1
                except (subprocess.CalledProcessError, ValueError):
                    return True  # Assume orphan if we can't check
            else:
                # Windows - more complex to check
                return True  # For now, be more aggressive on Windows
        
        except Exception:
            return True
    
    def cleanup_orphans(self):
        """
        Clean up orphaned Chrome/chromedriver processes
        
        Returns:
            int: Number of processes cleaned up
        """
        orphans = self.scan_orphan_processes()
        cleaned = 0
        
        for process_type, pid in orphans:
            try:
                if platform.system() == 'Darwin' or platform.system() == 'Linux':
                    os.kill(pid, 9)  # SIGKILL
                else:
                    subprocess.run(['taskkill', '/F', '/PID', str(pid)], 
                                 capture_output=True)
                
                self.chrome_logger.info(f"Cleaned up orphan {process_type} PID: {pid}")
                cleaned += 1
            except (OSError, ProcessLookupError, subprocess.CalledProcessError):
                # Process already gone
                pass
            except Exception as e:
                logger.error(f"Error killing process {pid}: {e}")
        
        if cleaned > 0:
            self.last_cleanup = datetime.utcnow()
            logger.info(f"Cleaned up {cleaned} orphan Chrome processes")
        
        return cleaned
    
    def start_monitor(self):
        """Start background monitoring thread"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            logger.warning("Monitor already running")
            return
        
        self.stop_event.clear()
        self.monitor_thread = Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info(f"Chrome Monitor started (check interval: {self.check_interval}s)")
    
    def stop_monitor(self):
        """Stop background monitoring thread"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.stop_event.set()
            self.monitor_thread.join(timeout=2)
            logger.info("Chrome Monitor stopped")
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while not self.stop_event.is_set():
            try:
                self.cleanup_orphans()
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
            
            # Wait for next check or stop signal
            self.stop_event.wait(self.check_interval)
    
    def get_last_cleanup_time(self):
        """
        Get timestamp of last cleanup
        
        Returns:
            datetime or None: Last cleanup time
        """
        return self.last_cleanup





