#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sora GUI Launcher - Phase 3B GUI v0
Main entry point for the GUI application
"""

import tkinter as tk
import sys
import os
import signal
from pathlib import Path

# Add chatgpt module path
sys.path.insert(0, str(Path(__file__).parent.parent))

from .gui.main_window import ChatGPTGUIWindow
from .gui.process_monitor import ProcessMonitor  
from .gui.event_handler import EventHandler


class SoraGUIApplication:
    """Main GUI Application"""
    
    def __init__(self):
        self.root = tk.Tk()
        
        # Components
        self.gui_window = ChatGPTGUIWindow(self.root)
        self.process_monitor = ProcessMonitor()
        self.event_handler = EventHandler(self.gui_window)
        
        # Setup
        self.setup_callbacks()
        self.setup_cleanup()
        self.set_defaults()
    
    def setup_callbacks(self):
        """Setup callback functions"""
        self.gui_window.set_callbacks(
            on_start=self.on_start,
            on_stop=self.on_stop
        )
        
        self.process_monitor.set_callbacks(
            on_event=self.event_handler.handle_event,
            on_finished=self.on_finished
        )
    
    def setup_cleanup(self):
        """Setup cleanup handlers"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        if hasattr(signal, 'SIGINT'):
            signal.signal(signal.SIGINT, self.signal_handler)
    
    def set_defaults(self):
        """Set default values"""
        current_dir = Path.cwd()
        csv_files = list(current_dir.glob("*.csv"))
        
        if csv_files:
            self.gui_window.csv_var.set(str(csv_files[0]))
        
        # dry_run is now set as default in main_window.py
    
    def on_start(self, settings: dict):
        """Start process callback"""
        self.gui_window.add_log("Starting ChatGPT CLI process...", "info")
        self.gui_window.add_log(f"Settings: dry_run={settings.get('dry_run', False)}, csv={settings.get('csv', 'none')}", "debug")
        
        success = self.process_monitor.start_process(settings)
        if not success:
            self.gui_window.add_log("Failed to start process", "error")
            self.gui_window.on_stop()
    
    def on_stop(self):
        """Stop process callback"""
        self.gui_window.add_log("Stopping process...", "warning")
        self.process_monitor.stop_process()
    
    def on_finished(self, exit_code: int, result: dict):
        """Process finished callback"""
        total = result.get("total", 0)
        sent = result.get("sent", 0)
        failed = result.get("failed", 0)
        
        self.gui_window.on_process_finished(exit_code, total, sent, failed)
        
        if exit_code == 0:
            self.gui_window.add_log(f"Completed successfully (exit: {exit_code})", "success")
        else:
            self.gui_window.add_log(f"Process failed (exit: {exit_code})", "error")
    
    def signal_handler(self, signum, frame):
        """Signal handler"""
        print(f"\\nShutting down gracefully...")
        self.cleanup()
        sys.exit(0)
    
    def on_closing(self):
        """Window closing handler"""
        self.cleanup()
        self.root.destroy()
    
    def cleanup(self):
        """Resource cleanup"""
        if self.process_monitor:
            self.process_monitor.cleanup()
    
    def run(self):
        """Run application"""
        try:
            self.gui_window.add_log("ChatGPT GUI Auto v0.1.0 - Ready", "success")
            self.gui_window.add_log("Select CSV file and click Start", "info")
            
            self.root.mainloop()
        except Exception as e:
            print(f"GUI Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()


def main():
    """Main function"""
    try:
        app = SoraGUIApplication()
        app.run()
    except Exception as e:
        print(f"Failed to start GUI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()