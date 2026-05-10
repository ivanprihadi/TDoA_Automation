/**
 * DASHBOARD MANAGER
 * dashboard.js - Menangani real-time updates dan dashboard logic
 */

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
        // Quick action buttons
        document.querySelector('[onclick*="startProcessing"]')?.addEventListener('click', () => {
            console.log('Quick action: Start Processing');
            goToProcessing();
        });
        
        document.querySelector('[onclick*="viewResults"]')?.addEventListener('click', () => {
            console.log('Quick action: View Results');
            goToResults();
        });
    }
};

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

// Load imported files ketika tab import-data dibuka
    const importDataTab = document.getElementById('import-data');
    if (importDataTab) {
        // Load on tab switch
        document.addEventListener('tabswitched', () => {
            if (document.querySelector('#import-data.active')) {
                loadImportedFiles();
            }
        });
    }
}

// Initialize saat DOM loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('dashboard')) {
        DashboardManager.init();
    }
});

// ==================== UTILITY FUNCTIONS ====================

/**
 * Show alert notification
 */
function showAlert(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
    
    // Create or get toast container
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
    
    // Create toast
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
    
    // Remove after 4 seconds
    setTimeout(() => toast.remove(), 4000);
}

/**
 * String utilities
 */
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

/**
 * Number utilities
 */
const NumberUtils = {
    formatNumber(num) {
        return num ? num.toLocaleString() : '0';
    }
};