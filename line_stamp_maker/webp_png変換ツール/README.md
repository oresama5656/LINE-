# WebP to PNG 一括変換ツール

WebP形式の画像ファイルをPNG形式に一括変換するツールです。

## 特徴

- ✅ **外部ライブラリ不要** - Windows標準機能のみで動作
- ✅ **どこでも使える** - フォルダごとコピーすればどこでも動作
- ✅ **簡単操作** - バッチファイルをダブルクリックするだけ
- ✅ **元ファイル保持** - 変換後も元のWebPファイルはそのまま残ります

## 動作環境

- Windows 10 / Windows 11
- PowerShell（Windows標準搭載）

## ファイル構成

```
webp_png変換ツール/
├── webp2png.bat              # 実行用バッチファイル
├── convert-webp-to-png.ps1   # PowerShell変換スクリプト
└── README.md                 # このファイル
```

## 使い方

### 1. ツールの配置

このフォルダ全体を、変換したいWebPファイルがある場所にコピーします。

### 2. WebPファイルの配置

変換したいWebPファイルを、`webp2png.bat` と同じフォルダに配置します。

```
作業フォルダ/
├── webp2png.bat
├── convert-webp-to-png.ps1
├── image1.webp  ← 変換したいファイル
├── image2.webp  ← 変換したいファイル
└── image3.webp  ← 変換したいファイル
```

### 3. 変換実行

**`webp2png.bat`** をダブルクリックします。

### 4. 完了

変換が完了すると、`png_output` フォルダが自動的に作成され、その中にPNGファイルが保存されます。

```
作業フォルダ/
├── webp2png.bat
├── convert-webp-to-png.ps1
├── image1.webp
├── image2.webp
├── image3.webp
└── png_output/  ← 自動作成
    ├── image1.png  ← 変換されたファイル
    ├── image2.png  ← 変換されたファイル
    └── image3.png  ← 変換されたファイル
```

## トラブルシューティング

### PowerShellのセキュリティエラーが出る場合

バッチファイルには `-ExecutionPolicy Bypass` が設定されているため、通常は問題ありません。
もしエラーが出る場合は、PowerShellを管理者権限で開き、以下のコマンドを実行してください：

```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### WebPファイルが見つからないと表示される場合

- WebPファイルが `webp2png.bat` と同じフォルダにあることを確認してください
- ファイルの拡張子が `.webp` であることを確認してください（`.WEBP` のように大文字の場合は認識されません）

### 変換に失敗する場合

- Windows 10/11であることを確認してください（Windows 7/8ではWebPコーデックが標準搭載されていません）
- WebPファイルが破損していないか確認してください

## 配布について

このツールは自由に配布・共有できます。
以下の2ファイルをセットで配布してください：

- `webp2png.bat`
- `convert-webp-to-png.ps1`

## 技術情報

- **使用技術**: PowerShell + WPF (Windows Presentation Foundation)
- **画像処理**: System.Windows.Media.Imaging.BitmapDecoder/PngBitmapEncoder
- **対応形式**: WebP → PNG（透過情報も保持されます）

## ライセンス

このツールは自由に使用・改変・配布できます。

---

**作成日**: 2025年10月19日
