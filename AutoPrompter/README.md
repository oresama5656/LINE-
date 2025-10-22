# AutoPrompter - ChatGPT Prefix Tool

ChatGPT Web版への自動プロンプト送信ツール（独立版）

## 概要

このツールは、CSVファイルに記載されたプロンプトを自動的にChatGPT Webインターフェースに送信します。
GUI・CLIの両モードで動作し、prefix/suffixの追加、リトライ機能、dry-runモードなどをサポートしています。

## ファイル構成

```
D:\AutoPrompter\
├── chatgpt_prefix\          # メインモジュール
│   ├── __init__.py
│   ├── gui_launcher.py      # GUIアプリケーション エントリーポイント
│   ├── chatgpt_cli.py       # CLIインターフェース
│   ├── chatgpt_core.py      # コア処理（イベント駆動）
│   ├── config.py            # 設定管理
│   ├── logging_setup.py     # ログ設定
│   └── gui\                 # GUIモジュール
│       ├── __init__.py
│       ├── main_window.py   # メインウィンドウ
│       ├── process_monitor.py  # プロセス監視
│       └── event_handler.py    # イベント処理
├── launch-chatgpt-prefix.bat  # GUIランチャー
└── README.md                # このファイル
```

## 必要環境

- **Python 3.7以上**
- **必要なPythonパッケージ**:
  - `pyautogui` - マウス・キーボード操作
  - `pyperclip` - クリップボード操作
  - `pywin32` (Windowsのみ) - ウィンドウ操作
  - `tkinter` - GUI（通常Python標準ライブラリに含まれる）
  - `pyyaml` - 設定ファイル読み込み（オプション）

### インストール

```bash
pip install pyautogui pyperclip pywin32 pyyaml
```

## 使用方法

### GUI モード（推奨）

1. `launch-chatgpt-prefix.bat` をダブルクリックして起動
2. GUIでCSVファイルを選択
3. 必要に応じて設定を変更（Wait時間、Prefix/Suffix等）
4. "Start" ボタンをクリック

#### GUI設定項目

- **CSV File**: プロンプトが記載されたCSVファイル
- **Wait (seconds)**: 各プロンプト送信後の待機時間（デフォルト: 120秒）
- **Dry Run**: 実際の送信を行わずシミュレーション実行
- **Interactive**: 対話的ガイダンス表示（カウントダウン等）
- **Max Items**: 処理する最大プロンプト数（件数制限）
- **Retry**: 失敗時のリトライ回数
- **操作速度**: マウス・キーボード操作の速度（高速/中速/低速）
- **Mode**: GUIモード（GUI設定のPrefix/Suffixを使用）またはCSVモード（CSV列から読み込み）
- **Prefix**: プロンプトの前に追加するテキスト（複数行対応）
- **Suffix**: プロンプトの後に追加するテキスト（複数行対応）

### CLI モード

```bash
cd D:\AutoPrompter
python -m chatgpt_prefix.chatgpt_cli --csv your_prompts.csv
```

#### CLI オプション

```bash
# 基本使用
python -m chatgpt_prefix.chatgpt_cli --csv prompts.csv

# 詳細設定
python -m chatgpt_prefix.chatgpt_cli --csv prompts.csv --wait 120 --interactive

# Dry-runモード（実際には送信しない）
python -m chatgpt_prefix.chatgpt_cli --csv prompts.csv --dry-run

# 件数制限（最初の5件のみ処理）
python -m chatgpt_prefix.chatgpt_cli --csv prompts.csv --max-items 5

# Prefix/Suffix付き
python -m chatgpt_prefix.chatgpt_cli --csv prompts.csv --prefix "質問: " --suffix "\n\n詳しく説明してください。"

# CSV Modeでprefix/suffix列を使用
python -m chatgpt_prefix.chatgpt_cli --csv prompts.csv --csv-mode

# 全オプション表示
python -m chatgpt_prefix.chatgpt_cli --help
```

## CSV フォーマット

### GUI Mode（デフォルト）

```csv
prompt
この商品のレビューを書いて
使い方を教えて
```

GUIで設定したPrefix/Suffixが全プロンプトに適用されます。

### CSV Mode

```csv
prompt,prefix,suffix
この商品のレビューを書いて,質問: ,\n\n詳しくお願いします
使い方を教えて,,\n\n初心者向けに
```

- `prefix`/`suffix`列が空の場合、前の行の値を引き継ぎます
- `prefix`/`suffix`列がない場合、自動的にGUI Modeにフォールバックします

## 操作フロー

1. **ウィンドウ検索**: ChatGPT Webページを開いたブラウザウィンドウを検索
2. **座標設定**: 5秒のカウントダウン後、マウス位置をChatGPT入力欄として記録
3. **処理準備**: 5秒のカウントダウン後、自動処理開始
4. **プロンプト送信**: 各プロンプトを順次送信
   - ウィンドウをアクティブ化
   - 入力欄をクリック
   - プロンプトをコピー&ペースト
   - Enterキーで送信
5. **待機**: 設定した時間、生成完了を待つ
6. **CSV更新**: 処理済みプロンプトをCSVから削除（Dry-runモードでは削除しない）

## 緊急停止方法

- **マウスを画面左上角に移動**: PyAutoGUIのフェイルセーフ機能
- **Ctrl+C**: コマンドラインから中断（CLIモードのみ）
- **Stopボタン**: GUIの停止ボタン

## トラブルシューティング

### Python起動エラー

- Pythonがインストールされているか確認: `python --version`
- 必要なパッケージがインストールされているか確認

### ウィンドウが見つからない

- ChatGPT Webページ（https://chatgpt.com）をブラウザで開いているか確認
- 複数のブラウザウィンドウがある場合、ChatGPTウィンドウをアクティブにしてから実行

### 座標がずれる

- 座標設定時（5秒カウントダウン）にChatGPTの入力欄に正確にマウスを置く
- ブラウザのズーム設定が100%になっているか確認
- マルチモニター環境の場合、メインモニターで実行

### 操作が速すぎる/遅すぎる

- GUIの「操作速度」設定を変更（高速/中速/低速）
- CLIの場合: `--short-sleep` / `--long-sleep` オプションで調整

## 出力モード（CLI）

- `--verbose`: 詳細なテキスト出力（デフォルト）
- `--interactive`: 対話的ガイダンス表示（日本語メッセージ、カウントダウン等）
- `--json`: 最終結果のみJSON形式で出力
- `--ndjson`: 全イベントを1行ずつJSON出力（GUI/API連携用）
- `--quiet`: 最小限の出力のみ

## 注意事項

- **ChatGPT Webページが開いている必要があります**
- **処理中はPCを操作しないでください**（マウス・キーボード操作が自動実行されます）
- **Dry-runモードで事前テスト**することを推奨します
- **処理済みプロンプトはCSVから自動削除されます**（Dry-runモード除く）

## ライセンス

このツールは元々 `D:\WordPress_coommu\my-blog\tools\chatgpt_prefix\` にあるツールのコピーです。

---

**開発者向けメモ**

- イベント駆動アーキテクチャ（Generator パターン）
- GUI/CLI完全分離設計
- NDJSON ストリーミングによるリアルタイム通信
- 複数エンコーディング対応（UTF-8, CP932, Shift-JIS）
