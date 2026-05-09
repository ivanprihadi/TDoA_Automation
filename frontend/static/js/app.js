// ==================== GLOBAL STATE ====================  

let currentResult = null;  
let currentConfig = null;  
let allFiles = [];  
let processingInProgress = false;  

// ==================== INITIALIZATION ====================  

document.addEventListener('DOMContentLoaded', function() {  
    console.log('🚀 TDOA Application Initialized');  
    
    // Load all data  
    loadConfig();  
    loadReceivers();  
    loadFiles();  
    loadMaps();  
    refreshStatus();  
    
    // Update time every second  
    setInterval(updateFooterTime, 1000);  
    
    // Auto-refresh files every 30 seconds  
    setInterval(loadFiles, 30000);  
    setInterval(refreshStatus, 60000);  
    
    // Setup event listeners  
    setupEventListeners();  
});  

// ==================== EVENT LISTENERS ====================  

function setupEventListeners() {  
    // Enter key untuk submit form  
    document.getElementById('bandwidth')?.addEventListener('keypress', function(e) {  
        if (e.key === 'Enter') processFiles();  
    });  
    
    // File selection changes  
    ['file1', 'file2', 'file3'].forEach(id => {  
        document.getElementById(id)?.addEventListener('change', updateFileSelection);  
    });  
}  

// ==================== TAB SWITCHING ====================  

function switchTab(tabName) {  
    console.log(`Switching to tab: ${tabName}`);  
    
    // Hide all tabs  
    document.querySelectorAll('.tab-content').forEach(tab => {  
        tab.classList.remove('active');  
    });  
    
    // Remove active class from all buttons  
    document.querySelectorAll('.nav-btn').forEach(btn => {  
        btn.classList.remove('active');  
    });  
    
    // Show selected tab  
    const selectedTab = document.getElementById(tabName);  
    if (selectedTab) {  
        selectedTab.classList.add('active');  
    }  
    
    // Mark button as active  
    event.target.closest('.nav-btn')?.classList.add('active');  
    
    // Load specific content  
    if (tabName === 'results') {  
        loadMaps();  
    } else if (tabName === 'configuration') {  
        loadConfig();  
    }  
}  

// ==================== NAVIGATION SHORTCUTS ====================  

function goToProcessing() {  
    const btn = document.querySelector('[onclick*="processing"]');  
    if (btn) {  
        btn.click();  
    } else {  
        switchTab('processing');  
    }  
}  

function goToResults() {  
    const btn = document.querySelector('[onclick*="results"]');  
    if (btn) {  
        btn.click();  
    } else {  
        switchTab('results');  
    }  
}  

// ==================== API CALLS ====================  

async function apiCall(endpoint, method = 'GET', data = null) {  
    try {  
        const options = {  
            method: method,  
            headers: { 'Content-Type': 'application/json' }  
        };  
        
        if (data) {  
            options.body = JSON.stringify(data);  
        }  
        
        const response = await fetch(endpoint, options);  
        
        if (!response.ok) {  
            throw new Error(`API Error: ${response.status}`);  
        }  
        
        return await response.json();  
        
    } catch (error) {  
        console.error(`API call failed: ${endpoint}`, error);  
        showToast(`Error: ${error.message}`, 'error');  
        throw error;  
    }  
}  

// ==================== CONFIG & STATUS ====================  

async function loadConfig() {  
    try {  
        const response = await apiCall('/api/config');  
        
        if (response.status === 'success') {  
            currentConfig = response.config;  
            
            // Update UI  
            document.getElementById('app-name').textContent =   
                currentConfig.application?.name || 'TDOA System';  
            document.getElementById('app-version').textContent =   
                'v' + (currentConfig.application?.version || '1.0.0');  
            document.getElementById('app-env').textContent =   
                currentConfig.application?.environment || 'Production';  
            
            // Display config JSON  
            const configDisplay = document.getElementById('config-display');  
            if (configDisplay) {  
                configDisplay.textContent = JSON.stringify(currentConfig, null, 2);  
            }  
            
            // Update configuration details  
            updateConfigDetails();  
        }  
    } catch (error) {  
        console.error('Failed to load config:', error);  
    }  
}  

