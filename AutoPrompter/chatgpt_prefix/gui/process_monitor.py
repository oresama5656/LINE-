#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Process Monitor - Clean Version
Manages subprocess execution of CLI with NDJSON monitoring
"""

import subprocess
import threading
import json
import sys
import os
from typing import Optional, Callable, Dict, Any
import queue
from pathlib import Path


class ProcessMonitor:
    """Subprocess CLI monitor class"""
    
    def __init__(self, working_dir: str = None):
        self.working_dir = working_dir or os.getcwd()
        self.process: Optional[subprocess.Popen] = None
        self.monitor_thread: Optional[threading.Thread] = None
        self.is_running = False
        self.stop_requested = False
        
        # Event queue for thread communication
        self.event_queue = queue.Queue()
        
        # Settings for event processing
        self.current_settings: Dict[str, Any] = {}
        
        # Callback functions
        self.on_event_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_finished_callback: Optional[Callable[[int, Dict[str, int]], None]] = None
        
    def set_callbacks(self, on_event: Callable, on_finished: Callable):
        """Set callback functions"""
        self.on_event_callback = on_event
        self.on_finished_callback = on_finished
    
    def start_process(self, settings: Dict[str, Any]) -> bool:
        """Start CLI process"""
        if self.is_running:
            return False
        
        # Store current settings for event processing
        self.current_settings = settings.copy()
        
        try:
            # Build CLI command
            cmd = self._build_command(settings)
            
            # Debug: Log the command being executed
            if self.on_event_callback:
                self.on_event_callback({
                    "type": "raw_output",
                    "message": f"Executing command: {' '.join(cmd)}",
                    "level": "debug"
                })
            
            # Start subprocess with unbuffered output
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'  # Force Python to be unbuffered
            
            self.process = subprocess.Popen(
                cmd,
                cwd=self.working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,  # Unbuffered
                universal_newlines=True,
                env=env
            )
            
            self.is_running = True
            self.stop_requested = False
            
            # Start monitor thread
            self.monitor_thread = threading.Thread(target=self._monitor_process, daemon=True)
            self.monitor_thread.start()
            
            return True
            
        except Exception as e:
            if self.on_event_callback:
                self.on_event_callback({
                    "type": "error",
                    "error": f"Failed to start process: {e}",
                    "step": "process_start"
                })
            return False
    
    def stop_process(self):
        """Stop process"""
        self.stop_requested = True
        
        if self.process and self.process.poll() is None:
            try:
                # Use terminate() on Windows
                if sys.platform == "win32":
                    self.process.terminate()
                else:
                    # Send SIGINT on Unix systems
                    self.process.send_signal(subprocess.signal.SIGINT)
                
                # Wait 3 seconds then force kill
                try:
                    self.process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    
            except Exception as e:
                if self.on_event_callback:
                    self.on_event_callback({
                        "type": "error",
                        "error": f"Failed to stop process: {e}",
                        "step": "process_stop"
                    })
    
    def _build_command(self, settings: Dict[str, Any]) -> list:
        """Build CLI execution command"""
        cmd = [sys.executable, "-m", "chatgpt_prefix.chatgpt_cli"]

        # Required arguments
        cmd.extend(["--csv", settings['csv']])
        cmd.extend(["--ndjson"])  # NDJSON output mode

        # Optional arguments
        if settings.get('wait'):
            cmd.extend(["--wait", str(settings['wait'])])

        if settings.get('dry_run'):
            cmd.append("--dry-run")

        if settings.get('interactive'):
            cmd.append("--interactive")

        if settings.get('max_items'):
            cmd.extend(["--max-items", str(settings['max_items'])])

        if settings.get('retry'):
            cmd.extend(["--retry", str(settings['retry'])])

        # Prefix/Suffix arguments
        if settings.get('prefix'):
            cmd.extend(["--prefix", settings['prefix']])

        if settings.get('suffix'):
            cmd.extend(["--suffix", settings['suffix']])

        # 操作速度設定
        if settings.get('short_sleep'):
            cmd.extend(["--short-sleep", str(settings['short_sleep'])])

        if settings.get('long_sleep'):
            cmd.extend(["--long-sleep", str(settings['long_sleep'])])

        # CSV/GUIモード切り替え
        if settings.get('use_csv_mode'):
            cmd.append("--csv-mode")

        return cmd
    
    def _process_line(self, line: str, final_result: dict):
        """Process a single NDJSON line"""
        try:
            # Parse NDJSON
            event = json.loads(line)
            
            # Save final result
            if event.get("type") == "result":
                final_result.update({
                    "total": event.get("total", 0),
                    "sent": event.get("sent", 0),
                    "failed": event.get("failed", 0)
                })
            
            # Add settings context to event
            event['_settings'] = self.current_settings
            
            # Event callback - call immediately for real-time processing
            if self.on_event_callback:
                self.on_event_callback(event)
                
        except json.JSONDecodeError as e:
            # Non-JSON output (error messages etc.)
            if self.on_event_callback:
                self.on_event_callback({
                    "type": "raw_output",
                    "message": line,
                    "level": "info"
                })
    
    def _monitor_process(self):
        """Process monitor thread"""
        final_result = {"total": 0, "sent": 0, "failed": 0}
        
        try:
            # Read stdout in real-time with immediate processing
            while self.process and self.process.poll() is None:
                if self.stop_requested:
                    break
                
                # Simple approach: always try to read with immediate processing
                import time
                
                try:
                    line = self.process.stdout.readline()
                    if line:
                        line = line.strip()
                        if line:
                            self._process_line(line, final_result)
                    else:
                        # Small delay if no data to avoid busy waiting
                        time.sleep(0.01)
                except Exception as e:
                    # Handle any read errors gracefully
                    time.sleep(0.01)
            
            # Wait for process to finish
            if self.process:
                exit_code = self.process.wait()
            else:
                exit_code = -1
            
            # Read stderr if available
            if self.process and self.process.stderr:
                stderr_output = self.process.stderr.read()
                if stderr_output:
                    if self.on_event_callback:
                        self.on_event_callback({
                            "type": "error",
                            "error": stderr_output,
                            "step": "stderr"
                        })
            
        except Exception as e:
            exit_code = -1
            if self.on_event_callback:
                self.on_event_callback({
                    "type": "error",
                    "error": f"Monitor thread error: {e}",
                    "step": "monitor"
                })
        
        finally:
            self.is_running = False
            
            # Finished callback
            if self.on_finished_callback:
                self.on_finished_callback(exit_code, final_result)
    
    def is_process_running(self) -> bool:
        """Check if process is running"""
        return self.is_running and self.process and self.process.poll() is None
    
    def cleanup(self):
        """Resource cleanup"""
        if self.is_running:
            self.stop_process()
        
        # Wait for thread to finish
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        
        self.process = None
        self.monitor_thread = None
        self.is_running = False