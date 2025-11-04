(() => {
    'use strict';
    
    // ------------------------------
    // Speed Test Content Management
    // ------------------------------
    
    function initializeSpeedTestContent() {
        // Set up HTMX event handlers for speed test
        const resultsContainer = document.getElementById('speed-test-results');
        const startButton = document.getElementById('start-speed-test');
        
        if (resultsContainer && startButton) {
            // Show results container when test starts
            document.body.addEventListener('htmx:afterRequest', function(event) {
                if (event.detail.pathInfo.requestPath.includes('speedtest.py') && 
                    event.detail.pathInfo.requestPath.includes('action=start')) {
                    resultsContainer.style.display = 'block';
                    startButton.style.display = 'none';
                    const stopButton = document.getElementById('stop-speed-test');
                    if (stopButton) stopButton.style.display = 'inline-flex';
                }
            });
        }
        
        console.log('Speed test content initialized');
    }
    
    function stopSpeedTest() {
        // Stop polling and reset UI
        const resultsContainer = document.getElementById('speed-test-results');
        const startButton = document.getElementById('start-speed-test');
        const stopButton = document.getElementById('stop-speed-test');
        
        if (resultsContainer) {
            htmx.trigger(resultsContainer, 'htmx:abort');
            resultsContainer.style.display = 'none';
        }
        if (startButton) startButton.style.display = 'inline-flex';
        if (stopButton) stopButton.style.display = 'none';
    }
    
    // ------------------------------
    // Global Functions
    // ------------------------------
    window.stopSpeedTest = stopSpeedTest;
    window.initializeSpeedTestContent = initializeSpeedTestContent;
    
    console.log('Speedtest.js loaded successfully');
})();
