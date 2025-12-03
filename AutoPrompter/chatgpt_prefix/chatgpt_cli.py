#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sora GUI自動操作 - CLI インターフェース (イベント駆動版)

コマンドライン引数を処理し、イベント駆動版 sora_core を呼び出す
複数の出力モード対応: json/ndjson/verbose/interactive/quiet
"""

import argparse
import json
import sys
import threading
import signal
from pathlib import Path

from .chatgpt_core import iter_process_prompts, InputError, RunError
from .config import create_config
from .logging_setup import setup_chatgpt_logger, get_null_logger


class OutputHandler:
    """出力モード別のハンドラー"""
    
    def __init__(self, mode="verbose", interactive=False, quiet=False):
        self.mode = mode
        self.interactive = interactive
        self.quiet = quiet
        self.final_result = None
    
    def handle_event(self, event):
        """イベントを適切な形式で出力"""
        if self.mode == "json":
            # JSON モード: 最終結果のみ保存（出力は最後）
            if event.get("type") == "result":
                self.final_result = event
        
        elif self.mode == "ndjson":
            # NDJSON モード: 全イベントを1行JSONで出力
            try:
                print(json.dumps(event, ensure_ascii=False))
            except UnicodeEncodeError as e:
                # 特殊文字が原因のエラーを検出
                error_char = e.object[e.start:e.end] if hasattr(e, 'object') else '不明'
                error_event = {
                    "type": "error",
                    "error_type": "UnicodeEncodeError",
                    "message": f"特殊文字エラー: '{error_char}' (cp932でエンコードできない文字が含まれています)",
                    "detail": f"CSVファイル内の特殊文字（{error_char}など）を通常のASCII文字に変更してください",
                    "encoding": e.encoding if hasattr(e, 'encoding') else 'cp932'
                }
                print(json.dumps(error_event, ensure_ascii=True))
        
        elif self.mode == "verbose":
            # 詳細モード: 人向けのテキスト出力
            self._handle_verbose(event)
        
        elif self.quiet:
            # 静音モード: 最小限の出力のみ
            self._handle_quiet(event)
    
    def _handle_verbose(self, event):
        """詳細モードの出力処理"""
        event_type = event.get("type")
        
        if event_type == "phase":
            phase_names = {
                "initialization": "初期化",
                "window_search": "ChatGPTウィンドウ検索", 
                "coordinate_setup": "座標設定",
                "processing_prep": "処理準備",
                "processing": "プロンプト送信",
                "generation_wait": "生成完了待機",
                "final_wait": "最終生成完了待機"
            }
            phase_name = phase_names.get(event["name"], event["name"])
            print(f"\n{'='*50}")
            print(f"フェーズ: {phase_name}")
            print(f"{'='*50}")
        
        elif event_type == "loaded":
            print(f"プロンプト読み込み完了: {event['total']}個")
            print(f"CSVファイル: {event['csv_path']}")
        
        elif event_type == "window_found":
            print(f"ChatGPTウィンドウを発見: {event['title']}")
        
        elif event_type == "countdown":
            if self.interactive:
                phase = event.get("phase", "")
                message = event.get("message", "")
                if phase == "coordinate_setup":
                    if event["seconds_left"] == 5:
                        print("📍 ChatGPTの入力欄にマウスカーソルを置いてください")
                        print("⏰ 5秒後に自動で座標を記録します")
                        print("🚨 緊急停止: マウスを画面左上角に移動")
                    print(f"⏳ {event['seconds_left']}秒...")
                elif phase == "processing_prep":
                    if event["seconds_left"] == 5:
                        print("🚀 準備完了！")
                        print(f"📊 処理対象: プロンプト")
                        print("⏰ 5秒後に自動処理を開始します...")
                        print("🚨 緊急停止: Ctrl+C または マウスを左上角に移動")
                    print(f"⏳ {event['seconds_left']}秒...")
            else:
                # 非インタラクティブモードでは簡潔に
                if event["seconds_left"] == 5:
                    print(f"準備中... ({event.get('message', '')})")
        
        elif event_type == "coordinate":
            print(f"✅ 座標記録完了: ({event['x']}, {event['y']})")
            print("📝 この座標をChatGPTの入力欄として使用します")
        
        elif event_type == "progress":
            step = event.get("step")
            index = event["index"]
            total = event["total"]
            
            if step == "start":
                print(f"\n--- 📝 Processing prompt {index}/{total} ---")
                try:
                    print(f"📄 Prompt: {event.get('prompt', '')}")
                except UnicodeEncodeError as e:
                    error_char = e.object[e.start:e.end] if hasattr(e, 'object') else '不明'
                    print(f"📄 Prompt: [特殊文字エラー: '{error_char}' が含まれています]")
                    print(f"⚠️  CSVファイル内の特殊文字（{error_char}など）を通常のASCII文字に変更してください")
            elif step == "activate":
                print("🎯 ChatGPTウィンドウをアクティブ化")
            elif step == "click":
                print(f"🖱️ 入力エリアをクリック: ({event.get('x')}, {event.get('y')})")
            elif step == "copy":
                print("📋 クリップボードにコピー")
            elif step == "paste":
                print("📝 プロンプトを貼り付け")
            elif step == "send":
                print("🚀 プロンプトを送信")
        
        elif event_type == "csv_updated":
            marked_done = event.get("marked_done", "")
            if marked_done:
                 print(f"✅ CSV更新: プロンプトを完了(done=1)にマークしました")
            else:
                # 後方互換性（念のため）
                old_count = event.get("old_count", 0)
                new_count = event.get("new_count", 0)
                print(f"🗑️ 処理済みプロンプトを削除 ({old_count} → {new_count} rows)")
        
        elif event_type == "wait":
            mins = event.get("minutes", 0)
            secs = event.get("seconds", 0)
            
            if event.get("final"):
                print(f"⏱️ 最終生成完了まで待機中: {mins:02d}:{secs:02d}")
            else:
                next_idx = event.get("next_index", 0)
                total = event.get("total", 0)
                print(f"⏱️ 残り時間: {mins:02d}:{secs:02d} | 次: {next_idx}/{total}")
        
        elif event_type == "error":
            step = event.get("step", "unknown")
            index = event.get("index", 0)
            total = event.get("total", 0)
            error_msg = event.get("error", "")
            try:
                print(f"❌ エラー (step: {step}, {index}/{total}): {error_msg}")
            except UnicodeEncodeError as e:
                error_char = e.object[e.start:e.end] if hasattr(e, 'object') else '不明'
                print(f"❌ エラー (step: {step}, {index}/{total}): [特殊文字エラー: '{error_char}' が含まれています]")
                print(f"⚠️  CSVファイル内の特殊文字（{error_char}など）を通常のASCII文字に変更してください")
        
        elif event_type == "result":
            print(f"\n{'='*50}")
            print("🎉 処理完了!")
            print(f"{'='*50}")
            print(f"📊 処理対象: {event['total']}個")
            print(f"✅ 成功: {event['sent']}個")
            print(f"❌ 失敗: {event['failed']}個")
            
            if event['total'] > 0:
                success_rate = (event['sent'] / event['total']) * 100
                print(f"📈 成功率: {success_rate:.1f}%")
            
            print(f"{'='*50}")
    
    def _handle_quiet(self, event):
        """静音モードの出力処理"""
        event_type = event.get("type")
        
        if event_type == "loaded":
            print(f"Loaded {event['total']} prompts")
        elif event_type == "result":
            total = event['total']
            sent = event['sent']
            failed = event['failed']
            print(f"Completed: {sent}/{total} successful, {failed} failed")
    
    def finalize(self):
        """最終出力処理"""
        if self.mode == "json" and self.final_result:
            # JSON モード: 最終結果のみ出力
            output = {
                "status": "ok",
                "total": self.final_result["total"],
                "sent": self.final_result["sent"],
                "failed": self.final_result["failed"]
            }
            try:
                print(json.dumps(output, ensure_ascii=False))
            except UnicodeEncodeError as e:
                error_char = e.object[e.start:e.end] if hasattr(e, 'object') else '不明'
                error_output = {
                    "status": "error",
                    "error": f"特殊文字エラー: '{error_char}' (cp932でエンコードできない文字が含まれています)"
                }
                print(json.dumps(error_output, ensure_ascii=True))
    
    def error(self, error_msg, error_type="error"):
        """エラー出力"""
        if self.mode == "json":
            output = {
                "status": "error",
                "total": 0,
                "sent": 0,
                "failed": 0,
                "error": str(error_msg)
            }
            try:
                print(json.dumps(output, ensure_ascii=False))
            except UnicodeEncodeError as e:
                error_char = e.object[e.start:e.end] if hasattr(e, 'object') else '不明'
                output["error"] = f"特殊文字エラー: '{error_char}' (cp932でエンコードできない文字が含まれています)"
                print(json.dumps(output, ensure_ascii=True))
        elif self.mode == "ndjson":
            try:
                print(json.dumps({
                    "type": "error",
                    "error_type": error_type,
                    "message": str(error_msg)
                }, ensure_ascii=False))
            except UnicodeEncodeError as e:
                error_char = e.object[e.start:e.end] if hasattr(e, 'object') else '不明'
                print(json.dumps({
                    "type": "error",
                    "error_type": "UnicodeEncodeError",
                    "message": f"特殊文字エラー: '{error_char}' (cp932でエンコードできない文字が含まれています)"
                }, ensure_ascii=True))
        else:
            try:
                print(f"Error: {error_msg}", file=sys.stderr)
            except UnicodeEncodeError as e:
                error_char = e.object[e.start:e.end] if hasattr(e, 'object') else '不明'
                print(f"Error: 特殊文字エラー: '{error_char}' (cp932でエンコードできない文字が含まれています)", file=sys.stderr)


def create_parser():
    """コマンドライン引数パーサーを作成"""
    parser = argparse.ArgumentParser(
        description="ChatGPT GUI自動操作 - プロンプト一括送信ツール (イベント駆動版)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
出力モード:
  --json          最終結果のみ1行JSON出力
  --ndjson        全イベントを1行ずつJSON出力 (GUI/API連携用)
  --verbose       詳細なテキスト出力 (デフォルト)
  --interactive   対話的ガイダンス表示
  --quiet         最小限の出力のみ

使用例:
  python -m chatgpt.chatgpt_cli --csv prompts.csv
  python -m chatgpt.chatgpt_cli --csv prompts.csv --wait 120 --json
  python -m chatgpt.chatgpt_cli --csv prompts.csv --interactive
  python -m chatgpt.chatgpt_cli --csv prompts.csv --ndjson
        """
    )
    
    # CSV引数（設定ファイルでも指定可能）
    parser.add_argument(
        "--csv",
        metavar="PATH",
        help="プロンプトが記載されたCSVファイルパス（必須、設定ファイルでも指定可能）"
    )
    
    # オプション引数
    parser.add_argument(
        "--wait",
        type=int,
        default=60,
        metavar="SECONDS",
        help="生成完了待機時間（秒）[default: 60]"
    )
    
    parser.add_argument(
        "--profile-dir",
        metavar="PATH",
        help="ブラウザプロファイルディレクトリ（オプション）"
    )
    
    # フラグ引数
    parser.add_argument(
        "--pause-for-login",
        action="store_true",
        help="ログイン用一時停止を有効にする"
    )
    
    # 出力モードオプション
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "--json",
        action="store_true",
        help="結果を1行JSONで出力（進捗なし）"
    )
    
    output_group.add_argument(
        "--ndjson",
        action="store_true",
        help="全イベントを1行ずつJSON出力（GUI/API連携用）"
    )
    
    output_group.add_argument(
        "--quiet",
        action="store_true",
        help="最小限の出力のみ"
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="対話的ガイダンス表示（カウントダウン等）"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="詳細なテキスト出力（デフォルト）"
    )
    
    # 設定・ログ関連
    parser.add_argument(
        "--config",
        metavar="PATH",
        help="設定ファイルパス（YAML形式）"
    )
    
    parser.add_argument(
        "--log-file",
        metavar="PATH",
        help="ログファイル出力先"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="ログレベル"
    )
    
    # 安全オプション
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="実際の処理を行わずシミュレーション実行（ブラウザ非起動）"
    )
    
    parser.add_argument(
        "--max-items",
        type=int,
        metavar="N",
        help="処理する最大プロンプト数（件数制限）"
    )
    
    parser.add_argument(
        "--retry",
        type=int,
        default=0,
        metavar="N",
        help="失敗時のリトライ回数 [default: 0]"
    )

    # プレフィックス・サフィックス
    parser.add_argument(
        "--prefix",
        type=str,
        default="",
        metavar="TEXT",
        help="プロンプトの前に追加するテキスト [default: なし]"
    )

    parser.add_argument(
        "--suffix",
        type=str,
        default="",
        metavar="TEXT",
        help="プロンプトの後に追加するテキスト [default: なし]"
    )

    # 操作速度設定
    parser.add_argument(
        "--short-sleep",
        type=float,
        metavar="SECONDS",
        help="短スリープ時間（秒）- キーボード・マウス操作後の待機 [default: 0.3]"
    )

    parser.add_argument(
        "--long-sleep",
        type=float,
        metavar="SECONDS",
        help="長スリープ時間（秒）- 重い処理後の待機 [default: 1.0]"
    )

    # CSV/GUIモード切り替え
    parser.add_argument(
        "--csv-mode",
        action="store_true",
        help="CSVモード: prefix/suffix列をCSVから読み込む（デフォルト: GUIモード）"
    )

    return parser


