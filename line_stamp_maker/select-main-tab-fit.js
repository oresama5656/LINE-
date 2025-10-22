const sharp = require('sharp');
const fs = require('fs');
const path = require('path');
const readline = require('readline');

// 設定
const CONFIG = {
  outputFolder: './output',
  mainSize: { width: 240, height: 240 },
  tabSize: { width: 96, height: 74 }
};

// readline インターフェース
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

// メイン処理
async function main() {
  console.log('🎨 LINEスタンプ main.png & tab.png 作成ツール（縮小版）');
  console.log('===============================================');
  console.log('※ 全体が見えるよう縮小してサイズ調整します');
  
  try {
    // 1. output フォルダの確認
    if (!fs.existsSync(CONFIG.outputFolder)) {
      console.log('❌ outputフォルダが見つかりません');
      console.log('💡 先に combine.js を実行してください');
      process.exit(1);
    }
    
    // 2. PNG画像の取得
    const pngFiles = getPngFiles();
    if (pngFiles.length === 0) {
      console.log('❌ outputフォルダにPNG画像が見つかりません');
      console.log('💡 先に combine.js を実行してください');
      process.exit(1);
    }
    
    // 3. 画像一覧表示
    displayImages(pngFiles);
    
    // 4. main画像選択
    const mainFile = await selectImage('main.png用画像', pngFiles);
    
    // 5. tab画像選択  
    const tabFile = await selectImage('tab.png用画像', pngFiles);
    
    // 6. 画像作成
    await createMainImage(mainFile);
    await createTabImage(tabFile);
    
    console.log('\n🎉 作成完了!');
    console.log('===============================================');
    console.log('✅ main.png: 240×240px で作成されました（全体表示・縮小）');
    console.log('✅ tab.png: 96×74px で作成されました（全体表示・縮小）');
    console.log(`📁 保存先: ${CONFIG.outputFolder} フォルダ`);
    
  } catch (error) {
    console.error('❌ エラーが発生しました:', error.message);
  } finally {
    rl.close();
  }
}

// PNG画像ファイル取得
function getPngFiles() {
  return fs.readdirSync(CONFIG.outputFolder)
    .filter(file => file.toLowerCase().endsWith('.png'))
    .filter(file => !['main.png', 'tab.png'].includes(file.toLowerCase())) // main.png, tab.pngは除外
    .sort((a, b) => {
      // 数字順ソート（01.png, 02.png... の順）
      const aNum = parseInt(a.match(/(\d+)/)?.[1] || '999');
      const bNum = parseInt(b.match(/(\d+)/)?.[1] || '999');
      return aNum - bNum;
    });
}

// 画像一覧表示
function displayImages(files) {
  console.log(`\n📋 利用可能な画像 (${files.length}個):`);
  console.log('===============================================');
  
  files.forEach((file, index) => {
    console.log(`${String(index + 1).padStart(2, ' ')}. ${file}`);
  });
  console.log('');
}

// 画像選択（ユーザー入力）
function selectImage(purpose, files) {
  return new Promise((resolve) => {
    const askSelection = () => {
      rl.question(`${purpose}を選択してください (1-${files.length}): `, (answer) => {
        const selection = parseInt(answer);
        
        if (isNaN(selection) || selection < 1 || selection > files.length) {
          console.log(`❌ 1から${files.length}の数字を入力してください`);
          askSelection();
        } else {
          const selectedFile = files[selection - 1];
          console.log(`✅ ${selectedFile} を選択しました`);
          resolve(selectedFile);
        }
      });
    };
    
    askSelection();
  });
}

// main画像作成 (240×240px) - 縮小版
async function createMainImage(filename) {
  const inputPath = path.join(CONFIG.outputFolder, filename);
  const outputPath = path.join(CONFIG.outputFolder, 'main.png');
  
  console.log(`\n🔄 main.png を作成中... (${filename} → 240×240px・縮小)`);
  
  await sharp(inputPath)
    .resize(CONFIG.mainSize.width, CONFIG.mainSize.height, {
      fit: 'contain', // アスペクト比維持、全体を収める
      background: { r: 0, g: 0, b: 0, alpha: 0 } // 透過背景
    })
    .png()
    .toFile(outputPath);
}

// tab画像作成 (96×74px) - 縮小版  
async function createTabImage(filename) {
  const inputPath = path.join(CONFIG.outputFolder, filename);
  const outputPath = path.join(CONFIG.outputFolder, 'tab.png');
  
  console.log(`🔄 tab.png を作成中... (${filename} → 96×74px・縮小)`);
  
  await sharp(inputPath)
    .resize(CONFIG.tabSize.width, CONFIG.tabSize.height, {
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