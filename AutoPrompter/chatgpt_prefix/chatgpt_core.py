#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sora GUI自動操作 - コア処理 (イベント駆動版)

UIとコア機能を完全分離、イベント駆動アーキテクチャで実装
print文は一切含まず、全ての進捗情報はイベントで通知
"""

import csv
import pyautogui
import pyperclip
import time
import os
import win32gui
import win32con
from pathlib import Path
from typing import Generator, Dict, Any, Optional, List, Tuple
import threading
import logging


# カスタム例外
class InputError(Exception):
    """入力エラー（CSV不存在、形式不正等）"""
    pass


class RunError(Exception):
    """実行エラー（GUI操作失敗等）"""
    pass


class ChatGPTCore:
    """ChatGPT GUI操作のコア機能（イベント駆動版）"""

    # ========================================
    # スリープ時間設定（PCの速度に応じて調整可能）
    # ========================================

    # 短スリープ - キーボード・マウス操作後の待機時間
    # 使用箇所: ウィンドウ切り替え後, クリック後, Ctrl+A後, コピー後, Enter後
    # 高速PC: 0.2 / 中速PC: 0.3 / 低速PC: 0.5
    SHORT_SLEEP = 0.3

    # 長スリープ - 重い処理(貼り付け反映, ウィンドウアクティブ化)の待機時間
    # 使用箇所: ウィンドウアクティブ化後, Ctrl+V貼り付け後
    # 高速PC: 0.5 / 中速PC: 1.0 / 低速PC: 1.5
    LONG_SLEEP = 1.0

    def __init__(self, wait=60, profile_dir=None, pause_for_login=False, stop_flag=None, logger=None, dry_run=False, max_items=None, retry=0, prefix="", suffix="", short_sleep=None, long_sleep=None):
        self.wait = wait
        self.profile_dir = profile_dir
        self.pause_for_login = pause_for_login
        self.stop_flag = stop_flag or threading.Event()
        self.logger = logger or logging.getLogger('sora_null')
        self.dry_run = dry_run
        self.max_items = max_items
        self.retry = retry
        self.prefix = prefix
        self.suffix = suffix
        self.input_x = 0
        self.input_y = 0
        self.chatgpt_window_handle = None
        self.original_window_handle = None

        # GUIから渡された値を使用、なければクラス定数を使用
        self.SHORT_SLEEP = short_sleep if short_sleep is not None else self.SHORT_SLEEP
        self.LONG_SLEEP = long_sleep if long_sleep is not None else self.LONG_SLEEP

        # PyAutoGUI設定
        # pyautogui.FAILSAFE = True  # コメントアウト: マウスを隅に移動した時の強制停止を無効化（GUIのStopボタンで停止可能）
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.0  # カスタムスリープで制御するため無効化
    
    def _check_stop(self):
        """緊急停止チェック"""
        if self.stop_flag.is_set():
            raise KeyboardInterrupt("Process stopped by user")

    def _get_window_title(self, hwnd):
        """ウィンドウハンドルからウィンドウタイトルを取得（cp932非対応文字を安全に処理）"""
        try:
            if hwnd:
                title = win32gui.GetWindowText(hwnd)
                if not title:
                    return f"<No Title> (Handle: {hwnd})"

                # cp932でエンコードできない文字を安全に処理
                try:
                    # cp932でエンコードできるか確認
                    title.encode('cp932')
                    return title
                except UnicodeEncodeError:
                    # エンコードできない文字を '?' に置き換え
                    safe_title = title.encode('cp932', errors='replace').decode('cp932')
                    return safe_title
            return "<Invalid Handle>"
        except Exception as e:
            return f"<Error getting title: {e}>"
    
    def find_chatgpt_window(self):
        """ChatGPTウィンドウを検索してハンドルを取得（座標記録時に実際のウィンドウを記録）"""
        self.logger.debug("Window will be captured during coordinate setup...")

        # ダミーのウィンドウ情報を返す（実際のウィンドウは座標記録時に取得）
        return "Active window (will be captured during coordinate setup)"
    
    def activate_chatgpt_window(self):
        """ChatGPTウィンドウをアクティブ化（座標記録時に記録されたウィンドウを使用）

        複数の方法でウィンドウアクティブ化を試行し、他のウィンドウで作業中でも強制的にフォーカスを奪取
        """
        if not self.chatgpt_window_handle:
            self.logger.error("ChatGPT window handle not captured yet")
            return False

        # 現在のフォアグラウンドウィンドウを記録
        self.original_window_handle = win32gui.GetForegroundWindow()
        current_title = self._get_window_title(self.original_window_handle)
        target_title = self._get_window_title(self.chatgpt_window_handle)

        self.logger.debug(f"Attempting to activate window: '{target_title}'")
        self.logger.debug(f"Current foreground window: '{current_title}'")

        # 最大3回リトライ
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                if attempt > 0:
                    self.logger.debug(f"Retry attempt {attempt + 1}/{max_attempts}")
                    time.sleep(1.0)  # リトライ前に待機（0.5秒→1.0秒に延長）

                # 方法1: ウィンドウを表示状態にする（隠れている場合に備えて）
                win32gui.ShowWindow(self.chatgpt_window_handle, win32con.SW_SHOW)
                time.sleep(0.2)

                # 方法2: ウィンドウを最小化状態から復元
                win32gui.ShowWindow(self.chatgpt_window_handle, win32con.SW_RESTORE)
                time.sleep(0.2)

                # 方法3: Z-orderで最前面に持ってくる
                win32gui.BringWindowToTop(self.chatgpt_window_handle)
                time.sleep(0.2)

                # 方法4: 最前面ウィンドウとして強制設定
                try:
                    win32gui.SetWindowPos(
                        self.chatgpt_window_handle,
                        win32con.HWND_TOPMOST,  # HWND_TOP → HWND_TOPMOSTに変更（常に最前面）
                        0, 0, 0, 0,
                        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
                    )
                    time.sleep(0.3)

                    # HWND_TOPMOSTを解除して通常の最前面ウィンドウに戻す
                    win32gui.SetWindowPos(
                        self.chatgpt_window_handle,
                        win32con.HWND_NOTOPMOST,
                        0, 0, 0, 0,
                        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
                    )
                    time.sleep(0.2)
                except Exception as e:
                    self.logger.debug(f"SetWindowPos failed: {e}")

                # 方法5: Alt押下でフォーカス制限を解除
                # Windowsのフォーカス制限を回避するために、Altキーを押して離す
                try:
                    import win32api
                    import win32con as wcon
                    # Altキーを押す
                    win32api.keybd_event(wcon.VK_MENU, 0, 0, 0)
                    time.sleep(0.05)
                    # Altキーを離す
                    win32api.keybd_event(wcon.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
                    time.sleep(0.1)
                except Exception as e:
                    self.logger.debug(f"Alt key simulation failed: {e}")

                # 方法6: フォアグラウンドウィンドウに設定
                # AttachThreadInputを使ってフォーカスを強制的に奪取
                try:
                    import win32process
                    # 現在のスレッドIDを取得
                    current_thread_id = win32process.GetCurrentThreadId()
                    # ターゲットウィンドウのスレッドIDを取得
                    target_thread_id = win32process.GetWindowThreadProcessId(self.chatgpt_window_handle)[0]

                    # スレッドを接続
                    if current_thread_id != target_thread_id:
                        win32process.AttachThreadInput(current_thread_id, target_thread_id, True)
                        time.sleep(0.1)

                    # フォアグラウンドウィンドウに設定
                    win32gui.SetForegroundWindow(self.chatgpt_window_handle)
                    time.sleep(0.1)

                    # スレッドを切断
                    if current_thread_id != target_thread_id:
                        win32process.AttachThreadInput(current_thread_id, target_thread_id, False)
                except Exception as e:
                    # AttachThreadInputが失敗した場合は通常の方法で試行
                    self.logger.debug(f"AttachThreadInput failed, using standard method: {e}")
                    try:
                        win32gui.SetForegroundWindow(self.chatgpt_window_handle)
                    except Exception as e2:
                        self.logger.debug(f"SetForegroundWindow also failed: {e2}")

                time.sleep(self.LONG_SLEEP)  # ウィンドウ切り替え後の待機（SHORT_SLEEP→LONG_SLEEPに変更）

                # アクティブ化後の確認
                activated_handle = win32gui.GetForegroundWindow()
                activated_title = self._get_window_title(activated_handle)

                if activated_handle == self.chatgpt_window_handle:
                    self.logger.debug(f"Successfully activated window: '{target_title}' (attempt {attempt + 1})")
                    return True
                else:
                    self.logger.warning(f"Attempt {attempt + 1}: Window activation incomplete. Target: '{target_title}', Actual: '{activated_title}'")

            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt == max_attempts - 1:
                    # 最後の試行でも失敗
                    self.logger.error(f"Failed to activate window '{target_title}' after {max_attempts} attempts: {e}")
                    return False

        # 全ての試行が失敗
        self.logger.error(f"Failed to activate window '{target_title}' after {max_attempts} attempts")
        return False
    
    def restore_original_window(self):
        """元のアクティブウィンドウに戻す"""
        if self.original_window_handle:
            try:
                win32gui.SetForegroundWindow(self.original_window_handle)
            except Exception:
                pass
    
    def load_prompts(self, csv_path, use_csv_mode=False) -> List[Tuple[str, str, str]]:
        """CSVファイルからプロンプトを読み込み（複数エンコーディング対応・CSV/GUIモード切り替え）

        Args:
            csv_path: CSVファイルパス
            use_csv_mode: Trueの場合CSV列からprefix/suffixを読み込み、Falseの場合GUIデフォルト値を使用

        Returns:
            List of (prompt, prefix, suffix) tuples
        """
        csv_path = Path(csv_path)

        self.logger.info(f"Loading prompts from CSV: {csv_path} (mode: {'CSV' if use_csv_mode else 'GUI'})")

        if not csv_path.exists():
            self.logger.error(f"CSV file not found: {csv_path}")
            raise InputError(f"CSV file not found: {csv_path}")

        # 複数のエンコーディングを試行（UTF-8 with BOMを優先）
        encodings = ['utf-8-sig', 'utf-8', 'cp932', 'shift-jis']
        rows = None
        successful_encoding = None

        for encoding in encodings:
            try:
                with open(csv_path, 'r', encoding=encoding, newline='') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                successful_encoding = encoding
                self.logger.debug(f"CSV loaded with {encoding} encoding, {len(rows)} rows")
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception as e:
                if encoding == encodings[-1]:
                    self.logger.error(f"Failed to read CSV file: {e}")
                    raise InputError(f"Failed to read CSV file: {e}")
                continue

        if rows is None or len(rows) == 0:
            self.logger.error("Failed to read CSV file with any supported encoding")
            raise InputError(f"Failed to read CSV file. Tried encodings: {', '.join(encodings)}")

        # prompt列の存在確認
        if 'prompt' not in rows[0]:
            self.logger.error(f"'prompt' column not found in CSV. Available columns: {list(rows[0].keys())}")
            raise InputError("'prompt' column not found in CSV file")

        # prefix/suffix列の存在確認
        has_prefix = 'prefix' in rows[0]
        has_suffix = 'suffix' in rows[0]

        # デフォルト値（GUIから渡された値）
        default_prefix = self.prefix
        default_suffix = self.suffix
        last_prefix = default_prefix
        last_suffix = default_suffix

        # CSV Modeでも列がない場合は警告を出してGUI Modeにフォールバック
        if use_csv_mode and not has_prefix and not has_suffix:
            available_columns = list(rows[0].keys())
            self.logger.warning(f"CSV Mode selected but 'prefix' and 'suffix' columns not found in CSV. Available columns: {available_columns}. Using GUI defaults instead.")
            use_csv_mode = False

        result = []

        if use_csv_mode and (has_prefix or has_suffix):
            # CSV Mode: 各行のprefix/suffixを使用（空欄は前行引き継ぎ）
            for row in rows:
                # done列のチェック (1, true, yes, on ならスキップ)
                done_val = str(row.get('done', '')).lower()
                if done_val in ('1', 'true', 'yes', 'on'):
                    continue

                prompt = row.get('prompt', '').strip()
                if not prompt:
                    continue  # 空行スキップ

                # prefix処理（列がない場合はデフォルト）
                if has_prefix:
                    prefix = row.get('prefix', '')  # .strip()を削除して前後の改行・空白を保持
                    if prefix == '':  # 完全に空の場合のみ前行引き継ぎ
                        prefix = last_prefix
                    else:
                        last_prefix = prefix
                else:
                    prefix = default_prefix

                # suffix処理（列がない場合はデフォルト）
                if has_suffix:
                    suffix = row.get('suffix', '')  # .strip()を削除して前後の改行・空白を保持
                    if suffix == '':  # 完全に空の場合のみ前行引き継ぎ
                        suffix = last_suffix
                    else:
                        last_suffix = suffix
                else:
                    suffix = default_suffix

                result.append((prompt, prefix, suffix))
        else:
            # GUI Mode: 全行でGUIデフォルト値を使用
            for row in rows:
                # done列のチェック
                done_val = str(row.get('done', '')).lower()
                if done_val in ('1', 'true', 'yes', 'on'):
                    continue

                prompt = row.get('prompt', '').strip()
                if not prompt:
                    continue
                result.append((prompt, default_prefix, default_suffix))

        if not result:
            self.logger.warning("No pending prompts found in CSV file (all done or empty)")
            raise InputError("No pending prompts found in CSV file (check 'done' column)")

        self.logger.info(f"Loaded {len(result)} prompts (encoding: {successful_encoding}, mode: {'CSV' if use_csv_mode else 'GUI'})")
        return result
    
    def mark_prompt_as_done(self, csv_path, processed_prompt):
        """処理済みプロンプトのdone列を1に更新（複数エンコーディング対応）"""
        try:
            # 複数のエンコーディングを試行して読み込み（UTF-8 with BOMを優先）
            encodings = ['utf-8-sig', 'utf-8', 'cp932', 'shift-jis']
            rows = None
            fieldnames = None
            successful_encoding = None

            for encoding in encodings:
                try:
                    with open(csv_path, 'r', encoding=encoding, newline='') as f:
                        reader = csv.DictReader(f)
                        fieldnames = reader.fieldnames
                        rows = list(reader)
                    successful_encoding = encoding
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue
                except Exception:
                    if encoding == encodings[-1]:
                        return False, 0, 0
                    continue

            if rows is None or fieldnames is None:
                return False, 0, 0

            if 'prompt' not in fieldnames:
                return False, 0, 0
            
            # done列がない場合は追加
            if 'done' not in fieldnames:
                fieldnames.append('done')
                # 既存の行にdone=0を設定（これから処理する行以外）
                for row in rows:
                    row['done'] = '0'

            original_count = len(rows)
            # 処理済みプロンプトと一致する最初の1行のみ更新
            found_first = False
            updated_count = 0
            
            for row in rows:
                # 既にdone=1になっているものはスキップ
                current_done = str(row.get('done', '')).lower()
                if current_done in ('1', 'true', 'yes', 'on'):
                    continue
                
                if not found_first and row.get('prompt', '').strip() == processed_prompt.strip():
                    row['done'] = '1'
                    found_first = True
                    updated_count += 1
                    # 1つ見つけたらループを抜ける（同じプロンプトが複数ある場合の挙動によるが、
                    # 順番に処理しているはずなので最初に見つかった未処理のものを更新）
                    break
            
            # 同じエンコーディングで保存
            with open(csv_path, 'w', encoding=successful_encoding, newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
                
            if found_first:
                return True, original_count, original_count # 行数は変わらない
            else:
                # 更新対象が見つからなかった
                self.logger.warning(f"Prompt not found in CSV for update: '{processed_prompt[:50]}...'")
                return False, original_count, original_count
        except Exception as e:
            self.logger.error(f"Failed to update prompt status in CSV: {e}")
            return False, 0, 0


def iter_process_prompts(csv_path, wait=60, profile_dir=None, pause_for_login=False,
                        stop_flag=None, logger=None, dry_run=False, max_items=None, retry=0, prefix="", suffix="", short_sleep=None, long_sleep=None, use_csv_mode=False) -> Generator[Dict[str, Any], None, Dict[str, int]]:
    """
    プロンプト一括処理のメイン関数（Generator版）
    
    Args:
        csv_path (str): CSVファイルパス
        wait (int): 生成完了待機時間（秒）
        profile_dir (str): プロファイルディレクトリ（未使用）
        pause_for_login (bool): ログイン用一時停止（未使用）
        stop_flag (threading.Event): 緊急停止用フラグ
        logger (logging.Logger): ロガーオブジェクト
        dry_run (bool): シミュレーションモード（ブラウザ操作なし）
        max_items (int): 処理する最大プロンプト数
        retry (int): 失敗時のリトライ回数
    
    Yields:
        Dict[str, Any]: イベント辞書
    
    Returns:
        Dict[str, int]: 最終結果 {"total": int, "sent": int, "failed": int}
    
    Raises:
        InputError: 入力エラー（CSV不存在等）
        RunError: 実行エラー（GUI操作失敗等）
    """
    core = ChatGPTCore(wait=wait, profile_dir=profile_dir,
                    pause_for_login=pause_for_login, stop_flag=stop_flag, logger=logger,
                    dry_run=dry_run, max_items=max_items, retry=retry, prefix=prefix, suffix=suffix,
                    short_sleep=short_sleep, long_sleep=long_sleep)
    
    try:
        # フェーズ1: 初期化
        yield {"type": "phase", "name": "initialization"}
        
        # プロンプト読み込み (use_csv_modeフラグを渡す)
        prompts = core.load_prompts(csv_path, use_csv_mode)
        
        # max_items制限適用
        if max_items and len(prompts) > max_items:
            if logger:
                logger.info(f"Limiting prompts from {len(prompts)} to {max_items} items")
            prompts = prompts[:max_items]
        
        total_prompts = len(prompts)
        
        yield {
            "type": "loaded", 
            "total": total_prompts,
            "csv_path": str(csv_path),
            "dry_run": dry_run,
            "max_items": max_items
        }
        
        # フェーズ2: Soraウィンドウ検索
        yield {"type": "phase", "name": "window_search"}
        
        if dry_run:
            # dry-runモードではブラウザ検索をスキップ
            if logger:
                logger.info("Dry-run mode: Skipping browser window search")
            yield {
                "type": "window_found", 
                "title": "[DRY-RUN] Simulated ChatGPT Window",
                "dry_run": True
            }
        else:
            window_title = core.find_chatgpt_window()
            if not window_title:
                if logger:
                    logger.error("ChatGPT window not found")
                raise RunError("ChatGPT window not found. Please open https://chatgpt.com in browser.")
            
            yield {
                "type": "window_found", 
                "title": window_title
            }
        
        # フェーズ3: 座標設定
        yield {"type": "phase", "name": "coordinate_setup"}
        
        if dry_run:
            # dry-runモードでは座標設定をスキップ
            if logger:
                logger.info("Dry-run mode: Skipping coordinate setup")
            core.input_x, core.input_y = 100, 200  # ダミー座標
            yield {
                "type": "coordinate", 
                "x": core.input_x, 
                "y": core.input_y,
                "dry_run": True
            }
        else:
            # 5秒カウントダウン
            for i in range(5, 0, -1):
                core._check_stop()
                yield {
                    "type": "countdown", 
                    "seconds_left": i,
                    "phase": "coordinate_setup",
                    "message": "ChatGPTの入力欄にマウスカーソルを置いてください"
                }
                time.sleep(1)
            
            # 座標記録とアクティブウィンドウの同時取得
            core.input_x, core.input_y = pyautogui.position()
            core.chatgpt_window_handle = win32gui.GetForegroundWindow()

            # 取得したウィンドウ情報をログに出力
            window_title = core._get_window_title(core.chatgpt_window_handle)
            if logger:
                logger.info(f"Target window captured: '{window_title}' (Handle: {core.chatgpt_window_handle})")
                logger.info(f"Mouse position: ({core.input_x}, {core.input_y})")

            yield {
                "type": "coordinate",
                "x": core.input_x,
                "y": core.input_y,
                "window_captured": True,
                "window_title": window_title,
                "window_handle": core.chatgpt_window_handle
            }
        
        # フェーズ4: 処理準備
        yield {"type": "phase", "name": "processing_prep"}
        
        if not dry_run:
            # 処理開始前の5秒カウントダウン
            for i in range(5, 0, -1):
                core._check_stop()
                yield {
                    "type": "countdown", 
                    "seconds_left": i,
                    "phase": "processing_prep",
                    "message": "自動処理を開始します"
                }
                time.sleep(1)
        else:
            if logger:
                logger.info("Dry-run mode: Skipping processing preparation countdown")
        
        # フェーズ5: プロンプト処理
        yield {"type": "phase", "name": "processing"}
        
        sent_count = 0
        failed_count = 0
        
        for i, (prompt, row_prefix, row_suffix) in enumerate(prompts, 1):
            core._check_stop()

            yield {
                "type": "progress",
                "step": "start",
                "index": i,
                "total": total_prompts,
                "prompt": prompt[:50] + "..." if len(prompt) > 50 else prompt,
                "dry_run": dry_run
            }
            
            # リトライロジック
            attempt = 0
            max_attempts = retry + 1
            success = False
            
            while attempt < max_attempts and not success:
                attempt += 1
                
                if attempt > 1:
                    if logger:
                        logger.info(f"Retry attempt {attempt-1}/{retry} for prompt {i}")
                    yield {
                        "type": "retry",
                        "attempt": attempt - 1,
                        "max_retry": retry,
                        "index": i,
                        "total": total_prompts
                    }
                
                try:
                    if dry_run:
                        # dry-runモードではGUI操作をスキップ
                        if logger:
                            logger.debug(f"Dry-run mode: Simulating prompt {i} processing")
                        
                        yield {
                            "type": "progress", 
                            "step": "simulate",
                            "index": i, 
                            "total": total_prompts,
                            "dry_run": True
                        }
                        
                        # シミュレーション用の短い待機
                        time.sleep(0.5)
                        success = True
                        sent_count += 1
                    else:
                        # ChatGPTウィンドウをアクティブ化
                        if not core.activate_chatgpt_window():
                            raise RunError("Failed to activate ChatGPT window")
                
                        yield {
                            "type": "progress",
                            "step": "activate",
                            "index": i,
                            "total": total_prompts
                        }

                        time.sleep(core.LONG_SLEEP)  # ウィンドウアクティブ化後の待機

                        # 入力エリアをクリック
                        pyautogui.click(core.input_x, core.input_y)
                        time.sleep(core.SHORT_SLEEP)  # クリック後の待機
                
                        yield {
                            "type": "progress", 
                            "step": "click",
                            "index": i, 
                            "total": total_prompts,
                            "x": core.input_x,
                            "y": core.input_y
                        }
                
                        # 既存テキストをクリア
                        pyautogui.hotkey('ctrl', 'a')
                        time.sleep(core.SHORT_SLEEP)  # Ctrl+A選択後の待機

                        # プレフィックス・サフィックスを適用してクリップボードにコピー（行ごとの値を使用）
                        final_prompt = f"{row_prefix}{prompt}{row_suffix}" if (row_prefix or row_suffix) else prompt
                        pyperclip.copy(final_prompt)
                        time.sleep(core.SHORT_SLEEP)  # クリップボードコピー後の待機
                
                        yield {
                            "type": "progress", 
                            "step": "copy",
                            "index": i, 
                            "total": total_prompts
                        }
                
                        # クリップボードから貼り付け
                        pyautogui.hotkey('ctrl', 'v')
                        time.sleep(core.LONG_SLEEP)  # Ctrl+V貼り付け後の待機

                        yield {
                            "type": "progress",
                            "step": "paste",
                            "index": i,
                            "total": total_prompts
                        }

                        # Enterキーで送信
                        pyautogui.press('enter')
                        time.sleep(core.SHORT_SLEEP)  # Enter送信後の待機
                
                        yield {
                            "type": "progress", 
                            "step": "send",
                            "index": i, 
                            "total": total_prompts
                        }
                        
                        success = True
                        sent_count += 1
                
                except RunError as e:
                    if attempt >= max_attempts:
                        failed_count += 1
                        if logger:
                            logger.error(f"RunError processing prompt {i} after {retry} retries: {e}")
                        yield {
                            "type": "error",
                            "step": "send_prompt",
                            "index": i,
                            "total": total_prompts,
                            "error": str(e),
                            "attempts": attempt,
                            "max_retry": retry
                        }
                    # リトライの場合はcontinueで次のループへ
                    continue
                except Exception as e:
                    if attempt >= max_attempts:
                        failed_count += 1
                        if logger:
                            logger.error(f"Unexpected error processing prompt {i} after {retry} retries: {e}")
                        yield {
                            "type": "error",
                            "step": "unexpected",
                            "index": i,
                            "total": total_prompts,
                            "error": str(e),
                            "attempts": attempt,
                            "max_retry": retry
                        }
                    # リトライの場合はcontinueで次のループへ
                    continue
            
            # 成功時の処理済みプロンプト更新（done=1）
            if success and not dry_run:
                success_csv, total_rows, _ = core.mark_prompt_as_done(csv_path, prompt)
                if success_csv:
                    if logger:
                        logger.info(f"Marked prompt as done in CSV")
                    yield {
                        "type": "csv_updated", 
                        "marked_done": prompt[:30] + "..." if len(prompt) > 30 else prompt,
                        "total_rows": total_rows
                    }
                
            # 最後のプロンプト以外は生成完了を待つ
            if success and i < len(prompts) and not dry_run:
                yield {"type": "phase", "name": "generation_wait"}
                
                # 元のウィンドウに戻す
                core.restore_original_window()
                
                # 待機時間中のカウントダウン
                remaining = core.wait
                while remaining > 0:
                    core._check_stop()

                    mins = remaining // 60
                    secs = remaining % 60

                    yield {
                        "type": "wait",
                        "seconds_left": remaining,
                        "minutes": mins,
                        "seconds": secs,
                        "next_index": i + 1,
                        "total": total_prompts
                    }

                    time.sleep(min(10, remaining))  # 10秒または残り時間
                    remaining -= min(10, remaining)
        
        # 最後のプロンプト処理後も生成完了を待機
        if sent_count > 0 and not dry_run:
            yield {"type": "phase", "name": "final_wait"}
            
            core.restore_original_window()
            remaining = core.wait
            while remaining > 0:
                core._check_stop()

                mins = remaining // 60
                secs = remaining % 60

                yield {
                    "type": "wait",
                    "seconds_left": remaining,
                    "minutes": mins,
                    "seconds": secs,
                    "final": True
                }

                time.sleep(min(10, remaining))
                remaining -= min(10, remaining)
        
        # 最終結果
        result = {
            "total": total_prompts,
            "sent": sent_count,
            "failed": failed_count
        }
        
        if logger:
            logger.info(f"Processing completed: {sent_count}/{total_prompts} sent, {failed_count} failed")
        
        yield {
            "type": "result",
            **result
        }
        
        return result
        
    except pyautogui.FailSafeException:
        raise RunError("Emergency stop activated (mouse moved to corner)")
    except KeyboardInterrupt:
        raise RunError("Process interrupted by user")
    except Exception as e:
        if isinstance(e, (InputError, RunError)):
            raise
        raise RunError(f"Unexpected error: {e}")


# 後方互換性のための関数
def process_prompts(csv_path, wait=60, profile_dir=None, pause_for_login=False, logger=None, dry_run=False, max_items=None, retry=0, prefix="", suffix=""):
    """
    後方互換性のためのラッパー関数

    Returns:
        dict: {"total": int, "sent": int, "failed": int}
    """
    result = None
    for event in iter_process_prompts(csv_path, wait, profile_dir, pause_for_login, logger=logger, dry_run=dry_run, max_items=max_items, retry=retry, prefix=prefix, suffix=suffix):
        if event.get("type") == "result":
            result = {k: v for k, v in event.items() if k != "type"}

    return result or {"total": 0, "sent": 0, "failed": 0}