async function refreshStatus() {  
    try {  
        const response = await apiCall('/api/status');  
        
        if (response.status === 'success') {  
            const status = response.data;  
            
            // Update status indicators  
            const statusEl = document.getElementById('system-status');  
            if (statusEl) {  
                statusEl.textContent = '● System: Healthy';  
                statusEl.className = 'status healthy';  
            }  
            
            // Update file and map counts  
            loadFiles();  
            loadMaps();  
        }  
    } catch (error) {  
        console.error('Failed to get status:', error);  
        const statusEl = document.getElementById('system-status');  
        if (statusEl) {  
            statusEl.textContent = '● System: Offline';  
            statusEl.className = 'status error';  
        }  
    }  
}  

async function loadReceivers() {  
    try {  
        const response = await apiCall('/api/receivers');  
        
        if (response.status === 'success') {  
            const receivers = response.receivers;  
            document.getElementById('receiver-count').textContent = receivers.length;  
            
            // Display receivers in status  
            const receiverList = document.getElementById('receiver-status-list');  
            if (receiverList) {  
                receiverList.innerHTML = '';  
                
                receivers.forEach((rx, index) => {  
                    const item = document.createElement('div');  
                    item.className = 'receiver-item';  
                    item.innerHTML = `  
                        <strong>${rx.name || 'RX' + (index + 1)}</strong>  
                        <span>📍 ${rx.latitude?.toFixed(6)} , ${rx.longitude?.toFixed(6)}</span>  
                        <span>🖥️ ${rx.host || rx.hostname}</span>  
                        <span class="status-badge success">● Connected</span>  
                    `;  
                    receiverList.appendChild(item);  
                });  
            }  
            
            // Display in configuration  
            const configList = document.getElementById('receiver-config-list');  
            if (configList) {  
                configList.innerHTML = '';  
                
                receivers.forEach((rx, index) => {  
                    const card = document.createElement('div');  
                    card.className = 'card';  
                    card.innerHTML = `  
                        <h4>${rx.name || 'Receiver ' + (index + 1)}</h4>  
                        <div class="info-group">  
                            <label>Host:</label>  
                            <span style="font-size: 12px;">${rx.host || rx.hostname}</span>  
                        </div>  
                        <div class="info-group">  
                            <label>Lat/Lon:</label>  
                            <span style="font-size: 12px;">${rx.latitude?.toFixed(6)}, ${rx.longitude?.toFixed(6)}</span>  
                        </div>  
                        <div class="info-group">  
                            <label>Status:</label>  
                            <span class="badge badge-success">Active</span>  
                        </div>  
                    `;  
                    configList.appendChild(card);  
                });  
            }  
        }  
    } catch (error) {  
        console.error('Failed to load receivers:', error);  
    }  
}  

async function loadFiles() {  
    try {  
        const response = await apiCall('/api/files');  
        
        if (response.status === 'success') {  
            const files = response.files;  
            allFiles = files;  
            
            document.getElementById('file-count').textContent = files.length;  
            
            // Populate dropdowns  
            ['file1', 'file2', 'file3'].forEach(id => {  
                const select = document.getElementById(id);  
                if (select) {  
                    const currentValue = select.value;  
                    select.innerHTML = '<option value="">-- Select File --</option>';  
                    
                    files.forEach(file => {  
                        const option = document.createElement('option');  
                        option.value = response.directory + '/' + file;  
                        option.textContent = file;  
                        select.appendChild(option);  
                    });  
                    
                    // Restore previous value if still available  
                    if (files.some(f => `${response.directory}/${f}` === currentValue)) {  
                        select.value = currentValue;  
                    }  
                }  
            });  
        }  
    } catch (error) {  
        console.error('Failed to load files:', error);  
    }  
}  

