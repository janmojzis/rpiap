(() => {
    'use strict';
    
    // Speed test state
    let isTestRunning = false;
    let testResults = {
        download: null,
        ping: null
    };
    
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
                testResults.ping = pingTime;
                return pingTime;
            } else {
                throw new Error(result.message || 'Ping test failed');
            }
        } catch (error) {
            console.error('Ping test error:', error);
            throw error;
        }
    }
    
    async function runDownloadTest() {
        const chunkSize = 1048576; // 1MB per chunk
        const numberOfChunks = 20; // 20 chunks = 20MB total
        const totalSize = chunkSize * numberOfChunks;
        
        const startTime = performance.now();
        let totalDownloadedBytes = 0;
        let allHashes = [];
        
        try {
            // Download 20 chunks of 1MB each
            for (let i = 0; i < numberOfChunks; i++) {
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
                    allHashes.push({
                        chunk: i + 1,
                        hash: calculatedHash,
                        serverHash: serverHash,
                        hashMatch: hashMatch,
                        size: data.length,
                        duration: chunkDuration,
                        speedMbps: chunkSpeedMbps
                    });
                    
                    console.log(`Chunk ${i + 1}/${numberOfChunks}: ${chunkSpeedMbps.toFixed(2)} Mbps, Hash: ${calculatedHash} (server: ${serverHash}, match: ${hashMatch})`);
                } else {
                    throw new Error(result.message || `Download test failed (chunk ${i + 1})`);
                }
            }
            
            const endTime = performance.now();
            const totalDuration = (endTime - startTime) / 1000; // Convert to seconds
            const averageSpeedMbps = (totalDownloadedBytes * 8) / (totalDuration * 1000000); // Convert to Mbps
            
            testResults.download = {
                bytes: totalDownloadedBytes,
                duration: totalDuration,
                speedMbps: averageSpeedMbps,
                chunks: allHashes,
                totalChunks: numberOfChunks
            };
            
            return {
                bytes: totalDownloadedBytes,
                duration: totalDuration,
                speedMbps: averageSpeedMbps,
                chunks: allHashes,
                totalChunks: numberOfChunks
            };
        } catch (error) {
            console.error('Download test error:', error);
            throw error;
        }
    }
    
    async function runDownloadTestWithProgress(progressFill, progressText) {
        const chunkSize = 1048576; // 1MB per chunk
        const numberOfChunks = 20; // 20 chunks = 20MB total
        
        const startTime = performance.now();
        let totalDownloadedBytes = 0;
        let allHashes = [];
        
        try {
            // Download 20 chunks of 1MB each with progress updates
            for (let i = 0; i < numberOfChunks; i++) {
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
                    allHashes.push({
                        chunk: i + 1,
                        hash: calculatedHash,
                        serverHash: serverHash,
                        hashMatch: hashMatch,
                        size: data.length,
                        duration: chunkDuration,
                        speedMbps: chunkSpeedMbps
                    });
                    
                    // Update progress bar (10% for ping + 90% for download)
                    const progressPercent = 10 + ((i + 1) / numberOfChunks) * 90;
                    if (progressFill) {
                        progressFill.style.width = `${progressPercent}%`;
                    }
                    if (progressText) {
                        progressText.textContent = `Downloading chunk ${i + 1}/${numberOfChunks}... ${(totalDownloadedBytes / (1024*1024)).toFixed(1)} MB (${chunkSpeedMbps.toFixed(1)} Mbps)`;
                    }
                    
                    console.log(`Chunk ${i + 1}/${numberOfChunks}: ${chunkSpeedMbps.toFixed(2)} Mbps, Hash: ${calculatedHash} (server: ${serverHash}, match: ${hashMatch})`);
                } else {
                    throw new Error(result.message || `Download test failed (chunk ${i + 1})`);
                }
            }
            
            const endTime = performance.now();
            const totalDuration = (endTime - startTime) / 1000; // Convert to seconds
            const averageSpeedMbps = (totalDownloadedBytes * 8) / (totalDuration * 1000000); // Convert to Mbps
            
            testResults.download = {
                bytes: totalDownloadedBytes,
                duration: totalDuration,
                speedMbps: averageSpeedMbps,
                chunks: allHashes,
                totalChunks: numberOfChunks
            };
            
            return {
                bytes: totalDownloadedBytes,
                duration: totalDuration,
                speedMbps: averageSpeedMbps,
                chunks: allHashes,
                totalChunks: numberOfChunks
            };
        } catch (error) {
            console.error('Download test error:', error);
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
    
    async function startSpeedTest() {
        if (isTestRunning) return;
        
        isTestRunning = true;
        const resultsContainer = document.getElementById('speed-test-results');
        const downloadSpeedEl = document.getElementById('download-speed');
        const pingEl = document.getElementById('ping-value');
        const startButton = document.getElementById('start-speed-test');
        const stopButton = document.getElementById('stop-speed-test');
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');
        const testDurationEl = document.getElementById('test-duration');
        const dataTransferredEl = document.getElementById('data-transferred');

        // Reset UI
        downloadSpeedEl.textContent = '--';
        pingEl.textContent = '--';
        testDurationEl.textContent = '--';
        dataTransferredEl.textContent = '--';
        if (progressFill) progressFill.style.width = '0%';
        if (progressText) progressText.textContent = 'Starting...';
        if (resultsContainer) resultsContainer.style.display = 'block';
        if (startButton) startButton.style.display = 'none';
        if (stopButton) stopButton.style.display = 'inline-flex';

        const totalChunks = 20;
        const chunkSize = 1048576; // 1MB
        const testStart = performance.now();
        let totalBytes = 0;

        try {
            // Ping
            if (progressText) progressText.textContent = 'Testing ping...';
            const pingTime = await runPingTest();
            pingEl.textContent = String(pingTime);
            if (progressFill) progressFill.style.width = '10%';
            
            // Download 20x1MB with progress updates
            if (progressText) progressText.textContent = 'Downloading 20 x 1MB chunks...';
            const downloadData = await runDownloadTestWithProgress(progressFill, progressText);
            totalBytes = downloadData.bytes;
            const totalDuration = downloadData.duration * 1000;
            downloadSpeedEl.textContent = downloadData.speedMbps.toFixed(2);
            if (progressFill) progressFill.style.width = '100%';
            if (progressText) progressText.textContent = 'Test completed';

            // Details
            testDurationEl.textContent = `${downloadData.duration.toFixed(2)} s`;
            dataTransferredEl.textContent = `${(totalBytes / (1024*1024)).toFixed(2)} MB`;
            
        } catch (error) {
            showStatusMessage('Speed test failed: ' + error.message, 'error', 5000);
        } finally {
            isTestRunning = false;
            if (startButton) startButton.style.display = 'inline-flex';
            if (stopButton) stopButton.style.display = 'none';
        }
    }

    function stopSpeedTest() {
        if (!isTestRunning) return;
        isTestRunning = false;
        showStatusMessage('Speed test stopped', 'warning', 3000);
        const startButton = document.getElementById('start-speed-test');
        const stopButton = document.getElementById('stop-speed-test');
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
