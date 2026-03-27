#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Event Handler - Clean Version
Processes NDJSON events and updates GUI accordingly
"""

from typing import Dict, Any, Optional
import tkinter as tk
from .main_window import ChatGPTGUIWindow


class EventHandler:
    """NDJSON event processing class"""
    
    def __init__(self, gui_window: ChatGPTGUIWindow):
        self.gui = gui_window
        self.current_total = 0
        self.current_index = 0
        self.is_interactive = False
        self.is_dry_run = False
        
        # Phase name mappings
        self.phase_names = {
            "coordinate_setup": "Coordinate Setup",
            "window_search": "Window Search", 
            "processing_prep": "Processing Prep",
            "processing": "Prompt Processing",
            "generation_wait": "Generation Wait",
            "final_wait": "Final Wait"
        }
        
        # Step name mappings
        self.step_names = {
            "start": "Start",
            "activate": "Activate",
            "click": "Click",
            "copy": "Copy",
            "paste": "Paste", 
            "send": "Send",
            "simulate": "Simulate"
        }
    
    def handle_event(self, event: Dict[str, Any]):
        """Main event dispatcher"""
        event_type = event.get("type")
        
        # Update settings from event context
        if '_settings' in event:
            settings = event['_settings']
            self.is_interactive = settings.get('interactive', False)
            self.is_dry_run = settings.get('dry_run', False)
        
        # Event type handling
        if event_type == "loaded":
            self._handle_loaded(event)
        elif event_type == "phase":
            self._handle_phase(event)
        elif event_type == "window_found":
            self._handle_window_found(event)
        elif event_type == "coordinate":
            self._handle_coordinate(event)
        elif event_type == "countdown":
            self._handle_countdown(event)
        elif event_type == "progress":
            self._handle_progress(event)
        elif event_type == "retry":
            self._handle_retry(event)
        elif event_type == "wait":
            self._handle_wait(event)
        elif event_type == "csv_updated":
            self._handle_csv_updated(event)
        elif event_type == "result":
            self._handle_result(event)
        elif event_type == "error":
            self._handle_error(event)
        elif event_type == "raw_output":
            self._handle_raw_output(event)
        else:
            # Unknown event type
            self.gui.add_log(f"Unknown event: {event}", "debug")
    
    def _handle_loaded(self, event: Dict[str, Any]):
        """Prompt loading completed"""
        total = event.get("total", 0)
        csv_path = event.get("csv_path", "unknown")
        dry_run = event.get("dry_run", False)
        max_items = event.get("max_items")
        
        self.current_total = total
        
        if self.is_interactive:
            self.gui.add_log(f"📊 プロンプト読み込み完了: {total}個", "info")
            self.gui.add_log(f"📄 CSVファイル: {csv_path}", "info")
            if dry_run:
                self.gui.add_log("🔍 [DRY-RUN MODE] シミュレーション実行", "warning")
            if max_items:
                self.gui.add_log(f"📋 処理制限: {max_items}件まで", "info")
        else:
            message = f"Loaded {total} prompts from {csv_path}"
            if dry_run:
                message += " [DRY-RUN MODE]"
            if max_items:
                message += f" (limited to {max_items} items)"
            self.gui.add_log(message, "info")
        
        self.gui.update_status(f"Loaded {total} prompts")
    
    def _handle_phase(self, event: Dict[str, Any]):
        """Phase change"""
        phase = event.get("name", "unknown")
        phase_name = self.phase_names.get(phase, phase)
        
        # Interactive mode shows more detailed phase information
        if self.is_interactive:
            self.gui.add_log("", "info")  # Empty line for spacing
            self.gui.add_log(f"{'='*50}", "info")
            self.gui.add_log(f"フェーズ: {phase_name}", "info")
            self.gui.add_log(f"{'='*50}", "info")
        else:
            self.gui.add_log("", "info")  # Empty line for spacing
            self.gui.add_log(f"Phase: {phase_name}", "info")
        
        self.gui.update_status(f"Phase: {phase_name}")
    
    def _handle_window_found(self, event: Dict[str, Any]):
        """Window found"""
        title = event.get("title", "unknown")
        dry_run = event.get("dry_run", False)
        
        if self.is_interactive:
            if dry_run:
                self.gui.add_log(f"🔍 [DRY-RUN] シミュレーション ウィンドウ: {title}", "success")
            else:
                self.gui.add_log(f"🖥️ Soraウィンドウを発見: {title}", "success")
        else:
            message = f"Found window: {title}"
            if dry_run:
                message = f"[DRY-RUN] Simulated window: {title}"
            self.gui.add_log(message, "success")
    
    def _handle_coordinate(self, event: Dict[str, Any]):
        """Coordinate setup"""
        x = event.get("x", 0)
        y = event.get("y", 0)
        dry_run = event.get("dry_run", False)
        window_title = event.get("window_title", "Unknown")
        window_handle = event.get("window_handle", "Unknown")

        if self.is_interactive:
            if dry_run:
                self.gui.add_log(f"🔍 [DRY-RUN] シミュレーション座標: ({x}, {y})", "info")
            else:
                self.gui.add_log(f"✅ 座標記録完了: ({x}, {y})", "info")
                self.gui.add_log(f"🎯 ターゲットウィンドウ: '{window_title}'", "success")
                self.gui.add_log(f"📝 この座標とウィンドウを使用します", "info")
        else:
            message = f"Coordinate set: ({x}, {y})"
            if dry_run:
                message = f"[DRY-RUN] Simulated coordinate: ({x}, {y})"
            else:
                message = f"Coordinate set: ({x}, {y}), Target window: '{window_title}'"
            self.gui.add_log(message, "info")
    
    def _handle_countdown(self, event: Dict[str, Any]):
        """Countdown"""
        seconds_left = event.get("seconds_left", 0)
        phase = event.get("phase", "")
        message = event.get("message", "")
        
        phase_name = self.phase_names.get(phase, phase)
        status = f"{phase_name}: {seconds_left}s - {message}"
        
        # Update status
        self.gui.update_status(status)
        
        # Add countdown to log
        if self.is_interactive:
            # Interactive mode: detailed guidance
            if phase == "coordinate_setup" and seconds_left == 5:
                self.gui.add_log("📍 Soraの入力欄にマウスカーソルを置いてください", "info")
                self.gui.add_log("⏰ 5秒後に自動で座標を記録します", "info")
                self.gui.add_log("🚨 緊急停止: マウスを画面左上角に移動", "warning")
            elif phase == "processing_prep" and seconds_left == 5:
                self.gui.add_log("🚀 準備完了！", "info")
                self.gui.add_log("📊 処理対象: プロンプト", "info")
                self.gui.add_log("⏰ 5秒後に自動処理を開始します...", "info")
                self.gui.add_log("🚨 緊急停止: Ctrl+C または マウスを左上角に移動", "warning")

            self.gui.add_log(f"⏳ {seconds_left}秒...", "info")
        else:
            # Non-interactive mode: simple countdown
            if seconds_left <= 5:
                log_message = f"準備中... ({message}) - {seconds_left}秒"
                self.gui.add_log(log_message, "info")
    
    def _handle_progress(self, event: Dict[str, Any]):
        """Progress update"""
        step = event.get("step", "")
        index = event.get("index", 0)
        total = event.get("total", 0)
        prompt = event.get("prompt", "")
        dry_run = event.get("dry_run", False)
        
        self.current_index = index
        if total > 0:
            self.current_total = total
        
        # Update progress bar
        self.gui.update_progress(index, total)
        
        # Create log message
        step_name = self.step_names.get(step, step)
        
        if self.is_interactive:
            # Interactive mode: detailed step-by-step logging like CLI
            if step == "start":
                self.gui.add_log("", "info")  # Empty line for spacing
                if dry_run:
                    self.gui.add_log(f"--- 🔍 [DRY-RUN] Processing prompt {index}/{total} ---", "debug")
                else:
                    self.gui.add_log(f"--- 📝 Processing prompt {index}/{total} ---", "info")
                self.gui.add_log(f"📄 Prompt: {prompt}", "info")
            elif step == "activate":
                self.gui.add_log("🎯 Soraウィンドウをアクティブ化", "info")
            elif step == "click":
                x = event.get('x', 0)
                y = event.get('y', 0)
                self.gui.add_log(f"🖱️ 入力エリアをクリック: ({x}, {y})", "info")
            elif step == "copy":
                self.gui.add_log("📋 クリップボードにコピー", "info")
            elif step == "paste":
                self.gui.add_log("📝 プロンプトを貼り付け", "info")
            elif step == "send":
                self.gui.add_log("🚀 プロンプトを送信", "info")
            elif step == "simulate":
                self.gui.add_log(f"🔍 [DRY-RUN] [{index}/{total}] プロンプト処理をシミュレーション", "debug")
        else:
            # Non-interactive mode: simple logging
            if step == "start":
                message = f"[{index}/{total}] Starting: {prompt}"
                if dry_run:
                    message = f"[DRY-RUN] [{index}/{total}] Starting: {prompt}"
            elif step == "simulate":
                message = f"[DRY-RUN] [{index}/{total}] Simulating prompt processing"
            else:
                message = f"[{index}/{total}] {step_name}"
            
            tag = "info" if not dry_run else "debug"
            self.gui.add_log(message, tag)
        
        # 進行中のステータスではスキップボタンを無効化
        self.gui.skip_btn.configure(state="disabled")
    
    def _handle_retry(self, event: Dict[str, Any]):
        """Retry information"""
        attempt = event.get("attempt", 0)
        max_retry = event.get("max_retry", 0)
        index = event.get("index", 0)
        total = event.get("total", 0)
        
        message = f"[{index}/{total}] Retry {attempt}/{max_retry}"
        self.gui.add_log(message, "warning")
    
    def _handle_wait(self, event: Dict[str, Any]):
        """Waiting"""
        seconds_left = event.get("seconds_left", 0)
        minutes = event.get("minutes", 0)
        seconds = event.get("seconds", 0)
        next_index = event.get("next_index")
        total = event.get("total", 0)
        final = event.get("final", False)
        
        if final:
            status = f"Final wait: {minutes}m {seconds}s remaining"
            log_message = f"⏱️ 最終生成完了まで待機中: {minutes:02d}:{seconds:02d}"
        else:
            status = f"Wait for generation [{next_index}/{total}]: {minutes}m {seconds}s remaining"
            log_message = f"⏱️ 残り時間: {minutes:02d}:{seconds:02d} | 次: {next_index}/{total}"
        
        # Update status
        self.gui.update_status(status)
        
        # Add wait info to log (show every 10 seconds to avoid spam)
        if seconds % 10 == 0 or seconds <= 5:
            self.gui.add_log(log_message, "info")
            
        # 待機中のみスキップボタンを有効化
        self.gui.skip_btn.configure(state="normal")
    
    def _handle_csv_updated(self, event: Dict[str, Any]):
        """CSV updated"""
        removed = event.get("removed", "")
        old_count = event.get("old_count", 0)
        new_count = event.get("new_count", 0)
        
        message = f"CSV updated: {old_count} -> {new_count} rows (removed: {removed})"
        self.gui.add_log(message, "info")
    
    def _handle_result(self, event: Dict[str, Any]):
        """Final result"""
        total = event.get("total", 0)
        sent = event.get("sent", 0)
        failed = event.get("failed", 0)
        
        if self.is_interactive:
            # Interactive mode: detailed completion report like CLI
            self.gui.add_log("", "info")  # Empty line for spacing
            self.gui.add_log(f"{'='*50}", "info")
            self.gui.add_log("🎉 処理完了!", "success")
            self.gui.add_log(f"{'='*50}", "info")
            self.gui.add_log(f"📊 処理対象: {total}個", "info")
            self.gui.add_log(f"✅ 成功: {sent}個", "success")
            self.gui.add_log(f"❌ 失敗: {failed}個", "error" if failed > 0 else "info")
            
            if total > 0:
                success_rate = (sent / total) * 100
                self.gui.add_log(f"📈 成功率: {success_rate:.1f}%", "info")
            
            self.gui.add_log(f"{'='*50}", "info")
        else:
            # Non-interactive mode: simple result
            self.gui.add_log("", "info")  # Empty line for spacing
            if failed == 0:
                tag = "success"
                message = f"All completed successfully: {sent}/{total} sent"
            elif sent > 0:
                tag = "warning" 
                message = f"Partially completed: {sent}/{total} sent, {failed} failed"
            else:
                tag = "error"
                message = f"All failed: {sent}/{total} sent, {failed} failed"
            
            self.gui.add_log(message, tag)
        
        # 終了時はスキップボタンを無効化
        self.gui.skip_btn.configure(state="disabled")
        
        # Set progress bar to 100%
        self.gui.update_progress(total, total)
    
    def _handle_error(self, event: Dict[str, Any]):
        """Error handling"""
        error = event.get("error", "Unknown error")
        error_type = event.get("error_type", "")
        step = event.get("step", "unknown")
        index = event.get("index")
        total = event.get("total")
        attempts = event.get("attempts")
        max_retry = event.get("max_retry")

        # Build error message
        if index and total:
            message = f"[{index}/{total}] Error in {step}: {error}"
            if attempts and max_retry:
                message += f" (attempt {attempts}/{max_retry + 1})"
        else:
            message = f"Error in {step}: {error}"

        self.gui.add_log(message, "error")

        # エラー時はスキップボタンを無効化
        self.gui.skip_btn.configure(state="disabled")

        # 特殊文字エラーの場合は追加の説明を表示
        if "UnicodeEncodeError" in error_type or "UnicodeEncodeError" in str(error) or "特殊文字" in str(error):
            self.gui.add_log("⚠️  CSVファイル内にcp932でエンコードできない特殊文字（é、à、ñなど）が含まれています", "warning")
            self.gui.add_log("💡 解決方法: CSVファイル内の特殊文字を通常のASCII文字に変更してください", "info")
            detail = event.get("detail", "")
            if detail:
                self.gui.add_log(f"   {detail}", "info")
    
    def _handle_raw_output(self, event: Dict[str, Any]):
        """Raw output handling"""
        message = event.get("message", "")
        level = event.get("level", "info")
        
        if message:
            # Select tag based on level
            tag_mapping = {
                "info": "info",
                "warning": "warning", 
                "error": "error",
                "debug": "debug"
            }
            tag = tag_mapping.get(level, "info")
            
            self.gui.add_log(f"Raw: {message}", tag)