async function loadMaps() {  
    try {  
        const response = await apiCall('/api/maps');  
        
        if (response.status === 'success') {  
            const maps = response.maps;  
            document.getElementById('map-count').textContent = maps.length;  
            
            const mapsList = document.getElementById('maps-list');  
            if (mapsList) {  
                mapsList.innerHTML = '';  
                
                if (maps.length === 0) {  
                    mapsList.innerHTML = '<p class="text-muted"><i class="fas fa-inbox"></i> No maps generated yet</p>';  
                    return;  
                }  
                
                maps.forEach(map => {  
                    const card = document.createElement('div');  
                    card.className = 'maps-card';  
                    card.innerHTML = `  
                        <div class="maps-card-thumbnail">  
                            <i class="fas fa-map" style="font-size: 40px; color: #ddd;"></i>  
                        </div>  
                        <h4>📍 ${map.replace('.html', '').substring(0, 20)}</h4>  
                        <p>${new Date().toLocaleDateString()}</p>  
                        <div class="button-group">  
                            <button class="btn-secondary btn-sm" onclick="openMap('${map}')">  
                                <i class="fas fa-eye"></i> View  
                            </button>  
                            <button class="btn-secondary btn-sm" onclick="downloadMap('${map}')">  
                                <i class="fas fa-download"></i> Download  
                            </button>  
                        </div>  
                    `;  
                    mapsList.appendChild(card);  
                });  
            }  
        }  
    } catch (error) {  
        console.error('Failed to load maps:', error);  
    }  
}  

// ==================== PROCESSING ====================  

function updateFileSelection() {  
    const file1 = document.getElementById('file1').value;  
    const file2 = document.getElementById('file2').value;  
    const file3 = document.getElementById('file3').value;  
    
    const btn = document.getElementById('process-btn');  
    if (btn) {  
        btn.disabled = !(file1 && file2 && file3);  
    }  
}  

async function processFiles() {  
    const file1 = document.getElementById('file1').value;  
    const file2 = document.getElementById('file2').value;  
    const file3 = document.getElementById('file3').value;  
    
    // Validation  
    if (!file1 || !file2 || !file3) {  
        showToast('Please select all 3 files', 'error');  
        return;  
    }  
    
    // Check if already processing  
    if (processingInProgress) {  
        showToast('Processing already in progress', 'warning');  
        return;  
    }  
    
    // Get parameters  
    const params = {  
        file1: file1,  
        file2: file2,  
        file3: file3,  
        bandwidth_khz: parseInt(document.getElementById('bandwidth').value) || 40,  
        correlation_type: document.getElementById('corr-type').value || 'dphase',  
        heatmap_resolution: parseInt(document.getElementById('heatmap-res').value) || 200,  
        heatmap_threshold: parseFloat(document.getElementById('heatmap-thresh').value) || 0.70  
    };  
    
    console.log('Processing with params:', params);  
    
    // Disable button and show progress  
    const btn = document.getElementById('process-btn');  
    btn.disabled = true;  
    processingInProgress = true;  
    
    const progressSection = document.getElementById('progress-section');  
    progressSection.style.display = 'block';  
    
    // Reset progress  
    updateProgress(0);  
    addLogEntry('Starting TDOA processing...', 'info');  
    
    // Simulate progress  
    let progress = 0;  
    const progressInterval = setInterval(() => {  
        progress += Math.random() * 20;  
        if (progress > 90) progress = 90;  
        updateProgress(progress);  
    }, 500);  
    
    try {  
        // Send request  
        const response = await apiCall('/api/process', 'POST', params);  
        
        clearInterval(progressInterval);  
        updateProgress(100);  
        
        if (response.status === 'success') {  
            currentResult = response.result;  
            addLogEntry('✓ Processing completed successfully!', 'success');  
            
            // Display result summary  
            displayResultSummary(response.result);  
            
            showToast('Processing completed!', 'success');  
            
            // Refresh maps  
            setTimeout(() => {  
                loadMaps();  
            }, 1000);  
            
        } else {  
            addLogEntry('✗ Processing failed: ' + response.message, 'error');  
            showToast('Error: ' + response.message, 'error');  
        }  
        
    } catch (error) {  
        clearInterval(progressInterval);  
        addLogEntry('✗ Error: ' + error.message, 'error');  
        showToast('Processing error: ' + error.message, 'error');  
    } finally {  
        btn.disabled = false;  
        processingInProgress = false;  
    }  
}  

