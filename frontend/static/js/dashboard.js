/**
 * DASHBOARD MANAGER
 * dashboard.js - Menangani real-time updates dan dashboard logic
 */

let resultsPollInterval = null;
let isLoadingResults = false;

const DashboardManager = {
    /**
     * Initialize dashboard dengan data
     */
    init() {
        console.log('✓ Dashboard Manager initialized');
        this.setupCharts();
        this.startAutoRefresh();
        this.setupEventListeners();
    },
    
    /**
     * Setup dashboard charts
     */
    setupCharts() {
        // Chart untuk Signal Quality
        const signalCanvas = document.getElementById('signal-quality-chart');
        if (signalCanvas) {
            ChartUtils.createLineChart(
                signalCanvas,
                'Signal Strength (dBm)',
                [-65, -64, -66, -63, -65, -67],
                { responsive: true }
            );
        }
        
        // Chart untuk TDOA Distribution
        const tdoaCanvas = document.getElementById('tdoa-dist-chart');
        if (tdoaCanvas) {
            ChartUtils.createBarChart(
                tdoaCanvas,
                ['RX1-RX2', 'RX1-RX3', 'RX2-RX3'],
                [{
                    label: 'TDOA (nanoseconds)',
                    data: [-2.1, -0.9, 1.2]
                }]
            );
        }
        
        // Chart untuk Accuracy Over Loops
        const accuracyCanvas = document.getElementById('accuracy-chart');
        if (accuracyCanvas) {
            ChartUtils.createLineChart(
                accuracyCanvas,
                'Localization Accuracy (meters)',
                [45, 42, 47, 44, 43]
            );
        }
    },
    
    /**
     * Start auto-refresh interval
     */
    startAutoRefresh() {
        setInterval(() => {
            this.refreshDashboard();
        }, 30000);  // Refresh setiap 30 detik
    },
    
    /**
     * Refresh dashboard data
     */
    async refreshDashboard() {
        try {
            const response = await apiCall('/api/dashboard-stats');
            
            if (response.status === 'success') {
                this.updateStats(response.data);
                this.updateCharts(response.data);
            }
        } catch (error) {
            console.error('Failed to refresh dashboard:', error);
        }
    },
    
    /**
     * Update stat cards
     */
    updateStats(data) {
        // Update receiver count
        const rxCount = document.getElementById('receiver-count');
        if (rxCount) rxCount.textContent = data.receiver_count || 3;
        
        // Update file count
        const fileCount = document.getElementById('file-count');
        if (fileCount) fileCount.textContent = data.file_count || 0;
        
        // Update map count
        const mapCount = document.getElementById('map-count');
        if (mapCount) mapCount.textContent = data.map_count || 0;
        
        // Update system status
        const systemStatus = document.getElementById('system-status');
        if (systemStatus) {
            systemStatus.textContent = data.system_healthy ? '● System: Healthy' : '● System: Warning';
            systemStatus.className = data.system_healthy ? 'status healthy' : 'status warning';
        }
    },
    
    /**
     * Update semua charts dengan data terbaru
     */
    updateCharts(data) {
        console.log('Updating charts with:', data);
        // Implementation untuk update chart data
        // (Chart.js instance sudah ada di setupCharts)
    },
    
    /**
     * Setup event listeners dashboard
     */
    setupEventListeners() {
        console.log('Setting up event listeners...');
        
        // Make sure elements exist before attaching listeners
        const processingBtn = document.querySelector('button[onclick*="processINGStartProcessing"]') ||
                            document.querySelector('button[onclick*="startProcessing"]') ||
                            document.getElementById('start-processing-btn');
        
        const resultsBtn = document.querySelector('button[onclick*="goToResults"]') ||
                        document.querySelector('button[onclick*="viewResults"]') ||
                        document.getElementById('view-results-btn');
        
        if (processingBtn) {
            processingBtn.addEventListener('click', () => {
                console.log('Start Processing clicked');
                switchTab('processing');
            });
        }
        
        if (resultsBtn) {
            resultsBtn.addEventListener('click', () => {
                console.log('View Results clicked');
                switchTab('results');
            });
        }
        
        console.log('✓ Event listeners setup complete');
    }
};

// Safe initialization on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('✓ DOM Content Loaded');
    
    // Wait for elements to be fully rendered
    setTimeout(() => {
        try {
            DashboardManager.setupEventListeners();
        } catch (error) {
            console.warn('Warning setting up listeners:', error);
        }
    }, 500);
    
    // Initialize other components
    initUploadButton();
    initTabNavigation();
    initAutoLoadResults();
});

