const fs = require('fs');
const path = require('path');
const sharp = require('sharp');

// フォルダ内のWebPファイルをPNGに一括変換
async function convertWebpToPng() {
  const currentDir = __dirname;

  console.log('WebP to PNG 変換ツール');
  console.log('='.repeat(50));
  console.log(`処理フォルダ: ${currentDir}`);
  console.log('');

  try {
    // カレントディレクトリのファイル一覧を取得
    const files = fs.readdirSync(currentDir);

    // .webpファイルのみフィルタ
    const webpFiles = files.filter(file =>
      path.extname(file).toLowerCase() === '.webp'
    );

    if (webpFiles.length === 0) {
      console.log('WebPファイルが見つかりませんでした。');
      return;
    }

    console.log(`${webpFiles.length}個のWebPファイルを検出しました。`);
    console.log('');

    let successCount = 0;
    let errorCount = 0;

    // 各WebPファイルを処理
    for (const file of webpFiles) {
      const inputPath = path.join(currentDir, file);
      const outputPath = path.join(
        currentDir,
        path.basename(file, '.webp') + '.png'
      );

      try {
        // WebPをPNGに変換
        await sharp(inputPath)
          .png()
          .toFile(outputPath);

        console.log(`✓ 変換完了: ${file} → ${path.basename(outputPath)}`);
        successCount++;
      } catch (error) {
        console.error(`✗ 変換失敗: ${file} - ${error.message}`);
        errorCount++;
      }
    }

    console.log('');
    console.log('='.repeat(50));
    console.log(`処理完了: 成功 ${successCount}件, 失敗 ${errorCount}件`);

  } catch (error) {
    console.error('エラーが発生しました:', error.message);
  }
}

// スクリプト実行
convertWebpToPng()
  .then(() => {
    console.log('');
    console.log('何かキーを押すと終了します...');
  })
  .catch(error => {
    console.error('予期しないエラー:', error);
  });
