# LINEスタンプ自動生成統合ツール

Soraでの画像生成から、ダウンロード、WebP→PNG変換、リサイズ＋リネーム、ZIP化までのワークフローを統合したGUIツールです。

## 📋 目次

- [概要](#概要)
- [ディレクトリ構成](#ディレクトリ構成)
- [必要環境](#必要環境)
- [セットアップ](#セットアップ)
- [使い方](#使い方)
- [ワークフロー](#ワークフロー)
- [設定ファイル](#設定ファイル)
- [トラブルシューティング](#トラブルシューティング)

## 📦 概要

このツールは、LINEスタンプ作成の以下の作業を自動化します：

1. **AutoPrompter**: Soraへのプロンプト自動貼り付け（独立実行）
2. **画像ダウンロード**: Chrome拡張でWebP形式の画像を一括ダウンロード
3. **WebP→PNG変換**: 自動判別＆変換（pngのみならスキップ）
4. **リサイズ＋リネーム**: 2パターン対応（縮小/トリミング）
5. **main/tab画像選択**: LINEスタンプ用のメイン・タブ画像作成
6. **ZIP作成**: LINEスタンプ提出用ZIP形式で自動圧縮

## 📁 ディレクトリ構成

```
D:\LINEスタンプツール\
├── main.py                        # エントリーポイント（GUIランチャー起動）
├── config.json                    # 共通設定ファイル
├── requirements.txt               # Python依存パッケージ
├── README.md                      # このファイル
│
├── gui/                           # GUI関連
│   ├── __init__.py
│   └── main_window.py            # Tkinterメインウィンドウ
│
├── modules/                       # 処理モジュール
│   ├── __init__.py
│   ├── logger.py                 # ログ出力
│   ├── config_manager.py         # 設定読み書き
│   ├── image_converter.py        # webp→png変換
│   ├── image_resizer.py          # リサイズ＋リネーム
│   └── zip_creator.py            # ZIP圧縮
│
├── AutoPrompter/                  # 独立実行（統合対象外）
│   ├── chatgpt_prefix/
│   ├── launch-chatgpt-prefix.bat
│   └── README.md
│
├── line_stamp_maker/              # 既存のNode.jsスクリプト
│   ├── convert-webp-to-png.js
│   ├── resize-only.js
│   ├── resize-only-trimming.js
│   ├── select-main-tab-fit.js
│   ├── select-main-tab-trimming.js
│   ├── package.json
│   └── ...
│
├── sora_image_downloader/         # Chrome拡張（実行対象外）
│   └── sora_simple.js
│
└── logs/                          # 処理ログ
    └── stamp_maker_YYYYMMDD_HHMMSS.log
```

## 🔧 必要環境

### Python
- **Python 3.7以降**（標準ライブラリのみ使用）
- 追加パッケージのインストールは不要

### Node.js
- **Node.js 14以降**
- `line_stamp_maker`フォルダ内のスクリプトで使用

### ブラウザ拡張
- **Google Chrome** + `sora_image_downloader`拡張（画像ダウンロード用）

## ⚙️ セットアップ

詳細なセットアップ手順は [`SETUP.md`](SETUP.md) を参照してください。

### クイックスタート

```bash
# 1. ドラッグ&ドロップライブラリをインストール
pip install tkinterdnd2

# 2. Node.jsの依存関係をインストール
cd line_stamp_maker
npm install

# 3. GUIツールを起動
cd ..
python main.py
```

または、`main.py`をダブルクリックして起動できます。

## 🚀 使い方

### GUI起動

```bash
python main.py
```

### ワークフロー全体

```
1️⃣ AutoPrompter（独立起動）
   └─ Soraにプロンプト自動貼り付け → 大量生成

2️⃣ Chrome拡張（sora_image_downloader）
   └─ WebP形式で画像を一括ダウンロード

3️⃣ 統合ツール（このGUI）
   ├─ フォルダ選択（ダウンロードした画像フォルダ）
   ├─ ☑ webp→png変換
   ├─ ☑ リサイズ＋リネーム（縮小 or トリミング）
   ├─ ☑ main/tab画像選択
   └─ ☑ ZIP作成
```

### GUI操作手順

#### 1. フォルダ選択

- 「フォルダを選択」ボタンをクリック
- Soraからダウンロードした画像フォルダを選択

#### 2. 設定

- **リサイズモード**: 縮小（全体表示）またはトリミング（中央切り抜き）
- **出力先**: デフォルトは `C:\LINE_OUTPUTS`（変更可能）
- 「設定を保存」ボタンで保存

#### 3. 処理選択

- ☑ **webp→png変換**: WebPファイルをPNGに変換（pngのみなら自動スキップ）
- ☑ **リサイズ＋リネーム**: 370×320pxにリサイズして01.png～40.pngにリネーム
- ☑ **tab/main画像を選択**: メイン画像とタブ画像を選択（番号指定）
  - main: メイン画像の番号（1～40）
  - tab: タブ画像の番号（1～40）
- ☑ **ZIP作成**: LINEスタンプ提出用ZIPファイル作成

#### 4. 実行

- 「すべて実行」ボタンをクリック
- 進捗バーとログで処理状況を確認
- 完了後、出力先フォルダに結果が保存されます

#### 5. AutoPrompter起動（任意）

- 「AutoPrompterを起動」ボタンで、Sora用プロンプト送信ツールを別途起動可能

## 📝 ワークフロー詳細

### フェーズ1: AutoPrompter（独立実行）

AutoPrompterフォルダ内の`launch-chatgpt-prefix.bat`を実行
- CSVファイルからプロンプトを読み込み
- Sora（ChatGPT）に自動貼り付け
- 大量の画像を生成

### フェーズ2: 画像ダウンロード

Chrome拡張`sora_image_downloader`を使用
- Soraで生成された画像を一括ダウンロード
- WebP形式で保存

### フェーズ3: 画像処理（このツール）

#### Step 1: WebP → PNG変換

- `convert-webp-to-png.js`を呼び出し
- WebPファイルのみを検出して変換
- pngのみの場合は自動スキップ

#### Step 2: リサイズ＋リネーム

- **縮小モード**: `resize-only.js`
  - 全体が見えるように縮小（余白あり）
  - 透過背景で370×320pxに調整
- **トリミングモード**: `resize-only-trimming.js`
  - 中央部分を切り抜き
  - 370×320pxに調整

連番リネーム: 01.png～40.png（最大40個）

#### Step 3: main/tab画像選択

- **縮小モード**: `select-main-tab-fit.js`
- **トリミングモード**: `select-main-tab-trimming.js`

指定した番号の画像から作成：
- main.png: 240×240px（メイン画像）
- tab.png: 96×74px（タブ画像）

#### Step 4: ZIP作成

必須ファイルを確認して圧縮：
- main.png
- tab.png
- 01.png～40.png

出力: `line_stamp_YYYYMMDD_HHMMSS.zip`

## 🔧 設定ファイル

`config.json`で以下を設定できます：

```json
{
  "settings": {
    "resize_mode": "fit",              // リサイズモード ("fit" or "trim")
    "output_base_path": "C:\\LINE_OUTPUTS",  // 出力先
    "auto_skip_png": true,             // png自動スキップ
    "max_stamp_count": 40              // 最大スタンプ数
  },
  "paths": {
    "line_stamp_maker": "./line_stamp_maker",
    "auto_prompter": "./AutoPrompter/launch-chatgpt-prefix.bat",
    "node_executable": "node"
  },
  "resize": {
    "fit": { "width": 370, "height": 320 },
    "trim": { "width": 370, "height": 320 },
    "main": { "width": 240, "height": 240 },
    "tab": { "width": 96, "height": 74 }
  },
  "logging": {
    "enabled": true,
    "log_folder": "./logs",
    "max_log_files": 30                // ログファイル保持数
  }
}
```

## 🐛 トラブルシューティング

### Python起動エラー

```
python: command not found
```

→ Pythonがインストールされているか確認: `python --version`

### Node.jsスクリプトエラー

```
Error: Cannot find module 'sharp'
```

→ `line_stamp_maker`フォルダで`npm install`を実行

### WebP変換がスキップされる

→ pngファイルのみの場合は自動スキップされます（正常動作）

### main.pngやtab.pngが作成されない

→ main/tab番号が範囲外（1～40以外）になっていないか確認

### ZIPが作成できない

→ main.png、tab.png、01.png～が存在するか確認

### AutoPrompterが起動しない

→ `config.json`の`paths.auto_prompter`パスが正しいか確認

## 📊 出力例

```
C:\LINE_OUTPUTS\
└── stamp_20250122_143025\
    ├── resized\
    │   ├── 01.png
    │   ├── 02.png
    │   ├── ...
    │   ├── 40.png
    │   ├── main.png
    │   └── tab.png
    └── zips\
        └── line_stamp_20250122_143025.zip
```

## 📄 ライセンス

このプロジェクトは個人用ツールです。

---

**開発メモ**

- Python標準ライブラリのみ使用（追加インストール不要）
- Node.jsスクリプトを再利用（既存コード活用）
- モジュール分割設計（拡張性重視）
- ログ管理（最大30ファイル自動削除）
- 設定永続化（JSON形式）

## 🔗 関連ツール

- **AutoPrompter**: `./AutoPrompter/README.md`
- **line_stamp_maker**: `./line_stamp_maker/README.md`
- **sora_image_downloader**: `./sora_image_downloader/README.md`