function updateProgress(percentage) {  
    const fill = document.getElementById('progress-fill');  
    const text = document.getElementById('progress-text');  
    
    if (fill) fill.style.width = percentage + '%';  
    if (text) text.textContent = `Processing... ${Math.round(percentage)}%`;  
}  

function addLogEntry(message, type = 'info') {  
    const logViewer = document.getElementById('processing-log');  
    if (logViewer) {  
        const entry = document.createElement('div');  
        entry.className = `log-entry ${type}`;  
        entry.innerHTML = `[${new Date().toLocaleTimeString()}] ${message}`;  
        logViewer.appendChild(entry);  
        logViewer.scrollTop = logViewer.scrollHeight;  
    }  
}  

function displayResultSummary(result) {  
    const summary = document.getElementById('result-summary');  
    
    if (!result || !result.tx_location) {  
        summary.innerHTML = '<p class="text-muted">No result data</p>';  
        return;  
    }  
    
    const txLoc = result.tx_location || {};  
    const tdoa = result.tdoa_results || {};  
    
    summary.innerHTML = `  
        <div class="grid-2">  
            <div>  
                <h3 style="margin-bottom: 15px;">📍 Estimated TX Location</h3>  
                <div class="info-group">  
                    <label>Latitude:</label>  
                    <span>${(txLoc.latitude || 0).toFixed(8)}</span>  
                </div>  
                <div class="info-group">  
                    <label>Longitude:</label>  
                    <span>${(txLoc.longitude || 0).toFixed(8)}</span>  
                </div>  
                <div class="info-group">  
                    <label>Accuracy:</label>  
                    <span>${(result.accuracy || 'N/A')}</span>  
                </div>  
            </div>  
            <div>  
                <h3 style="margin-bottom: 15px;">📊 Processing Metadata</h3>  
                <div class="info-group">  
                    <label>Processing Time:</label>  
                    <span>${(result.processing_time || 'N/A')}s</span>  
                </div>  
                <div class="info-group">  
                    <label>Signal Correlation:</label>  
                    <span>${(result.correlation_quality || 'N/A')}</span>  
                </div>  
                <div class="info-group">  
                    <label>Generated Map:</label>  
                    <span><a href="#" onclick="openMap('${result.html_map}')" style="color: var(--primary);">${result.html_map}</a></span>  
                </div>  
            </div>  
        </div>  
    `;  
}  

// ==================== MAP OPERATIONS ====================  

function openMap(mapFilename) {  
    fetch(`/api/download-map/${mapFilename}`)  
        .then(res => res.blob())  
        .then(blob => {  
            const url = window.URL.createObjectURL(blob);  
            window.open(url, '_blank');  
        })  
        .catch(err => {  
            console.error('Error opening map:', err);  
            showToast('Failed to open map', 'error');  
        });  
}  

function downloadMap(mapFilename) {  
    const link = document.createElement('a');  
    link.href = `/api/download-map/${mapFilename}`;  
    link.download = mapFilename;  
    link.click();  
}  

// ==================== EXPORT OPTIONS ====================  

function exportAsCSV() {  
    if (!currentResult) {  
        showToast('No results to export', 'warning');  
        return;  
    }  
    
    showToast('Exporting as CSV...', 'info');  
    // Implementation untuk CSV export  
}  

