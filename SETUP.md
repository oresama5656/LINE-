# セットアップガイド

## 1. Python環境の確認

Python 3.7以降が必要です。

```bash
python --version
```

## 2. tkinterdnd2のインストール

ドラッグ&ドロップ機能を有効にするために必要です。

```bash
pip install tkinterdnd2
```

### インストール確認

```bash
python -c "import tkinterdnd2; print('OK')"
```

`OK`と表示されればインストール成功です。

## 3. Node.jsの依存関係インストール

画像処理スクリプト（sharp）が必要です。

```bash
cd line_stamp_maker
npm install
```

### Node.jsのインストール確認

```bash
node --version
npm --version
```

Node.jsがインストールされていない場合:
- https://nodejs.org/ からダウンロードしてインストール

## 4. ツールの起動

```bash
python main.py
```

または `main.py` をダブルクリック

## トラブルシューティング

### ドラッグ&ドロップができない

**原因**: tkinterdnd2がインストールされていない

**解決方法**:
```bash
pip install tkinterdnd2
```

### Node.jsスクリプトエラー

**原因**: sharpモジュールがインストールされていない

**解決方法**:
```bash
cd line_stamp_maker
npm install
```

### 文字化け（Windowsコマンドプロンプト）

**原因**: コンソール文字コードの問題

**解決方法**:
- PowerShellまたはWindows Terminalを使用
- GUIアプリとして実行（main.pyをダブルクリック）

## 動作確認

1. `python main.py` でGUIを起動
2. フォルダ選択エリアにフォルダをドラッグ&ドロップ
3. パスが表示されれば成功！

## 最小要件

- Windows 10/11
- Python 3.7+
- Node.js 14+
- pip（Pythonパッケージマネージャー）
- npm（Node.jsパッケージマネージャー）

## 推奨環境

- Windows 11
- Python 3.10+
- Node.js 18+
- 8GB以上のRAM
- SSD推奨（画像処理の高速化）
