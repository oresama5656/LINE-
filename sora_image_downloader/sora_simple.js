// ==UserScript==
// @name         Sora Simple Image Downloader
// @description  Download Sora images (WebP) from current page
// @version      1.0.0
// @author       You
// @license      MIT
// @match        *://sora.com/*
// @match        *://sora.chatgpt.com/*
// @grant        GM_download
// @grant        GM_setValue
// @grant        GM_getValue
// ==/UserScript==

(function() {
    'use strict';

    // Configuration
    const config = {
        downloadedUrls: new Set(GM_getValue('downloadedUrls', [])),
        debug: true
    };

    let downloadStats = {
        total: 0,
        downloaded: 0,
        skipped: 0,
        failed: 0
    };

    function debugLog(message, data = null) {
        if (config.debug) {
            console.log(`[Sora Simple Downloader] ${message}`, data || '');
        }
    }

    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Extract task ID and timestamp from URL for filename
    function generateFilename(url) {
        try {
            const match = url.match(/task_([^\/]+)\/(\d+)_img_(\d+)\.webp/);
            if (match) {
                const [, taskId, timestamp, imgNum] = match;
                return `Sora_${timestamp}_${taskId.substring(0, 12)}_${imgNum}.webp`;
            }
            // Fallback
            return `Sora_${Date.now()}.webp`;
        } catch (err) {
            return `Sora_${Date.now()}.webp`;
        }
    }

    // Download all visible images
    async function downloadAllImages() {
        try {
            downloadStats = { total: 0, downloaded: 0, skipped: 0, failed: 0 };

            // Find all image/video elements with OpenAI CDN URLs
            const media = Array.from(document.querySelectorAll('img, video'));
            const urls = media
                .map(el => el.src || el.currentSrc)
                .filter(url => url && url.includes('videos.openai.com'))
                .filter(url => url.includes('.webp') || url.includes('.jpg') || url.includes('.png'));

            // Remove duplicates
            const uniqueUrls = [...new Set(urls)];

            downloadStats.total = uniqueUrls.length;

            if (uniqueUrls.length === 0) {
                alert('No images found on this page!\n\nTry scrolling to load more images.');
                return;
            }

            const confirmMsg = `Found ${uniqueUrls.length} images on current page.\n\nStart download?`;
            if (!confirm(confirmMsg)) {
                return;
            }

            debugLog(`Starting download of ${uniqueUrls.length} images`);

            for (let i = 0; i < uniqueUrls.length; i++) {
                const url = uniqueUrls[i];

                // Skip if already downloaded
                if (config.downloadedUrls.has(url)) {
                    downloadStats.skipped++;
                    debugLog(`Skipping already downloaded: ${url}`);
                    updateProgressInUI(i + 1, uniqueUrls.length);
                    continue;
                }

                try {
                    const filename = generateFilename(url);
                    debugLog(`Downloading ${i + 1}/${uniqueUrls.length}: ${filename}`);

                    await new Promise((resolve, reject) => {
                        GM_download({
                            url: url,
                            name: filename,
                            saveAs: false,
                            onload: () => {
                                config.downloadedUrls.add(url);
                                GM_setValue('downloadedUrls', Array.from(config.downloadedUrls));
                                downloadStats.downloaded++;
                                debugLog(`Downloaded: ${filename}`);
                                resolve();
                            },
                            onerror: (error) => {
                                debugLog(`Download failed: ${filename}`, error);
                                downloadStats.failed++;
                                reject(error);
                            }
                        });
                    });

                    updateProgressInUI(i + 1, uniqueUrls.length);
                    await sleep(300); // Small delay between downloads

                } catch (error) {
                    debugLog(`Error downloading: ${url}`, error);
                    downloadStats.failed++;
                }
            }

            // Final summary
            const summary = `Download Complete!\n` +
                          `Downloaded: ${downloadStats.downloaded}\n` +
                          `Skipped: ${downloadStats.skipped}\n` +
                          `Failed: ${downloadStats.failed}\n` +
                          `Total: ${downloadStats.total}`;

            alert(summary);
            debugLog('All downloads complete!');

        } catch (error) {
            alert(`Download failed: ${error.message}`);
            debugLog('Bulk download error:', error);
        }
    }

    // Update UI count
    function updateUICount() {
        const countEl = document.getElementById('sora-simple-count');
        if (countEl) {
            const media = Array.from(document.querySelectorAll('img, video'));
            const count = media
                .map(el => el.src || el.currentSrc)
                .filter(url => url && url.includes('videos.openai.com'))
                .filter(url => url.includes('.webp') || url.includes('.jpg') || url.includes('.png'))
                .length;
            countEl.textContent = `📊 Visible: ${count} images`;
        }
    }

    // Update progress in UI
    function updateProgressInUI(current, total) {
        const progressEl = document.getElementById('sora-simple-progress');
        if (progressEl) {
            const percent = Math.round((current / total) * 100);
            progressEl.textContent = `Progress: ${current}/${total} (${percent}%)`;
        }
    }

    // Create UI
    function createUI() {
        const existing = document.getElementById('sora-simple-downloader-ui');
        if (existing) existing.remove();

        const container = document.createElement('div');
        container.id = 'sora-simple-downloader-ui';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            border: 2px solid #10a37f;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            z-index: 10000;
            font-family: system-ui, -apple-system, sans-serif;
            min-width: 300px;
        `;

        container.innerHTML = `
            <h3 style="margin: 0 0 10px 0; color: #10a37f;">Sora Image Downloader</h3>
            <div id="sora-simple-count" style="margin-bottom: 8px; font-size: 12px; color: #666;">
                📊 Visible: 0 images
            </div>
            <div id="sora-simple-progress" style="margin-bottom: 10px; font-size: 12px; color: #666;">
            </div>
            <div style="margin-bottom: 10px; padding: 8px; background: #f3f4f6; border-radius: 5px; font-size: 11px;">
                <strong>Instructions:</strong><br>
                1. Scroll down to load more images<br>
                2. Click download to save visible images<br>
                3. Repeat to download all images
            </div>
            <button id="sora-simple-download-btn" style="
                background: #10a37f;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-weight: bold;
                width: 100%;
                margin-bottom: 5px;
            ">📥 Download Visible Images</button>
            <button id="sora-simple-refresh-btn" style="
                background: #6366f1;
                color: white;
                border: none;
                padding: 6px 20px;
                border-radius: 5px;
                cursor: pointer;
                width: 100%;
                margin-bottom: 5px;
                font-size: 12px;
            ">🔄 Refresh Count</button>
            <button id="sora-simple-clear-btn" style="
                background: #dc2626;
                color: white;
                border: none;
                padding: 6px 20px;
                border-radius: 5px;
                cursor: pointer;
                width: 100%;
                margin-bottom: 5px;
                font-size: 12px;
            ">🗑️ Clear History</button>
            <div style="font-size: 10px; color: #999; margin-top: 8px;">
                Downloaded: ${config.downloadedUrls.size} images
            </div>
        `;

        document.body.appendChild(container);

        // Update count immediately
        updateUICount();

        // Event listeners
        document.getElementById('sora-simple-download-btn').onclick = downloadAllImages;

        document.getElementById('sora-simple-refresh-btn').onclick = () => {
            updateUICount();
        };

        document.getElementById('sora-simple-clear-btn').onclick = () => {
            if (confirm('Clear download history? This will allow re-downloading previously downloaded images.')) {
                config.downloadedUrls.clear();
                GM_setValue('downloadedUrls', []);
                alert('History cleared!');
                createUI();
            }
        };
    }

    // Initialize
    function init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
            return;
        }

        setTimeout(() => {
            createUI();
            debugLog('Sora Simple Image Downloader initialized');
        }, 1000);
    }

    init();

})();
