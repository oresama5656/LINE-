# Sora Simple Image Downloader

[English](#english) | [日本語](#japanese)

---

<a name="english"></a>
## English

### Overview
A simple and efficient Tampermonkey userscript to download all your Sora-generated images in WebP format.

### Features
- ✅ **Download visible images** - Downloads all currently visible images on the page
- ✅ **WebP format** - Preserves original WebP format
- ✅ **Duplicate detection** - Automatically skips already downloaded images
- ✅ **Scroll support** - Load more images by scrolling, then download again
- ✅ **Progress tracking** - Real-time download progress display
- ✅ **Simple UI** - Clean, easy-to-use interface in the top-right corner

### Requirements
- Google Chrome (or Chromium-based browser)
- Tampermonkey extension

### Installation

#### Step 1: Install Tampermonkey
1. Visit the [Chrome Web Store](https://chrome.google.com/webstore/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo)
2. Click "Add to Chrome"
3. Confirm installation

#### Step 2: Configure Tampermonkey Permissions ⚠️ IMPORTANT
**Without this step, the script will NOT work!**

1. Open Chrome and go to `chrome://extensions/`
2. Find **Tampermonkey** in the list
3. Click **"Details"**
4. Find **"Site access"** section
5. Change from "On click" to **"On all sites"**
6. Reload the Sora page

#### Step 3: Install Script
1. Click the Tampermonkey icon in your browser
2. Select **"Create a new script"**
3. Delete all existing code in the editor
4. Copy and paste the entire contents of `sora_simple.js`
5. Press **Ctrl+S** (or Cmd+S on Mac) to save
6. Close the editor

#### Step 4: Enable Automatic Downloads (Optional but Recommended)
1. Go to `chrome://settings/content/automaticDownloads`
2. Enable **"Sites can ask to automatically download multiple files"**
3. Or add `sora.chatgpt.com` to the "Allowed" list

### Usage

1. **Open Sora Library**
   - Navigate to https://sora.chatgpt.com/library

2. **Scroll to Load Images**
   - Scroll down to load more images into view
   - The UI in the top-right corner shows the count of visible images

3. **Download Visible Images**
   - Click the **"📥 Download Visible Images"** button
   - Confirm the download when prompted
   - Wait for download to complete

4. **Download More Images**
   - Scroll down to load additional images
   - Click **"🔄 Refresh Count"** to update the visible count
   - Click **"📥 Download Visible Images"** again
   - Already downloaded images will be automatically skipped

5. **Clear History (Optional)**
   - Click **"🗑️ Clear History"** to reset download tracking
   - This allows re-downloading previously downloaded images

### File Naming Format

Downloaded files are named with the following pattern:
```
Sora_[timestamp]_[taskID]_[imageNumber].webp
```

Example: `Sora_1760690792_01k7rngd7qfx_1.webp`

- **timestamp**: Creation timestamp
- **taskID**: Unique task identifier (first 12 characters)
- **imageNumber**: Image number (0, 1, 2, etc.)

### Troubleshooting

#### Script Not Working / UI Not Visible
1. **Check Tampermonkey permissions**
   - Go to `chrome://extensions/`
   - Find Tampermonkey → Details
   - Ensure "Site access" is set to **"On all sites"**

2. **Verify script is enabled**
   - Click Tampermonkey icon
   - "Sora Simple Image Downloader" should show a number in parentheses like "(1)"
   - If it says "This script has not been executed yet", check permissions again

3. **Reload the page**
   - Press **Ctrl+Shift+R** for a hard reload
   - Check if the UI appears in the top-right corner

#### Downloads Are Slow
1. **Enable automatic downloads**
   - Go to `chrome://settings/content/automaticDownloads`
   - Set to "Allow sites to automatically download multiple files"

2. **Check site permissions**
   - Click the lock icon 🔒 in the address bar
   - Go to "Site settings"
   - Ensure "Automatic downloads" is set to "Allow"

#### Console Errors (Advanced)
1. Press **F12** to open Developer Tools
2. Go to the **Console** tab
3. Look for messages starting with `[Sora Simple Downloader]`
4. Check for any error messages in red

### License
MIT License - Free to use, modify, and distribute.

---

<a name="japanese"></a>
## 日本語

### 概要
Soraで生成した画像をWebP形式で一括ダウンロードできるシンプルなTampermonkeyユーザースクリプトです。

### 機能
- ✅ **表示中の画像をダウンロード** - ページに表示されている全ての画像をダウンロード
- ✅ **WebP形式** - オリジナルのWebP形式のまま保存
- ✅ **重複検出** - 既にダウンロード済みの画像は自動スキップ
- ✅ **スクロール対応** - スクロールして追加の画像を読み込み、再度ダウンロード可能
- ✅ **進捗表示** - リアルタイムでダウンロード進捗を表示
- ✅ **シンプルなUI** - 右上に表示される使いやすいインターフェース

### 必要なもの
- Google Chrome（またはChromiumベースのブラウザ）
- Tampermonkey拡張機能

### インストール方法

#### ステップ1: Tampermonkeyをインストール
1. [Chrome Web Store](https://chrome.google.com/webstore/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo)にアクセス
2. 「Chromeに追加」をクリック
3. インストールを確認

#### ステップ2: Tampermonkeyの権限設定 ⚠️ 重要
**この手順を行わないとスクリプトは動作しません！**

1. Chromeで `chrome://extensions/` を開く
2. リストから **Tampermonkey** を探す
3. **「詳細」**をクリック
4. **「サイトアクセス」**セクションを探す
5. 「クリック時」から **「すべてのサイト」** に変更
6. Soraページをリロード

#### ステップ3: スクリプトをインストール
1. ブラウザのTampermonkeyアイコンをクリック
2. **「新規スクリプトを作成」**を選択
3. エディタ内の既存コードを全て削除
4. `sora_simple.js` の内容を全てコピーして貼り付け
5. **Ctrl+S**（MacはCmd+S）で保存
6. エディタを閉じる

#### ステップ4: 自動ダウンロードを許可（任意だが推奨）
1. `chrome://settings/content/automaticDownloads` を開く
2. **「サイトが複数のファイルを自動的にダウンロードできるようにする」**を有効化
3. または `sora.chatgpt.com` を「許可」リストに追加

### 使い方

1. **Soraライブラリを開く**
   - https://sora.chatgpt.com/library にアクセス

2. **スクロールして画像を読み込む**
   - 下にスクロールして画像を表示
   - 右上のUIに表示されている画像数が表示されます

3. **表示中の画像をダウンロード**
   - **「📥 Download Visible Images」**ボタンをクリック
   - ダウンロード確認ダイアログで「OK」をクリック
   - ダウンロード完了まで待つ

4. **追加の画像をダウンロード**
   - さらに下にスクロールして追加の画像を読み込む
   - **「🔄 Refresh Count」**をクリックして表示数を更新
   - 再度 **「📥 Download Visible Images」**をクリック
   - 既にダウンロード済みの画像は自動的にスキップされます

5. **履歴をクリア（任意）**
   - **「🗑️ Clear History」**をクリックしてダウンロード履歴をリセット
   - 以前ダウンロードした画像を再度ダウンロードできるようになります

### ファイル名の形式

ダウンロードされるファイル名は以下の形式です：
```
Sora_[タイムスタンプ]_[タスクID]_[画像番号].webp
```

例: `Sora_1760690792_01k7rngd7qfx_1.webp`

- **タイムスタンプ**: 作成時のタイムスタンプ
- **タスクID**: 一意のタスク識別子（最初の12文字）
- **画像番号**: 画像番号（0, 1, 2など）

### トラブルシューティング

#### スクリプトが動作しない / UIが表示されない
1. **Tampermonkeyの権限を確認**
   - `chrome://extensions/` を開く
   - Tampermonkey → 詳細
   - 「サイトアクセス」が **「すべてのサイト」** になっているか確認

2. **スクリプトが有効か確認**
   - Tampermonkeyアイコンをクリック
   - 「Sora Simple Image Downloader」の横に「(1)」のような数字が表示されているか確認
   - 「このスクリプトはまだ実行されていません」と表示されている場合は、権限設定を再確認

3. **ページをリロード**
   - **Ctrl+Shift+R** で強制リロード
   - 右上にUIが表示されるか確認

#### ダウンロードが遅い
1. **自動ダウンロードを許可**
   - `chrome://settings/content/automaticDownloads` を開く
   - 「サイトが複数のファイルを自動的にダウンロードできるようにする」を有効化

#### コンソールエラー（上級者向け）
1. **F12**キーでデベロッパーツールを開く
2. **Console**タブに移動
3. `[Sora Simple Downloader]` で始まるメッセージを確認
4. 赤色のエラーメッセージがないか確認

### ライセンス
MITライセンス - 自由に使用、改変、配布できます。

---

## Files
- `sora_simple.js` - Main userscript file / メインスクリプトファイル
- `README.md` - This file / このファイル

## Author
Created with assistance from Claude Code

## Version
1.0.0