// ==================== PROCESSING DATA FUNCTIONS ====================

/**
 * Load imported files list
 */
    async function loadImportedFiles() {
        try {
            const response = await API.getImportedFiles();
            
            if (!response.success) {
                showToast('Failed to load imported files', 'error');
                return;
            }
            
            const files = response.data.files || [];
            const listDiv = document.getElementById('imported-files-list');
            
            if (files.length === 0) {
                listDiv.innerHTML = '<p style="color: #999;">No files imported yet. Upload a file above.</p>';
                document.getElementById('file-selection-list').innerHTML = '<p style="color: #999;">Load imported files first</p>';
                return;
            }
            
            // Display files
            listDiv.innerHTML = files.map(f => `
                <div class="receiver-item">
                    <strong>${f.filename}</strong>
                    <small>Size: ${StringUtils.formatBytes(f.size_bytes || 0)}</small>
                    <small>Loaded: ${f.loaded ? '✓ Yes' : '✗ No'}</small>
                    <small>Processing: ${f.processed ? '✓ Yes' : '✗ No'}</small>
                    <button class="btn btn-secondary btn-sm" onclick="deleteImportedFile('${f.file_id}')" 
                            style="margin-top: 0.5rem; width: 100%;">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </div>
            `).join('');
            
            // Create checkboxes for file selection
            const selectionDiv = document.getElementById('file-selection-list');
            selectionDiv.innerHTML = files.map(f => `
                <div style="margin-bottom: 0.5rem;">
                    <label style="display: flex; align-items: center; gap: 0.5rem; margin: 0;">
                        <input type="checkbox" class="file-selector" value="${f.file_id}" />
                        <span>${f.filename}</span>
                    </label>
                </div>
            `).join('');
            
        } catch (error) {
            console.error('Error loading files:', error);
            showToast('Error loading files', 'error');
        }
    }

    /**
     * Upload IQ file
     */
    async function uploadIQFile() {
        const fileInput = document.getElementById('iq-file-input');
        const sampleRateInput = document.getElementById('sample-rate-input');
        
        if (!fileInput.files || fileInput.files.length === 0) {
            showToast('Please select a file', 'warning');
            return;
        }
        
        const file = fileInput.files[0];
        const sampleRate = parseFloat(sampleRateInput.value) * 1e6;
        
        if (isNaN(sampleRate) || sampleRate <= 0) {
            showToast('Invalid sample rate', 'error');
            return;
        }
        
        showToast('Uploading file...', 'info');
        
        try {
            const response = await API.importFile(file, sampleRate);
            
            if (!response.success) {
                showToast(`Error: ${response.error}`, 'error');
                return;
            }
            
            showToast(`File uploaded: ${response.data.filename}`, 'success');
            fileInput.value = '';
            
            // Reload files list
            await loadImportedFiles();
            
        } catch (error) {
            console.error('Upload error:', error);
            showToast('Upload failed', 'error');
        }
    }

    /**
     * Delete imported file
     */
    async function deleteImportedFile(fileId) {
        if (!confirm('Delete this file? This cannot be undone.')) return;
        
        try {
            const response = await API.deleteFile(fileId);
            
            if (response.success) {
                showToast('File deleted', 'success');
                await loadImportedFiles();
            } else {
                showToast(`Error: ${response.error}`, 'error');
            }
            
        } catch (error) {
            console.error('Delete error:', error);
            showToast('Delete failed', 'error');
        }
    }

    /**
     * Process TDOA dengan multiple files
     */
    async function processTDOA() {
        // Get selected files
        const selectedCheckboxes = document.querySelectorAll('.file-selector:checked');
        const selectedFiles = Array.from(selectedCheckboxes).map(cb => cb.value);
        
        const refFreq = parseFloat(document.getElementById('ref-freq-input').value);
        
        if (selectedFiles.length < 2) {
            showToast('Select at least 2 files for TDOA', 'warning');
            return;
        }
        
        if (isNaN(refFreq) || refFreq < 87 || refFreq > 108) {
            showToast('Reference frequency must be between 87-108 MHz', 'error');
            return;
        }
        
        console.log('Starting TDOA processing:', selectedFiles, refFreq);
        showToast('Starting TDOA processing...', 'info');
        
        try {
            const response = await API.processMultipleFiles(selectedFiles, refFreq);
            
            if (!response.success) {
                showToast(`Error: ${response.error}`, 'error');
                return;
            }
            
            // Show progress container
            const progressContainer = document.getElementById('processing-progress-container');
            if (progressContainer) {
                progressContainer.style.display = 'block';
            }
            
            // Store job ID untuk polling
            window.currentProcessingJobId = response.data.session_id || response.data.job_id;
            
            // Start polling
            pollProcessingStatus(window.currentProcessingJobId);
            
        } catch (error) {
            console.error('Processing error:', error);
            showToast('Processing failed', 'error');
        }
    }

    /**
     * Poll processing status
     */
    async function pollProcessingStatus(jobId, attempt = 0) {
        if (attempt > 300) {  // Max 5 minutes
            showToast('Processing timeout', 'error');
            return;
        }
        
        try {
            const response = await API.getProcessingStatus(jobId);
            
            if (!response.success) {
                setTimeout(() => pollProcessingStatus(jobId, attempt + 1), 2000);
                return;
            }
            
            const data = response.data;
            
            // Update progress
            const progressFill = document.getElementById('processing-progress-fill');
            const progressText = document.getElementById('processing-progress-text');
            
            if (progressFill) {
                progressFill.style.width = data.progress + '%';
                progressFill.textContent = Math.round(data.progress) + '%';
            }
            
            if (progressText) {
                progressText.textContent = data.step || 'Processing...';
            }
            
            // Check status
            if (data.status === 'COMPLETED' || data.status === 'completed') {
                showToast('TDOA processing completed!', 'success');
                
                // Display results
                const statusDisplay = document.getElementById('processing-status-display');
                if (statusDisplay) {
                    statusDisplay.style.display = 'block';
                    statusDisplay.className = 'status-box success';
                    statusDisplay.textContent = 
                        `✓ Processing Completed!\n` +
                        `Location: ${(data.result?.location?.latitude || 0).toFixed(4)}, ` +
                        `${(data.result?.location?.longitude || 0).toFixed(4)}\n` +
                        `Accuracy: ${(data.result?.location?.accuracy_meters || 0).toFixed(1)}m\n` +
                        `Map: ${data.result?.map_info?.name || 'N/A'}`;
                }
                
                // Reload maps
                setTimeout(() => loadResultsData(), 1000);
                
            } else if (data.status === 'ERROR' || data.status === 'failed') {
                showToast('Processing error', 'error');
                const statusDisplay = document.getElementById('processing-status-display');
                if (statusDisplay) {
                    statusDisplay.style.display = 'block';
                    statusDisplay.className = 'status-box error';
                    statusDisplay.textContent = `✗ Processing Error: ${data.error || 'Unknown error'}`;
                }
            } else {
                    // Continue polling
                    setTimeout(() => pollProcessingStatus(jobId, attempt + 1), 2000);
                }
            } catch (error) {
                console.error('Polling error:', error);
                setTimeout(() => pollProcessingStatus(jobId, attempt + 1), 2000);
            }
        }

        /**
         * Show toast notification
         */
        // function showToast(message, type = 'info') {
        //     showAlert(message, type);
        // }

        /**
         * Show alert notification
         */
        // // function showAlert(message, type = 'info') {
        // //     console.log(`[${type.toUpperCase()}] ${message}`);
            
        //     // Create or get toast container
        //     let toastContainer = document.getElementById('toast-container');
        //     if (!toastContainer) {
        //         toastContainer = document.createElement('div');
        //         toastContainer.id = 'toast-container';
        //         toastContainer.style.cssText = `
        //             position: fixed;
        //             top: 20px;
        //             right: 20px;
        //             z-index: 9999;
        //         `;
        //         document.body.appendChild(toastContainer);
        //     }
            
        //     // Create toast
        //     const toast = document.createElement('div');
        //     const colors = {
        //         'success': '#51cf66',
        //         'error': '#ff6b6b',
        //         'warning': '#ffc107',
        //         'info': '#4dabf7'
        //     };
            
        //     toast.style.cssText = `
        //         background: ${colors[type] || '#999'};
        //         color: white;
        //         padding: 1rem;
        //         border-radius: 6px;
        //         margin-bottom: 0.5rem;
        //         box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        //         animation: slideIn 0.3s ease-out;
        //     `;
            
        //     toast.textContent = message;
        //     toastContainer.appendChild(toast);
            
        //     // Remove after 4 seconds
        //     setTimeout(() => toast.remove(), 4000);
        // }

        // ==================== STRING UTILITIES ====================

        const StringUtils = {
            formatBytes(bytes, decimals = 2) {
                if (bytes === 0) return '0 Bytes';
                const k = 1024;
                const dm = decimals < 0 ? 0 : decimals;
                const sizes = ['Bytes', 'KB', 'MB', 'GB'];
                const i = Math.floor(Math.log(bytes) / Math.log(k));
                return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
            }
        };

        // ==================== NUMBER UTILITIES ====================

        const NumberUtils = {
            formatNumber(num) {
                return num ? num.toLocaleString() : '0';
            }
        };

