const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

// 設定
const CONFIG = {
  inputFolder: './base',
  outputFolder: './output',
  finalSize: { width: 370, height: 320 }
};

// メイン処理
async function main() {
  console.log('🎨 LINEスタンプ用リサイズツール（縮小版）');
  console.log('===============================================');
  console.log('※ 全体が見えるよう縮小してサイズ調整します');

  try {
    // 1. 入力フォルダの確認
    if (!fs.existsSync(CONFIG.inputFolder)) {
      console.log(`❌ ${CONFIG.inputFolder} フォルダが見つかりません`);
      process.exit(1);
    }

    // 2. 出力フォルダの作成
    if (!fs.existsSync(CONFIG.outputFolder)) {
      fs.mkdirSync(CONFIG.outputFolder, { recursive: true });
      console.log(`✅ ${CONFIG.outputFolder} フォルダを作成しました`);
    }

    // 3. 画像ファイル取得
    const imageFiles = getImageFiles(CONFIG.inputFolder);

    if (imageFiles.length === 0) {
      console.log(`❌ ${CONFIG.inputFolder} フォルダに画像ファイルが見つかりません`);
      console.log('💡 対応形式: PNG, JPG, JPEG, WebP');
      process.exit(1);
    }

    console.log(`\n📋 ${imageFiles.length}個の画像を処理します`);
    console.log('===============================================\n');

    // 4. 各画像をリサイズ
    let successCount = 0;
    for (const file of imageFiles) {
      try {
        await resizeImage(file);
        successCount++;
        console.log(`✅ [${successCount}/${imageFiles.length}] ${file}`);
      } catch (error) {
        console.error(`❌ [エラー] ${file}: ${error.message}`);
      }
    }

    console.log('\n===============================================');
    console.log(`🎉 リサイズ完了! ${successCount}/${imageFiles.length}個の画像を処理しました`);
    console.log(`📁 保存先: ${CONFIG.outputFolder} フォルダ`);
    console.log(`📏 サイズ: ${CONFIG.finalSize.width}×${CONFIG.finalSize.height}px（縮小・余白あり）`);

    // 5. ファイル名を連番リネーム
    console.log('\n🔄 ファイル名を連番リネーム中...');
    await renameToSequential();

  } catch (error) {
    console.error('❌ エラーが発生しました:', error.message);
    process.exit(1);
  }
}

// ファイル名を連番リネーム (01.png, 02.png... 最大40個)
async function renameToSequential() {
  const outputFiles = fs.readdirSync(CONFIG.outputFolder)
    .filter(file => {
      const ext = path.extname(file).toLowerCase();
      return ['.png', '.webp'].includes(ext);
    })
    .filter(file => !['main.png', 'tab.png'].includes(file.toLowerCase()))
    .sort();

  if (outputFiles.length === 0) {
    console.log('⚠️  リネーム対象のファイルがありません');
    return;
  }

  // 最大40個に制限
  const filesToRename = outputFiles.slice(0, 40);

  if (outputFiles.length > 40) {
    console.log(`⚠️  ファイルが40個を超えています。最初の40個のみ処理します`);
  }

  let renameCount = 0;
  for (let i = 0; i < filesToRename.length; i++) {
    const oldPath = path.join(CONFIG.outputFolder, filesToRename[i]);
    const ext = path.extname(filesToRename[i]);
    const newFilename = String(i + 1).padStart(2, '0') + ext;
    const newPath = path.join(CONFIG.outputFolder, newFilename);

    // 既に正しい名前の場合はスキップ
    if (filesToRename[i] === newFilename) {
      continue;
    }

    fs.renameSync(oldPath, newPath);
    renameCount++;
  }

  console.log(`✅ ${renameCount}個のファイルを連番リネームしました (01〜${String(filesToRename.length).padStart(2, '0')})`);
  console.log('\n🎉 すべての処理が完了しました!');
}

// 画像ファイル取得
function getImageFiles(folder) {
  return fs.readdirSync(folder)
    .filter(file => {
      const ext = path.extname(file).toLowerCase();
      return ['.png', '.jpg', '.jpeg', '.webp'].includes(ext);
    })
    .sort();
}

// 画像リサイズ
async function resizeImage(filename) {
  const inputPath = path.join(CONFIG.inputFolder, filename);
  const outputPath = path.join(CONFIG.outputFolder, filename);

  await sharp(inputPath)
    .resize(CONFIG.finalSize.width, CONFIG.finalSize.height, {
      fit: 'contain', // アスペクト比維持、全体を収める
      background: { r: 0, g: 0, b: 0, alpha: 0 } // 透過背景
    })
    .png()
    .toFile(outputPath);
}

// 実行
if (require.main === module) {
  main();
}
