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
                const response = await fetch(`/cgi-bin/speedtest.py?test=download&size=${chunkSize}`);
                const chunkEndTime = performance.now();
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText} (chunk ${i + 1})`);
                }
                
                const result = await response.json();
                
                if (result.success) {
                    const data = result.data;
                    const hash = await calculateHash(data);
                    const chunkDuration = (chunkEndTime - chunkStartTime) / 1000;
                    const chunkSpeedMbps = (data.length * 8) / (chunkDuration * 1000000);
                    
                    totalDownloadedBytes += data.length;
                    allHashes.push({
                        chunk: i + 1,
                        hash: hash,
                        size: data.length,
                        duration: chunkDuration,
                        speedMbps: chunkSpeedMbps
                    });
                    
                    console.log(`Chunk ${i + 1}/${numberOfChunks}: ${chunkSpeedMbps.toFixed(2)} Mbps, Hash: ${hash}`);
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
    
    async function runFullSpeedTest() {
        if (isTestRunning) {
            showStatusMessage('Speed test is already running', 'error', 3000);
            return;
        }
        
        isTestRunning = true;
        const resultsContainer = document.getElementById('speedtest-results');
        const pingResult = document.getElementById('ping-result');
        const downloadResult = document.getElementById('download-result');
        const testButton = document.getElementById('run-speedtest-btn');
        
        // Reset results
        testResults = { download: null, ping: null };
        
        // Update UI
        if (testButton) {
            testButton.disabled = true;
            testButton.textContent = 'Running Test...';
        }
        
        if (resultsContainer) {
            resultsContainer.style.display = 'block';
        }
        
        try {
            // Run ping test
            if (pingResult) {
                pingResult.innerHTML = '<div class="test-status">Testing ping...</div>';
            }
            
            const pingTime = await runPingTest();
            if (pingResult) {
                pingResult.innerHTML = `
                    <div class="test-result">
                        <span class="test-label">Ping:</span>
                        <span class="test-value">${pingTime} ms</span>
                    </div>
                `;
            }
            
            // Run download test
            if (downloadResult) {
                downloadResult.innerHTML = '<div class="test-status">Testing download speed (20 x 1MB chunks)...</div>';
            }
            
            const downloadData = await runDownloadTest();
            if (downloadResult) {
                // Create chunks summary
                let chunksHtml = '';
                if (downloadData.chunks && downloadData.chunks.length > 0) {
                    chunksHtml = '<div class="chunks-summary">';
                    chunksHtml += '<h4>Chunk Details:</h4>';
                    chunksHtml += '<div class="chunks-grid">';
                    
                    downloadData.chunks.forEach((chunk, index) => {
                        chunksHtml += `
                            <div class="chunk-item">
                                <span class="chunk-number">Chunk ${chunk.chunk}:</span>
                                <span class="chunk-speed">${chunk.speedMbps.toFixed(2)} Mbps</span>
                                <span class="chunk-hash">${chunk.hash}</span>
                            </div>
                        `;
                    });
                    
                    chunksHtml += '</div></div>';
                }
                
                downloadResult.innerHTML = `
                    <div class="test-result">
                        <span class="test-label">Average Download Speed:</span>
                        <span class="test-value">${downloadData.speedMbps.toFixed(2)} Mbps</span>
                    </div>
                    <div class="test-result">
                        <span class="test-label">Total Data Size:</span>
                        <span class="test-value">${(downloadData.bytes / (1024 * 1024)).toFixed(2)} MB</span>
                    </div>
                    <div class="test-result">
                        <span class="test-label">Total Duration:</span>
                        <span class="test-value">${downloadData.duration.toFixed(2)} s</span>
                    </div>
                    <div class="test-result">
                        <span class="test-label">Chunks Tested:</span>
                        <span class="test-value">${downloadData.totalChunks} x 1MB</span>
                    </div>
                    ${chunksHtml}
                `;
            }
            
            showStatusMessage('Speed test completed successfully', 'success', 3000);
            
        } catch (error) {
            console.error('Speed test error:', error);
            showStatusMessage('Speed test failed: ' + error.message, 'error', 5000);
            
            // Show error in results
            if (pingResult && !testResults.ping) {
                pingResult.innerHTML = '<div class="test-error">Ping test failed</div>';
            }
            if (downloadResult && !testResults.download) {
                downloadResult.innerHTML = '<div class="test-error">Download test failed</div>';
            }
        } finally {
            isTestRunning = false;
            if (testButton) {
                testButton.disabled = false;
                testButton.textContent = 'Run Speed Test';
            }
        }
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
    window.runFullSpeedTest = runFullSpeedTest;
    window.initializeSpeedTestContent = initializeSpeedTestContent;
    
    console.log('Speedtest.js loaded successfully');
})();