// ==================== UTILITY FUNCTIONS ====================

/**
 * Show notification toast
 */
// function showToast(message, type = 'info') {
//     return showAlert(message, type);
// }

function showAlert(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
    
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
        `;
        document.body.appendChild(toastContainer);
    }
    
    const toast = document.createElement('div');
    const colors = {
        'success': '#51cf66',
        'error': '#ff6b6b',
        'warning': '#ffc107',
        'info': '#4dabf7'
    };
    
    toast.style.cssText = `
        background: ${colors[type] || '#999'};
        color: white;
        padding: 1rem;
        border-radius: 6px;
        margin-bottom: 0.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    `;
    
    toast.textContent = message;
    toastContainer.appendChild(toast);
    
    setTimeout(() => toast.remove(), 4000);
}

// const StringUtils = {
//     formatBytes(bytes, decimals = 2) {
//         if (bytes === 0) return '0 Bytes';
//         const k = 1024;
//         const dm = decimals < 0 ? 0 : decimals;
//         const sizes = ['Bytes', 'KB', 'MB', 'GB'];
//         const i = Math.floor(Math.log(bytes) / Math.log(k));
//         return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
//     }
// };

function initUploadButton() {
    console.log('Dashboard.js: Setting up upload button');
    
    // Wait for upload handler ready (max 3 seconds)
    let attempts = 0;
    const checkInterval = setInterval(() => {
        attempts++;
        
        if (window.tdoaUploader && window.tdoaUploader.show) {
            console.log('✓ Upload handler ready');
            clearInterval(checkInterval);
            
            // Setup button
            const uploadBtn = document.getElementById('upload-iq-btn');
            if (uploadBtn) {
                uploadBtn.addEventListener('click', () => {
                    console.log('🎯 Showing upload modal');
                    window.tdoaUploader.show();
                });
                console.log('✓ Upload button listener attached');
            }
        }
        
        if (attempts > 30) {
            console.warn('⚠️ Upload handler not found after 3 seconds');
            clearInterval(checkInterval);
        }
    }, 100);
}

/**
 * Display localization results di UI
 */
function displayResults(results) {
    const container = document.getElementById('results-container');
    
    if (!container) {
        console.warn('⚠️ results-container not found');
        return;
    }
    
    if (!results || results.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 50px; color: #999;">
                <i class="fas fa-folder-open" style="font-size: 48px; margin-bottom: 20px;"></i>
                <p>📁 No results available yet</p>
            </div>
        `;
        return;
    }
    
    // Build results HTML
    const resultsHTML = results.map((result, idx) => {
        const location = result.data?.location || {};
        const lat = (location.latitude || 0).toFixed(6);
        const lon = (location.longitude || 0).toFixed(6);
        const accuracy = (location.accuracy_meters || 0).toFixed(1);
        
        return `
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        color: white; padding: 20px; border-radius: 8px; 
                        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2); 
                        margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 15px;">
                    <div>
                        <h4 style="margin: 0; font-size: 16px;">
                            <i class="fas fa-map-marker-alt"></i> Result #${idx + 1}
                        </h4>
                        <small style="opacity: 0.8;">
                            📅 ${result.created_at ? new Date(result.created_at).toLocaleString() : 'N/A'}
                        </small>
                    </div>
                    <span style="background: rgba(255,255,255,0.2); padding: 5px 12px; 
                                border-radius: 20px; font-size: 12px;">
                        <i class="fas fa-check-circle"></i> Complete
                    </span>
                </div>
                
                <div style="background: rgba(255,255,255,0.1); padding: 15px; 
                           border-radius: 6px; margin-bottom: 15px;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 10px;">
                        <div>
                            <small style="opacity: 0.8;">📍 Latitude</small>
                            <div style="font-size: 18px; font-weight: bold; font-family: monospace;">
                                ${lat}°
                            </div>
                        </div>
                        <div>
                            <small style="opacity: 0.8;">📍 Longitude</small>
                            <div style="font-size: 18px; font-weight: bold; font-family: monospace;">
                                ${lon}°
                            </div>
                        </div>
                        <div style="grid-column: 1 / -1;">
                            <small style="opacity: 0.8;">📏 Accuracy</small>
                            <div style="font-size: 16px;">±${accuracy} meters</div>
                        </div>
                    </div>
                </div>
                
                <div style="display: flex; gap: 10px;">
                    <button onclick="downloadResult('${result.filename}')" 
                            style="flex: 1; background: rgba(255,255,255,0.2); 
                                   border: none; color: white; cursor: pointer; 
                                   padding: 8px; border-radius: 4px; font-size: 12px;
                                   transition: all 0.3s ease;"
                            onmouseover="this.style.background='rgba(255,255,255,0.3)'"
                            onmouseout="this.style.background='rgba(255,255,255,0.2)'">
                        <i class="fas fa-download"></i> Download JSON
                    </button>
                </div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = resultsHTML;
    console.log(`✓ Displayed ${results.length} result(s)`);
}

// ==================== LOAD RESULTS & MAPS ====================

/**
 * Load results data dengan proper error handling
 */
/**
 * Load results data dengan proper error handling & no infinite loops
 */
async function loadResultsData() {
    // ✅ GUARD: Prevent multiple concurrent requests
    if (isLoadingResults) {
        console.log('Already loading results, skipping');
        return;
    }
    
    isLoadingResults = true;
    
    try {
        console.log('🔄 Loading results...');
        
        const resultsContainer = document.getElementById('results-container');
        if (!resultsContainer) {
            console.warn('Results container not found');
            isLoadingResults = false;
            return;
        }
        
        // Show loading state ONLY if container is empty
        if (resultsContainer.innerHTML.includes('Fetching results') || 
            resultsContainer.innerHTML.includes('spinner')) {
            console.log('Already showing loading state');
            isLoadingResults = false;
            return;
        }
        
        resultsContainer.innerHTML = `
            <div style="text-align: center; padding: 50px; color: #667eea;">
                <i class="fas fa-spinner fa-spin" style="font-size: 30px; margin-bottom: 15px;"></i>
                <p>🔄 Fetching results...</p>
            </div>
        `;
        
        // ✅ ADD TIMEOUT
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);  // 5 sec timeout
        
        const response = await fetch('/api/results', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache'
            },
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        console.log('✓ Results received:', data);
        
        if (data.results && data.results.length > 0) {
            console.log(`✅ Found ${data.results.length} result(s)!`);
            displayResults(data.results);
            showAlert(`✅ Loaded ${data.results.length} result(s)!`, 'success');
        } else {
            resultsContainer.innerHTML = `
                <div style="text-align: center; padding: 50px; color: #999;">
                    <i class="fas fa-hourglass-end" style="font-size: 30px; margin-bottom: 15px;"></i>
                    <p>⏳ No results yet</p>
                    <p style="font-size: 12px;">Processing may still be running...</p>
                    <button class="btn btn-primary btn-sm" onclick="loadResultsDataOnce()" style="margin-top: 15px;">
                        <i class="fas fa-sync-alt"></i> Refresh
                    </button>
                </div>
            `;
        }
        
    } catch (error) {
        console.error('❌ Error loading results:', error);
        const resultsContainer = document.getElementById('results-container');
        if (resultsContainer) {
            resultsContainer.innerHTML = `
                <div style="text-align: center; padding: 50px; color: #ff6b6b;">
                    <i class="fas fa-exclamation-circle" style="font-size: 30px; margin-bottom: 15px;"></i>
                    <p>❌ Error: ${error.message}</p>
                    <button class="btn btn-primary btn-sm" onclick="loadResultsDataOnce()" style="margin-top: 15px;">
                        <i class="fas fa-sync-alt"></i> Retry
                    </button>
                </div>
            `;
        }
    } finally {
        isLoadingResults = false;
    }
}

/**
 * Display localization results
 */
function displayResults(results) {
    const container = document.getElementById('results-container');
    
    if (!container) {
        console.warn('results-container not found');
        return;
    }
    
    if (!results || results.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 50px; color: #999;">
                <i class="fas fa-hourglass-end" style="font-size: 48px; margin-bottom: 20px;"></i><br>
                No results available yet<br>
                <small>Process IQ data first to see results</small>
            </div>
        `;
        return;
    }
    
    container.innerHTML = results.map((result, idx) => `
        <div style="background: #f8f9fa; padding: 15px; border-radius: 6px; margin-bottom: 10px; border-left: 4px solid #667eea;">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div>
                    <strong style="color: #333;">Result #${idx + 1}</strong>
                    <small style="display: block; color: #666; margin-top: 5px;">
                        File: ${result.filename || 'N/A'}
                    </small>
                </div>
                <small style="color: #999;">${result.created_at ? new Date(result.created_at).toLocaleString() : 'N/A'}</small>
            </div>
            
            ${result.data && result.data.location ? `
                <div style="margin-top: 15px; background: white; padding: 10px; border-radius: 4px;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; font-size: 13px;">
                        <div>
                            <strong>Latitude:</strong><br>
                            <code style="color: #667eea;">${(result.data.location.latitude || 0).toFixed(6)}</code>
                        </div>
                        <div>
                            <strong>Longitude:</strong><br>
                            <code style="color: #667eea;">${(result.data.location.longitude || 0).toFixed(6)}</code>
                        </div>
                        ${result.data.location.altitude_meters ? `
                            <div>
                                <strong>Altitude:</strong><br>
                                <code style="color: #667eea;">${result.data.location.altitude_meters.toFixed(2)} m</code>
                            </div>
                        ` : ''}
                        <div>
                            <strong>Accuracy:</strong><br>
                            <code style="color: #51cf66;">${(result.data.location.accuracy_meters || 0).toFixed(1)} m</code>
                        </div>
                    </div>
                </div>
            ` : '<p style="color: #999; font-size: 12px; margin-top: 10px;">No location data available</p>'}
            
            <div style="margin-top: 10px; display: flex; gap: 10px;">
                <button class="btn btn-secondary btn-sm" onclick="downloadResult('${result.filename}')" style="flex: 1;">
                    <i class="fas fa-download"></i> Download
                </button>
            </div>
        </div>
    `).join('');
}