function exportAsJSON() {  
    if (!currentResult) {  
        showToast('No results to export', 'warning');  
        return;  
    }  
    
    const json = JSON.stringify(currentResult, null, 2);  
    const blob = new Blob([json], { type: 'application/json' });  
    const url = window.URL
    // ==================== UTILITY FUNCTIONS ====================

function updateConfigDetails() {
    if (!currentConfig) return;
    
    // Sample Rate
    const sampleRate = currentConfig.signal_processing?.sample_rate || 2048000;
    document.getElementById('config-sample-rate').textContent = 
        `${(sampleRate / 1e6).toFixed(2)} MSPS`;
    
    // Bandwidth
    const bandwidth = currentConfig.signal_processing?.bandwidth_khz || 40;
    document.getElementById('config-bandwidth').textContent = `${bandwidth} kHz`;
    
    // Directories
    document.getElementById('config-data-dir').textContent = 
        currentConfig.output?.data_dir || './output/recorded_data';
    document.getElementById('config-maps-dir').textContent = 
        currentConfig.output?.map_dir || './output/maps';
}

function printReport() {
    if (!currentResult) {
        showToast('No results to print', 'warning');
        return;
    }
    
    const printWindow = window.open('', 'TDOA Report');
    printWindow.document.write(`
        <html>
        <head>
            <title>TDOA Localization Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #667eea; }
                .section { margin: 20px 0; }
                table { width: 100%; border-collapse: collapse; }
                th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #f5f5f5; }
            </style>
        </head>
        <body>
            <h1>TDOA Localization Report</h1>
            <div class="section">
                <h2>TX Location Estimate</h2>
                <table>
                    <tr>
                        <th>Parameter</th>
                        <th>Value</th>
                    </tr>
                    <tr>
                        <td>Latitude</td>
                        <td>${currentResult.tx_location?.latitude || 'N/A'}</td>
                    </tr>
                    <tr>
                        <td>Longitude</td>
                        <td>${currentResult.tx_location?.longitude || 'N/A'}</td>
                    </tr>
                    <tr>
                        <td>Accuracy</td>
                        <td>${currentResult.accuracy || 'N/A'}</td>
                    </tr>
                </table>
            </div>
            <p><small>Generated: ${new Date().toLocaleString()}</small></p>
            <script>
                window.print();
                window.close();
            </script>
        </body>
        </html>
    `);
    printWindow.document.close();
}

function downloadResults() {
    if (allFiles.length === 0) {
        showToast('No results available to download', 'warning');
        return;
    }
    
    const link = document.createElement('a');
    link.href = '/api/download-results';
    link.download = `tdoa-results-${new Date().toISOString().split('T')[0]}.zip`;
    link.click();
    
    showToast('Download started...', 'info');
}

function updateFooterTime() {
    const footerTime = document.getElementById('footer-time');
    if (footerTime) {
        const now = new Date();
        footerTime.textContent = now.toLocaleTimeString();
    }
}

// ==================== TOAST NOTIFICATIONS ====================

function showToast(message, type = 'info', duration = 3000) {
    const toast = document.getElementById('toast');
    
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, duration);
}

// ==================== BATCH PROCESSING ====================

async function startBatchProcessing() {
    const patternInput = prompt('Enter file pattern (e.g., "triplet_"):');
    if (!patternInput) return;
    
    const count = parseInt(prompt('Number of triplets to process:'));
    if (!count || count < 1) return;
    
    showToast(`Starting batch processing of ${count} triplets...`, 'info');
    
    try {
        const response = await apiCall('/api/batch-process', 'POST', {
            pattern: patternInput,
            count: count
        });
        
        if (response.status === 'success') {
            showToast('Batch processing started!', 'success');
            
            // Monitor progress
            monitorBatchProgress(response.job_id);
        } else {
            showToast('Error: ' + response.message, 'error');
        }
    } catch (error) {
        showToast('Batch processing error: ' + error.message, 'error');
    }
}