def setup_signal_handling(stop_flag):
    """シグナルハンドリング設定"""
    def signal_handler(signum, frame):
        print("\n緊急停止シグナルを受信しました...", file=sys.stderr)
        stop_flag.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def main():
    """CLI メイン処理"""
    parser = create_parser()
    
    # 引数解析
    try:
        args = parser.parse_args()
    except SystemExit as e:
        # argparse内部でのエラー（--help含む）
        sys.exit(e.code if e.code is not None else 1)
    
    # 設定ファイル読み込みと設定マージ
    config = create_config(config_file=args.config, cli_args=args)
    
    # 引数検証
    wait_time = config.get('wait', 60)
    if wait_time <= 0:
        print("Error: wait must be positive integer", file=sys.stderr)
        sys.exit(1)
    
    # 設定から出力モード決定
    output_mode = config.get('output_mode', 'verbose')
    interactive = config.get('interactive', False)
    quiet = config.get('quiet', False)
    
    # ロガー設定
    log_file = config.get('log_file')
    log_level = config.get('log_level', 'INFO')
    
    if log_file or log_level != 'INFO':
        logger = setup_chatgpt_logger(log_file=log_file, log_level=log_level)
    else:
        logger = get_null_logger()
    
    # 出力ハンドラー作成
    output_handler = OutputHandler(
        mode=output_mode,
        interactive=interactive,
        quiet=quiet
    )
    
    # CSV ファイルパスの検証
    csv_file = config.get('csv')
    if not csv_file:
        output_handler.error("CSV file path is required. Use --csv argument or specify 'csv' in config file", "InputError")
        sys.exit(2)
    
    csv_path = Path(csv_file)
    if not csv_path.is_absolute():
        csv_path = Path.cwd() / csv_path
    
    # 緊急停止フラグとシグナルハンドリング
    stop_flag = threading.Event()
    setup_signal_handling(stop_flag)
    
    try:
        # イベント駆動処理実行
        result = None
        for event in iter_process_prompts(
            csv_path=str(csv_path),
            wait=wait_time,
            profile_dir=config.get('profile_dir'),
            pause_for_login=config.get('pause_for_login', False),
            stop_flag=stop_flag,
            logger=logger,
            dry_run=config.get('dry_run', False),
            max_items=config.get('max_items'),
            retry=config.get('retry', 0),
            prefix=config.get('prefix', ''),
            suffix=config.get('suffix', ''),
            short_sleep=config.get('short_sleep'),
            long_sleep=config.get('long_sleep'),
            use_csv_mode=config.get('use_csv_mode', False)
        ):
            output_handler.handle_event(event)
            
            # 最終結果を保存
            if event.get("type") == "result":
                result = {k: v for k, v in event.items() if k != "type"}
        
        # 最終出力処理
        output_handler.finalize()
        
        # 終了コード判定
        if result and result.get("failed", 0) > 0 and result.get("sent", 0) == 0:
            # 全て失敗した場合は実行エラー扱い
            sys.exit(3)
        
        sys.exit(0)
        
    except InputError as e:
        # 入力エラー -> 終了コード2
        output_handler.error(str(e), "InputError")
        sys.exit(2)
        
    except RunError as e:
        # 実行エラー -> 終了コード3
        output_handler.error(str(e), "RunError")
        sys.exit(3)
        
    except KeyboardInterrupt:
        # Ctrl+C 中断
        output_handler.error("Process interrupted by user", "KeyboardInterrupt")
        sys.exit(3)
        
    except Exception as e:
        # 予期しないエラー -> 実行エラー扱い
        output_handler.error(f"Unexpected error: {e}", "UnexpectedError")
        sys.exit(3)


if __name__ == "__main__":
    main()