/**
 * Display generated maps
 */
function displayMaps(maps) {
    const container = document.getElementById('maps-container');
    
    if (!container) {
        console.warn('maps-container not found');
        return;
    }
    
    if (!maps || maps.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 50px; color: #999;">
                <i class="fas fa-map" style="font-size: 48px; margin-bottom: 20px;"></i><br>
                No maps generated yet<br>
                <small>Generate results to see maps</small>
            </div>
        `;
        return;
    }
    
    container.innerHTML = maps.map((map, idx) => `
        <div style="background: #f8f9fa; padding: 15px; border-radius: 6px; margin-bottom: 10px; border-left: 4px solid #764ba2;">
            <strong style="color: #333;">
                <i class="fas fa-map"></i> ${map.replace('.html', '')}
            </strong>
            <div style="margin-top: 10px; display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                <button class="btn btn-primary btn-sm" onclick="openMap('${map}')">
                    <i class="fas fa-external-link-alt"></i> Open Map
                </button>
                <button class="btn btn-secondary btn-sm" onclick="downloadMap('${map}')">
                    <i class="fas fa-download"></i> Download
                </button>
            </div>
        </div>
    `).join('');
}

/**
 * Open map in new tab
 */
function openMap(filename) {
    console.log(`Opening map: ${filename}`);
    window.open(`/api/download-map/${filename}`, '_blank');
}

/**
 * Download map file
 */
function downloadMap(filename) {
    console.log(`Downloading map: ${filename}`);
    const link = document.createElement('a');
    link.href = `/api/download-map/${filename}`;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showAlert(`Downloading: ${filename}`, 'info');
}

/**
 * Download result file
 */
function downloadResult(filename) {
    console.log(`Downloading result: ${filename}`);
    const link = document.createElement('a');
    link.href = `/api/results/${filename}`;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showAlert(`Downloading: ${filename}`, 'info');
}

/**
 * Show toast notification (alias untuk showAlert)
 */
function showToast(message, type = 'info') {
    return showAlert(message, type);
}

// ==================== AUTO-LOAD RESULTS ====================

function initAutoLoadResults() {
    console.log('Setting up results auto-load...');

    const resultsTab = document.querySelector('[data-tab="results"]') ||
                       document.getElementById('results-tab') ||
                       document.getElementById('results');

    if (!resultsTab) {
        console.warn('Results tab not found');
        return;
    }

    resultsTab.addEventListener('click', () => {
        console.log('Results tab clicked - loading data');
        loadResultsDataOnce();
        startResultsPolling();
    });

    const otherTabs = Array.from(document.querySelectorAll('[onclick*="switchTab"]'))
        .filter(tab => !tab.textContent.includes('Results'));

    otherTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            stopResultsPolling();
        });
    });

    const observer = new MutationObserver(() => {
        if (resultsTab.style.display !== 'none' && resultsTab.classList.contains('active')) {
            loadResultsDataOnce();
            startResultsPolling();
        } else {
            stopResultsPolling();
        }
    });

    observer.observe(resultsTab, { attributes: true, attributeFilter: ['class', 'style'] });

    const tabButtons = document.querySelectorAll('button[onclick*="switchTab"]');
    tabButtons.forEach(btn => {
        if (btn.textContent.includes('Results')) {
            btn.addEventListener('click', () => {
                setTimeout(loadResultsData, 500);
            });
        }
    });
}

function loadResultsDataOnce() {
    if (isLoadingResults) {
        console.log('Already loading, skipping...');
        return;
    }
    loadResultsData();
}

function startResultsPolling() {
    if (resultsPollInterval) {
        console.log('Polling already running');
        return;
    }

    console.log('Starting results polling...');
    resultsPollInterval = setInterval(() => {
        loadResultsData();
    }, 15000);  // Poll setiap 15 detik
}

function stopResultsPolling() {
    if (resultsPollInterval) {
        console.log('Stopping results polling...');
        clearInterval(resultsPollInterval);
        resultsPollInterval = null;
    }
}

// ==================== TAB SWITCHING ====================

/**
 * Switch to different tab
 */
function switchTab(tabName, event) {
    console.log(`Switching to tab: ${tabName}`);
    
    // Hide all tabs
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all buttons
    const buttons = document.querySelectorAll('.nav-btn');
    buttons.forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    const selectedTab = document.getElementById(tabName);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    const activeButton = event?.target?.closest('.nav-btn')
        || Array.from(document.querySelectorAll('.nav-btn')).find(btn => btn.textContent.trim().toLowerCase() === tabName.toLowerCase());
    if (activeButton) {
        activeButton.classList.add('active');
    }
    
    // Load data jika tab Results
    if (tabName === 'results' && window.loadResultsData) {
        console.log('Results tab active, loading data...');
        loadResultsData();
    }
}

function initTabNavigation() {
    console.log('Dashboard loaded, initializing tabs...');
    
    const firstTab = document.querySelector('.nav-btn');
    if (firstTab) {
        firstTab.classList.add('active');
    }
    
    const firstContent = document.querySelector('.tab-content');
    if (firstContent) {
        firstContent.classList.add('active');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initUploadButton();
    initTabNavigation();
    initAutoLoadResults();
});

/**
 * Load results data dengan polling
 */
// async function loadResultsData() {
//     try {
//         console.log('📊 Loading results...');
        
//         const resultsContainer = document.getElementById('results-container');
//         if (!resultsContainer) {
//             console.warn('Results container not found');
//             return;
//         }
        
//         // Show loading state
//         resultsContainer.innerHTML = `
//             <div style="text-align: center; padding: 50px; color: #667eea;">
//                 <i class="fas fa-spinner fa-spin" style="font-size: 30px; margin-bottom: 15px;"></i>
//                 <p>Fetching results...</p>
//             </div>
//         `;
        
//         // Try to get results
//         const response = await fetch('/api/results');
        
//         if (!response.ok) {
//             throw new Error(`HTTP ${response.status}`);
//         }
        
//         const data = await response.json();
//         console.log('Results data:', data);
        
//         if (data.results && data.results.length > 0) {
//             displayResults(data.results);
//             showAlert(`✓ Found ${data.results.length} result(s)!`, 'success');
//         } else {
//             resultsContainer.innerHTML = `
//                 <div style="text-align: center; padding: 50px; color: #999;">
//                     <i class="fas fa-hourglass-end" style="font-size: 30px; margin-bottom: 15px;"></i>
//                     <p>No results yet. Processing may still be in progress...</p>
//                     <p style="font-size: 12px; margin-top: 10px;">
//                         <i class="fas fa-info-circle"></i> 
//                         Results will appear here once processing completes. Check back in a moment.
//                     </p>
//                     <button class="btn btn-primary btn-sm" onclick="loadResultsData()" style="margin-top: 15px;">
//                         <i class="fas fa-sync-alt"></i> Refresh
//                     </button>
//                 </div>
//             `;
//         }
        
//     } catch (error) {
//         console.error('Error loading results:', error);
//         const resultsContainer = document.getElementById('results-container');
//         if (resultsContainer) {
//             resultsContainer.innerHTML = `
//                 <div style="text-align: center; padding: 50px; color: #ff6b6b;">
//                     <i class="fas fa-exclamation-circle" style="font-size: 30px; margin-bottom: 15px;"></i>
//                     <p>Error loading results: ${error.message}</p>
//                     <button class="btn btn-primary btn-sm" onclick="loadResultsData()" style="margin-top: 15px;">
//                         <i class="fas fa-sync-alt"></i> Retry
//                     </button>
//                 </div>
//             `;
//         }
//     }
// }

/**
 * Display results
 */
// function displayResults(results) {
//     const container = document.getElementById('results-container');
    
//     if (!results || results.length === 0) {
//         container.innerHTML = `
//             <p style="color: #999; text-align: center; padding: 50px;">
//                 <i class="fas fa-hourglass-end"></i><br>
//                 No results available yet
//             </p>
//         `;
//         return;
//     }
    
//     container.innerHTML = `
//         <div style="display: grid; gap: 15px;">
//             ${results.map((result, idx) => `
//                 <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);">
//                     <div style="display: flex; justify-content: space-between; align-items: start;">
//                         <div>
//                             <h4 style="margin: 0 0 10px 0; font-size: 16px;">
//                                 <i class="fas fa-location-dot"></i> Result #${idx + 1}
//                             </h4>
//                             <small style="opacity: 0.9;">${result.created_at}</small>
//                         </div>
//                         <span style="background: rgba(255,255,255,0.2); padding: 5px 12px; border-radius: 20px; font-size: 12px;">
//                             <i class="fas fa-check-circle"></i> Complete
//                         </span>
//                     </div>
                    
//                     ${result.data && result.data.location ? `
//                         <div style="margin-top: 15px; background: rgba(255,255,255,0.1); padding: 15px; border-radius: 6px;">
//                             <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 10px;">
//                                 <div>
//                                     <small style="opacity: 0.8;">Latitude</small>
//                                     <div style="font-size: 18px; font-weight: bold;">
//                                         ${result.data.location.latitude?.toFixed(4) || 'N/A'}°
//                                     </div>
//                                 </div>
//                                 <div>
//                                     <small style="opacity: 0.8;">Longitude</small>
//                                     <div style="font-size: 18px; font-weight: bold;">
//                                         ${result.data.location.longitude?.toFixed(4) || 'N/A'}°
//                                     </div>
//                                 </div>
//                             </div>
//                             ${result.data.location.accuracy_meters ? `
//                                 <div>
//                                     <small style="opacity: 0.8;">📍 Accuracy</small>
//                                     <div style="font-size: 16px;">±${result.data.location.accuracy_meters.toFixed(1)} meters</div>
//                                 </div>
//                             ` : ''}
//                             ${result.data.location.altitude_meters ? `
//                                 <div>
//                                     <small style="opacity: 0.8;">📏 Altitude</small>
//                                     <div style="font-size: 16px;">${result.data.location.altitude_meters.toFixed(1)} m</div>
//                                 </div>
//                             ` : ''}
//                         </div>
//                     ` : '<p style="color: rgba(255,255,255,0.8); font-size: 12px;">No location data</p>'}
                    
//                     <div style="margin-top: 15px; display: flex; gap: 10px;">
//                         <button class="btn btn-secondary btn-sm" onclick="downloadResult('${result.filename}')" style="flex: 1; background: rgba(255,255,255,0.2); border: none; color: white; cursor: pointer; padding: 8px; border-radius: 4px; font-size: 12px;">
//                             <i class="fas fa-download"></i> Download JSON
//                         </button>
//                         <button class="btn btn-secondary btn-sm" onclick="copyLocation(${result.data.location?.latitude}, ${result.data.location?.longitude})" style="flex: 1; background: rgba(255,255,255,0.2); border: none; color: white; cursor: pointer; padding: 8px; border-radius: 4px; font-size: 12px;">
//                             <i class="fas fa-copy"></i> Copy Coords
//                         </button>
//                     </div>
//                 </div>
//             `).join('')}
//         </div>
//     `;
// }

// /**
//  * Copy location to clipboard
//  */
// function copyLocation(lat, lon) {
//     const text = `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
//     navigator.clipboard.writeText(text).then(() => {
//         showAlert(`✓ Copied: ${text}`, 'success');
//     });
// }

/**
 * Download result
 */
// function downloadResult(filename) {
//     const link = document.createElement('a');
//     link.href = `/api/results/${filename}`;
//     link.download = filename;
//     document.body.appendChild(link);
//     link.click();
//     document.body.removeChild(link);
//     showAlert(`📥 Downloading: ${filename}`, 'info');
// }

// /**
//  * Download map
//  */
// function downloadMap(filename) {
//     const link = document.createElement('a');
//     link.href = `/api/download-map/${filename}`;
//     link.download = filename;
//     document.body.appendChild(link);
//     link.click();
//     document.body.removeChild(link);
//     showAlert(`📥 Downloading: ${filename}`, 'info');
// }

// /**
//  * Open map in new tab
//  */
// function openMap(filename) {
//     window.open(`/api/download-map/${filename}`, '_blank');
// }

