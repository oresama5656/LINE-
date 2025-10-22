const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

// 設定（将来の拡張ポイント）
const CONFIG = {
  baseFolder: './base',
  textFolder: './text',
  outputFolder: './output',
  finalSize: { width: 370, height: 320 },
  textPosition: 'south' // 将来: 'north', 'center', 'southeast' なども対応可能
};

// メイン処理
async function main() {
  console.log('🎨 LINEスタンプ画像合成ツール');
  console.log('=====================================');
  
  try {
    // 1. フォルダの準備
    await setupFolders();
    
    // 2. 画像ファイルの取得
    const baseFiles = await getImageFiles(CONFIG.baseFolder, 'base');
    const textFiles = await getImageFiles(CONFIG.textFolder, 'text');
    
    if (baseFiles.length === 0 || textFiles.length === 0) {
      return;
    }
    
    // 3. 合成処理実行
    await combineImages(baseFiles, textFiles);
    
  } catch (error) {
    console.error('❌ エラーが発生しました:', error.message);
    console.log('\n📝 解決方法:');
    console.log('1. base/ と text/ フォルダに画像ファイル（PNG）を配置してください');
    console.log('2. npm install を実行してライブラリをインストールしてください');
    process.exit(1);
  }
}

// フォルダ作成と確認
async function setupFolders() {
  const folders = [CONFIG.baseFolder, CONFIG.textFolder, CONFIG.outputFolder];
  
  for (const folder of folders) {
    if (!fs.existsSync(folder)) {
      fs.mkdirSync(folder, { recursive: true });
      console.log(`📁 ${folder} フォルダを作成しました`);
    }
  }
}

// 画像ファイル取得
async function getImageFiles(folderPath, folderName) {
  if (!fs.existsSync(folderPath)) {
    console.log(`⚠️  ${folderPath} フォルダが見つかりません`);
    return [];
  }
  
  const files = fs.readdirSync(folderPath)
    .filter(file => /\.(png|jpg|jpeg)$/i.test(file))
    .sort();
    
  if (files.length === 0) {
    console.log(`⚠️  ${folderPath} に画像ファイルが見つかりません`);
    console.log(`💡 ${folderName === 'base' ? 'キャラクター' : 'テキスト'}画像（PNG形式）を配置してください`);
    return [];
  }
  
  console.log(`✅ ${folderName}画像: ${files.length}個 発見`);
  return files;
}

// 画像合成メイン処理
async function combineImages(baseFiles, textFiles) {
  // 1対1対応で合成（最小の個数まで）
  const maxLength = Math.min(baseFiles.length, textFiles.length);
  let completedCount = 0;
  let successCount = 0;
  let errorCount = 0;
  
  // ファイル数チェック
  if (baseFiles.length !== textFiles.length) {
    console.log(`⚠️  ファイル数が異なります:`);
    console.log(`   base: ${baseFiles.length}個, text: ${textFiles.length}個`);
    console.log(`   → ${maxLength}個のペアのみ合成します`);
  }
  
  console.log(`\n🔄 合成開始: ${maxLength}個の画像を1対1で作成します`);
  console.log('=====================================');
  
  const startTime = Date.now();
  
  // 1対1で合成
  for (let i = 0; i < maxLength; i++) {
    const baseFile = baseFiles[i];
    const textFile = textFiles[i];
    // LINEスタンプ用ファイル名: 01.png～40.png
    const outputName = `${String(i + 1).padStart(2, '0')}.png`;
    
    try {
      await combineImage(baseFile, textFile, outputName);
      successCount++;
      console.log(`✅ ${outputName} 完成 [${++completedCount}/${maxLength}] (${baseFile} + ${textFile})`);
      
    } catch (error) {
      errorCount++;
      console.log(`❌ ${outputName} エラー: ${error.message} [${++completedCount}/${maxLength}]`);
    }
  }
  
  // 結果サマリー
  const endTime = Date.now();
  const duration = Math.round((endTime - startTime) / 1000);
  
  console.log('\n🎉 合成完了!');
  console.log('=====================================');
  console.log(`📊 結果: 成功 ${successCount}個 / エラー ${errorCount}個`);
  console.log(`⏱️  処理時間: ${duration}秒`);
  console.log(`📁 出力先: ${CONFIG.outputFolder} フォルダ`);
  
  if (errorCount > 0) {
    console.log('\n💡 エラーが発生した場合は:');
    console.log('- 画像ファイルが破損していないか確認してください');
    console.log('- PNG形式で透過画像になっているか確認してください');
  }
}

// 1枚の画像合成処理
async function combineImage(baseFile, textFile, outputName) {
  const basePath = path.join(CONFIG.baseFolder, baseFile);
  const textPath = path.join(CONFIG.textFolder, textFile);
  const outputPath = path.join(CONFIG.outputFolder, outputName);
  
  // base画像を読み込み、リサイズ
  const baseImage = sharp(basePath)
    .resize(CONFIG.finalSize.width, CONFIG.finalSize.height, {
      fit: 'contain',
      background: { r: 0, g: 0, b: 0, alpha: 0 } // 透過背景
    });
  
  // text画像を読み込み
  const textBuffer = await sharp(textPath).toBuffer();
  
  // 合成実行
  await baseImage
    .composite([{
      input: textBuffer,
      gravity: CONFIG.textPosition
    }])
    .png()
    .toFile(outputPath);
}

// 実行
if (require.main === module) {
  main();
}