(() => {
    'use strict';
    
    // Speed test state
    let isTestRunning = false;
    let testAborted = false;
    
    // ------------------------------
    // Speed Test Functions
    // ------------------------------
    
    async function runPingTest() {
        const startTime = performance.now();
        
        try {
            const response = await fetch('/cgi-bin/speedtest.py?test=ping');
            const endTime = performance.now();
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                const pingTime = Math.round(endTime - startTime);
                return pingTime;
            } else {
                throw new Error(result.message || 'Ping test failed');
            }
        } catch (error) {
            console.error('Ping test error:', error);
            throw error;
        }
    }
    
    async function calculateHash(data) {
        // Use a simple hash function that works in all browsers
        let hash = 0;
        if (data.length === 0) return '00000000';
        
        for (let i = 0; i < data.length; i++) {
            const char = data.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash | 0; // Convert to 32-bit signed integer
        }
        
        // Convert to positive hex string (8 characters)
        return (hash >>> 0).toString(16).padStart(8, '0');
    }
    
    async function runDownloadTestWithProgress(progressFill, progressText) {
        const chunkSize = 1048576; // 1MB per chunk
        const numberOfChunks = 20; // 20 chunks = 20MB total
        
        const startTime = performance.now();
        let totalDownloadedBytes = 0;
        
        try {
            // Download 20 chunks of 1MB each with progress updates
            for (let i = 0; i < numberOfChunks; i++) {
                if (testAborted) {
                    throw new Error('Test aborted by user');
                }
                
                const chunkStartTime = performance.now();
                const response = await fetch(`/cgi-bin/speedtest.py?test=download&size=${chunkSize}&id=${i + 1}`);
                const chunkEndTime = performance.now();
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText} (chunk ${i + 1})`);
                }
                
                const result = await response.json();
                
                if (result.success) {
                    const data = result.data;
                    const serverHash = result.hash;
                    const calculatedHash = await calculateHash(data);
                    const chunkDuration = (chunkEndTime - chunkStartTime) / 1000;
                    const chunkSpeedMbps = (data.length * 8) / (chunkDuration * 1000000);
                    
                    // Verify hash match
                    const hashMatch = serverHash === calculatedHash;
                    if (!hashMatch) {
                        console.warn(`Hash mismatch for chunk ${i + 1}: server=${serverHash}, calculated=${calculatedHash}`);
                    }
                    
                    totalDownloadedBytes += data.length;
                    
                    // Update progress bar (10% for ping + 90% for download)
                    const progressPercent = 10 + ((i + 1) / numberOfChunks) * 90;
                    if (progressFill) {
                        progressFill.style.width = `${progressPercent}%`;
                    }
                    if (progressText) {
                        progressText.textContent = `Downloading chunk ${i + 1}/${numberOfChunks}... ${(totalDownloadedBytes / (1024*1024)).toFixed(1)} MB (${chunkSpeedMbps.toFixed(1)} Mbps)`;
                    }
                } else {
                    throw new Error(result.message || `Download test failed (chunk ${i + 1})`);
                }
            }
            
            const endTime = performance.now();
            const totalDuration = (endTime - startTime) / 1000; // Convert to seconds
            const averageSpeedMbps = (totalDownloadedBytes * 8) / (totalDuration * 1000000); // Convert to Mbps
            
            return {
                bytes: totalDownloadedBytes,
                duration: totalDuration,
                speedMbps: averageSpeedMbps
            };
        } catch (error) {
            console.error('Download test error:', error);
            throw error;
        }
    }
    
    async function startSpeedTest() {
        if (isTestRunning) return;
        
        isTestRunning = true;
        testAborted = false;
        
        const resultsContainer = document.getElementById('speed-test-results');
        const downloadSpeedEl = document.getElementById('download-speed');
        const pingEl = document.getElementById('ping-value');
        const startButton = document.getElementById('start-speed-test');
        const stopButton = document.getElementById('stop-speed-test');
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');
        const testDurationEl = document.getElementById('test-duration');
        const dataTransferredEl = document.getElementById('data-transferred');

        // Show results container
        if (resultsContainer) {
            resultsContainer.style.display = 'block';
        }
        
        // Reset UI
        if (downloadSpeedEl) downloadSpeedEl.textContent = '--';
        if (pingEl) pingEl.textContent = '--';
        if (testDurationEl) testDurationEl.textContent = '--';
        if (dataTransferredEl) dataTransferredEl.textContent = '--';
        if (progressFill) progressFill.style.width = '0%';
        if (progressText) progressText.textContent = 'Starting...';
        if (startButton) startButton.style.display = 'none';
        if (stopButton) stopButton.style.display = 'inline-flex';

        try {
            // Ping test
            if (progressText) progressText.textContent = 'Testing ping...';
            const pingTime = await runPingTest();
            if (pingEl) pingEl.textContent = String(pingTime);
            if (progressFill) progressFill.style.width = '10%';
            
            // Download test
            if (progressText) progressText.textContent = 'Downloading 20 x 1MB chunks...';
            const downloadData = await runDownloadTestWithProgress(progressFill, progressText);
            
            if (downloadSpeedEl) downloadSpeedEl.textContent = downloadData.speedMbps.toFixed(2);
            if (progressFill) progressFill.style.width = '100%';
            if (progressText) progressText.textContent = 'Test completed';
            
            // Details
            if (testDurationEl) testDurationEl.textContent = `${downloadData.duration.toFixed(2)} s`;
            if (dataTransferredEl) dataTransferredEl.textContent = `${(downloadData.bytes / (1024*1024)).toFixed(2)} MB`;
            
        } catch (error) {
            console.error('Speed test error:', error);
            if (progressText) {
                progressText.textContent = `Error: ${error.message}`;
            }
            
            // Show error status via HTMX
            if (typeof htmx !== 'undefined') {
                const errorHtml = `<div class="status-bar error visible" id="statusBar" hx-swap-oob="true">
                    <span id="statusMessage">Speed test failed: ${error.message}</span>
                    <button class="status-close" onclick="document.getElementById('statusBar').classList.remove('visible')">×</button>
                </div>`;
                // Use HTMX to update status bar
                htmx.ajax('GET', 'about:blank', {
                    swap: 'none',
                    headers: {'X-HTML': errorHtml}
                });
            }
        } finally {
            isTestRunning = false;
            if (startButton) startButton.style.display = 'inline-flex';
            if (stopButton) stopButton.style.display = 'none';
        }
    }

    function stopSpeedTest() {
        if (!isTestRunning) return;
        
        testAborted = true;
        isTestRunning = false;
        
        const startButton = document.getElementById('start-speed-test');
        const stopButton = document.getElementById('stop-speed-test');
        const progressText = document.getElementById('progress-text');
        
        if (progressText) progressText.textContent = 'Test stopped by user';
        if (startButton) startButton.style.display = 'inline-flex';
        if (stopButton) stopButton.style.display = 'none';
    }
    
    // ------------------------------
    // Speed Test Content Management
    // ------------------------------
    
    function initializeSpeedTestContent() {
        // This function will be called when speed test content is shown
        console.log('Speed test content initialized');
    }
    
    // ------------------------------
    // Global Functions
    // ------------------------------
    window.startSpeedTest = startSpeedTest;
    window.stopSpeedTest = stopSpeedTest;
    window.initializeSpeedTestContent = initializeSpeedTestContent;
    
    console.log('Speedtest.js loaded successfully');
})();
