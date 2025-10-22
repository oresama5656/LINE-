# WebP to PNG 一括変換ツール (PowerShell版)
# Windows標準機能のみで動作（外部ライブラリ不要）
# Windows 10/11のWebPコーデックを利用

# WPFアセンブリの読み込み
Add-Type -AssemblyName PresentationCore
Add-Type -AssemblyName WindowsBase

Write-Host ""
Write-Host "=========================================="
Write-Host "  WebP to PNG 一括変換ツール"
Write-Host "=========================================="
Write-Host ""

# スクリプトが配置されているフォルダを取得
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "処理フォルダ: $scriptDir"
Write-Host ""

# 出力フォルダを作成
$outputDir = Join-Path $scriptDir "png_output"
if (-not (Test-Path $outputDir)) {
    New-Item -Path $outputDir -ItemType Directory | Out-Null
    Write-Host "出力フォルダを作成しました: png_output"
} else {
    Write-Host "出力フォルダ: png_output"
}
Write-Host ""

# WebPファイルを検索
$webpFiles = Get-ChildItem -Path $scriptDir -Filter "*.webp" -File

if ($webpFiles.Count -eq 0) {
    Write-Host "WebPファイルが見つかりませんでした。"
    Write-Host ""
    exit
}

Write-Host "$($webpFiles.Count)個のWebPファイルを検出しました。"
Write-Host ""

$successCount = 0
$errorCount = 0

# 各WebPファイルを処理
foreach ($file in $webpFiles) {
    $inputPath = $file.FullName
    $outputFileName = [System.IO.Path]::GetFileNameWithoutExtension($inputPath) + ".png"
    $outputPath = Join-Path $outputDir $outputFileName

    try {
        # WebP画像を読み込み (WPF BitmapDecoder)
        $fileStream = [System.IO.File]::OpenRead($inputPath)
        $decoder = [System.Windows.Media.Imaging.BitmapDecoder]::Create(
            $fileStream,
            [System.Windows.Media.Imaging.BitmapCreateOptions]::None,
            [System.Windows.Media.Imaging.BitmapCacheOption]::OnLoad
        )
        $frame = $decoder.Frames[0]

        # PNG形式でエンコード
        $encoder = New-Object System.Windows.Media.Imaging.PngBitmapEncoder
        $encoder.Frames.Add([System.Windows.Media.Imaging.BitmapFrame]::Create($frame))

        # ファイルに保存
        $outputStream = [System.IO.File]::Create($outputPath)
        $encoder.Save($outputStream)

        # リソース解放
        $outputStream.Close()
        $fileStream.Close()

        $outputFileName = [System.IO.Path]::GetFileName($outputPath)
        Write-Host "✓ 変換完了: $($file.Name) -> $outputFileName" -ForegroundColor Green
        $successCount++
    }
    catch {
        # エラー時もストリームを確実に閉じる
        if ($outputStream) { $outputStream.Close() }
        if ($fileStream) { $fileStream.Close() }

        Write-Host "✗ 変換失敗: $($file.Name) - $($_.Exception.Message)" -ForegroundColor Red
        $errorCount++
    }
}

Write-Host ""
Write-Host "=========================================="
Write-Host "処理完了: 成功 $successCount 件, 失敗 $errorCount 件"
Write-Host "=========================================="
Write-Host ""