async function monitorBatchProgress(jobId) {
    const checkProgress = async () => {
        try {
            const response = await apiCall(`/api/batch-progress/${jobId}`);
            
            if (response.status === 'success') {
                const progress = response.data;
                console.log(`Progress: ${progress.completed}/${progress.total}`);
                
                if (progress.completed < progress.total) {
                    // Continue monitoring
                    setTimeout(checkProgress, 1000);
                } else {
                    showToast('Batch processing completed!', 'success');
                    loadMaps();
                }
            }
        } catch (error) {
            console.error('Failed to get batch progress:', error);
        }
    };
    
    checkProgress();
}

// ==================== KEYBOARD SHORTCUTS ====================

document.addEventListener('keydown', function(event) {
    // Ctrl+P untuk print
    if (event.ctrlKey && event.key === 'p') {
        event.preventDefault();
        printReport();
    }
    
    // Ctrl+D untuk download
    if (event.ctrlKey && event.key === 'd') {
        event.preventDefault();
        downloadResults();
    }
    
    // Ctrl+R untuk refresh
    if (event.ctrlKey && event.key === 'r') {
        event.preventDefault();
        location.reload();
    }
});

// ==================== THEME SWITCHER ====================

function toggleTheme() {
    const root = document.documentElement;
    const isDark = root.style.filter === 'invert(1)';
    
    if (isDark) {
        root.style.filter = 'invert(0)';
        localStorage.setItem('theme', 'light');
    } else {
        root.style.filter = 'invert(1)';
        localStorage.setItem('theme', 'dark');
    }
}

// Load saved theme
window.addEventListener('load', function() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.documentElement.style.filter = 'invert(1)';
    }
});

// ==================== RESPONSIVE UTILITIES ====================

function isMobile() {
    return window.innerWidth <= 768;
}

function isTablet() {
    return window.innerWidth > 768 && window.innerWidth <= 1024;
}

// ==================== ERROR HANDLING ====================

window.addEventListener('error', function(event) {
    console.error('Global error:', event.error);
    showToast('An unexpected error occurred', 'error');
});

window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    showToast('Error: ' + event.reason, 'error');
});

// ==================== AUTO-SAVE FUNCTIONALITY ====================

function autoSaveFormState() {
    const formElements = ['bandwidth', 'corr-type', 'smoothing', 'heatmap-res', 'heatmap-thresh'];
    
    formElements.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            // Save on change
            element.addEventListener('change', () => {
                const state = {};
                formElements.forEach(eid => {
                    const el = document.getElementById(eid);
                    if (el) state[eid] = el.value;
                });
                localStorage.setItem('processingState', JSON.stringify(state));
            });
            
            // Restore on load
            const saved = JSON.parse(localStorage.getItem('processingState') || '{}');
            if (saved[id]) element.value = saved[id];
        }
    });
}

autoSaveFormState();

// ==================== ANALYTICS (Optional) ====================

function trackEvent(eventName, eventData = {}) {
    console.log(`📊 Event: ${eventName}`, eventData);
    // Implement analytics here (Google Analytics, Mixpanel, etc.)
}

// Track tab switches
document.addEventListener('click', function(e) {
    if (e.target.closest('.nav-btn')) {
        const tabName = e.target.closest('.nav-btn').textContent.trim();
        trackEvent('tab_switch', { tab: tabName });
    }
});

// Track processing
const originalProcess = window.processFiles;
window.processFiles = function() {
    trackEvent('process_start', { 
        bandwidth: document.getElementById('bandwidth').value,
        correlation_type: document.getElementById('corr-type').value
    });
    return originalProcess.call(this);
};

// ==================== CONSOLE HELPERS ====================

console.log('%c🛰️ TDOA Localization System', 'font-size: 20px; color: #667eea; font-weight: bold;');
console.log('%cVersion 1.0.0 | Ready for processing', 'color: #999;');
console.log('%cAvailable APIs:', 'color: #667eea; font-weight: bold;');
console.log('  - apiCall(endpoint, method, data)');
console.log('  - processFiles()');
console.log('  - loadMaps()');
console.log('  - showToast(message, type)');
}