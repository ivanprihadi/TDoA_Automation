/**
 * Main Application Logic
 * Handles dashboard initialization, tab switching, and global state
 */

// ==================== GLOBAL STATE ====================
let appState = {
    currentTab: 'dashboard',
    systemStatus: null,
    receivers: [],
    isLoading: false,
    lastRefresh: null
};

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 Initializing Application...');
    
    // Initialize dashboard
    await initializeApp();
    
    // Setup event listeners
    setupEventListeners();
    
    // Update footer time
    updateFooterTime();
    setInterval(updateFooterTime, 1000);
    
    // Auto-refresh system data
    await refreshSystemData();
    setInterval(refreshSystemData, 30000); // Every 30 seconds
    
    console.log('✓ Application initialized');
});

// ==================== INITIALIZATION FUNCTIONS ====================

/**
 * Initialize application
 */
async function initializeApp() {
    try {
        console.log('📊 Loading dashboard data...');
        
        // Load system status
        const statusResult = await API.getStatus();
        if (statusResult.success) {
            appState.systemStatus = statusResult.data;
            updateSystemInfo(statusResult.data);
        }
        
        // Load receivers
        const receiversResult = await API.getReceivers();
        if (receiversResult.success) {
            appState.receivers = receiversResult.data;
            updateReceiversDisplay(receiversResult.data);
        }
        
        // Load dashboard stats
        const statsResult = await API.getDashboardStats();
        if (statsResult.success) {
            updateDashboardStats(statsResult.data);
        }
        
        console.log('✓ Dashboard data loaded');
        
    } catch (error) {
        console.error('❌ Initialization error:', error);
        showToast('Failed to initialize dashboard', 'error');
    }
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Tab navigation
    document.querySelectorAll('.nav-btn, [onclick*="switchTab"]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const tabName = e.target.closest('.nav-btn, [onclick*="switchTab"]')?.dataset?.tab ||
                           e.target.closest('.nav-btn')?.textContent?.toLowerCase().split(' ')[0];
            if (tabName) {
                switchTab(tabName);
            }
        });
    });
    
    // Recording button
    const recordBtn = document.getElementById('recordBtn');
    if (recordBtn) {
        recordBtn.addEventListener('click', (e) => {
            e.preventDefault();
            if (window.recordingDialog) {
                window.recordingDialog.show();
            }
        });
    }
    
    console.log('✓ Event listeners setup');
}

// ==================== TAB SWITCHING ====================

/**
 * Switch to different tab
 */
function switchTab(tabName) {
    console.log(`📑 Switching to tab: ${tabName}`);
    
    // Validate tab exists
    const tabElement = document.getElementById(tabName);
    if (!tabElement) {
        console.warn(`⚠️ Tab not found: ${tabName}`);
        return;
    }
    
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active from all buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    tabElement.classList.add('active');
    
    // Mark button as active
    const activeBtn = document.querySelector(`.nav-btn[onclick*="${tabName}"]`) ||
                     Array.from(document.querySelectorAll('.nav-btn')).find(btn => 
                         btn.textContent.toLowerCase().includes(tabName.split('-')[0])
                     );
    
    if (activeBtn) {
        activeBtn.classList.add('active');
    }
    
    // Update state
    appState.currentTab = tabName;
    
    // Load tab-specific data if needed
    loadTabData(tabName);
}

/**
 * Load data for specific tab
 */
async function loadTabData(tabName) {
    switch(tabName) {
        case 'dashboard':
            await refreshSystemData();
            break;
        case 'import-data':              
            await loadImportedFiles();   
            break;
        case 'processing':
            await loadProcessingData();
            break;
        case 'results':
            await loadResultsData();
            break;
        case 'configuration':
            await loadConfigurationData();
            break;
        default:
            break;
    }
}

// ==================== DATA LOADING FUNCTIONS ====================

/**
 * Refresh system data
 */
async function refreshSystemData() {
    if (appState.isLoading) return;
    
    try {
        appState.isLoading = true;
        
        // Update timestamp
        appState.lastRefresh = new Date();
        
        // Get system status
        const statusResult = await API.getStatus();
        if (statusResult.success) {
            updateSystemInfo(statusResult.data);
        }
        
        // Get receivers
        const receiversResult = await API.getReceivers();
        if (receiversResult.success) {
            appState.receivers = receiversResult.data;
            updateReceiversDisplay(receiversResult.data);
        }
        
        // Get stats
        const statsResult = await API.getDashboardStats();
        if (statsResult.success) {
            updateDashboardStats(statsResult.data);
        }
        
    } catch (error) {
        console.error('❌ Refresh error:', error);
    } finally {
        appState.isLoading = false;
    }
}

/**
 * Load processing tab data
 */
async function loadProcessingData() {
    console.log('📂 Loading processing data...');
    
    try {
        const filesResult = await API.getFiles();
        if (filesResult.success) {
            updateFilesList(filesResult.data);
        }
    } catch (error) {
        console.error('❌ Error loading processing data:', error);
    }
}

/**
 * Load results tab data
 */
async function loadResultsData() {
    console.log('🗺️ Loading results data...');
    
    try {
        const mapsResult = await API.getMaps();
        if (mapsResult.success) {
            updateMapsList(mapsResult.data);
        }
    } catch (error) {
        console.error('❌ Error loading results data:', error);
    }
}

/**
 * Load configuration tab data
 */
async function loadConfigurationData() {
    console.log('⚙️ Loading configuration data...');
    
    try {
        const configResult = await API.getConfig();
        if (configResult.success) {
            updateConfigDisplay(configResult.data);
        }
    } catch (error) {
        console.error('❌ Error loading configuration:', error);
    }
}

// ==================== UI UPDATE FUNCTIONS ====================

/**
 * Update system information display
 */
function updateSystemInfo(status) {
    if (!status) return;
    
    const appEnv = document.getElementById('app-env');
    if (appEnv) {
        if (status.environment === 'mock') {
            appEnv.textContent = '🎭 Mock Mode (Testing)';
            appEnv.style.color = '#ff6b6b';
        } else {
            appEnv.textContent = '📡 Real Mode';
            appEnv.style.color = '#51cf66';
        }
    }
    
    const systemStatus = document.getElementById('system-status');
    if (systemStatus) {
        systemStatus.textContent = status.running ? '● Running' : '● Stopped';
        systemStatus.style.color = status.running ? '#51cf66' : '#ff6b6b';
    }
}

/**
 * Update receivers display
 */
function updateReceiversDisplay(receivers) {
    if (!receivers || receivers.length === 0) {
        console.warn('⚠️ No receivers available');
        return;
    }
    
    // Update receiver count
    const rxCount = document.getElementById('receiver-count');
    if (rxCount) {
        rxCount.textContent = receivers.length;
    }
    
    // Update receivers list
    const rxList = document.getElementById('receiver-status-list');
    if (rxList) {
        rxList.innerHTML = receivers.map(rx => `
            <div class="receiver-item">
                <strong>${rx.name || `Receiver ${rx.id}`}</strong>
                <span>Host: ${rx.hostname || 'N/A'}</span>
                <span>Location: ${(rx.latitude || 0).toFixed(4)}, ${(rx.longitude || 0).toFixed(4)}, ${rx.altitude || 0}m</span>
                <span>Status: <span class="status-badge success">● Online</span></span>
            </div>
        `).join('');
    }
    
    // Update receiver config
    const configList = document.getElementById('receiver-config-list');
    if (configList) {
        configList.innerHTML = receivers.map(rx => `
            <div class="info-group">
                <label>${rx.name || `Receiver ${rx.id}`}</label>
                <span>IP: ${rx.hostname || 'N/A'} | Coords: (${(rx.latitude || 0).toFixed(4)}, ${(rx.longitude || 0).toFixed(4)}, ${rx.altitude || 0}m)</span>
            </div>
        `).join('');
    }
}

/**
 * Update dashboard statistics
 */
function updateDashboardStats(stats) {
    if (!stats) return;
    
    const fileCount = document.getElementById('file-count');
    if (fileCount) fileCount.textContent = stats.file_count || 0;
    
    const mapCount = document.getElementById('map-count');
    if (mapCount) mapCount.textContent = stats.map_count || 0;
}

/**
 * Update files list (for processing tab)
 */
function updateFilesList(files) {
    const fileSelect1 = document.getElementById('file1');
    const fileSelect2 = document.getElementById('file2');
    const fileSelect3 = document.getElementById('file3');
    
    const options = files.map(f => `<option value="${f.name}">${f.name}</option>`).join('');
    
    [fileSelect1, fileSelect2, fileSelect3].forEach(select => {
        if (select) {
            select.innerHTML = '<option value="">-- Select File --</option>' + options;
        }
    });
}

/**
 * Update maps list (for results tab)
 */
function updateMapsList(maps) {
    const mapsList = document.getElementById('maps-list');
    if (!mapsList) return;
    
    if (!maps || maps.length === 0) {
        mapsList.innerHTML = '<p style="grid-column: 1/-1; color: #999;">No maps generated yet.</p>';
        return;
    }
    
    mapsList.innerHTML = maps.map(m => `
        <div class="maps-card">
            <div class="maps-card-thumbnail">
                <i class="fas fa-map" style="font-size: 48px; color: #999;"></i>
            </div>
            <h4>${m.name}</h4>
            <p style="font-size: 12px; color: #999; margin-bottom: 10px;">Generated: ${new Date(m.created_at).toLocaleString()}</p>
            <button class="btn btn-primary btn-sm" onclick="viewMap('${m.path}')">
                <i class="fas fa-eye"></i> View
            </button>
        </div>
    `).join('');
}

/**
 * Update configuration display
 */
function updateConfigDisplay(config) {
    if (!config) return;
    
    const configDisplay = document.getElementById('config-display');
    if (configDisplay) {
        configDisplay.textContent = JSON.stringify(config, null, 2);
    }
}

// ==================== UTILITY FUNCTIONS ====================

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    if (!toast) return;
    
    toast.className = `toast ${type}`;
    toast.textContent = message;
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

/**
 * Update footer time
 */
function updateFooterTime() {
    const footerTime = document.getElementById('footer-time');
    if (footerTime) {
        footerTime.textContent = DateUtils.getCurrentTime();
    }
}

/**
 * View map in new window
 */
function viewMap(mapPath) {
    if (mapPath) {
        window.open(mapPath, '_blank');
    }
}

/**
 * Download results
 */
function downloadResults() {
    console.log('⬇️ Downloading results...');
    showToast('Download starting...', 'info');
    // Implementation depends on backend
}

/**
 * Start batch processing
 */
async function startBatchProcessing() {
    console.log('🔄 Starting batch processing...');
    showToast('Batch processing not yet implemented', 'warning');
}

/**
 * Process files
 */
async function processFiles() {
    const file1 = document.getElementById('file1')?.value;
    const file2 = document.getElementById('file2')?.value;
    const file3 = document.getElementById('file3')?.value;
    
    if (!file1 || !file2 || !file3) {
        showToast('Please select all three files', 'warning');
        return;
    }
    
    console.log('🔄 Processing files...', { file1, file2, file3 });
    
    try {
        const result = await API.startProcessing(
            [file1, file2, file3],
            {
                bandwidth: parseFloat(document.getElementById('bandwidth')?.value || 40),
                correlation_type: document.getElementById('corr-type')?.value || 'dphase',
                heatmap_resolution: parseInt(document.getElementById('heatmap-res')?.value || 200),
                heatmap_threshold: parseFloat(document.getElementById('heatmap-thresh')?.value || 0.70)
            }
        );
        
        if (result.success) {
            showToast('Processing started', 'success');
        } else {
            showToast(`Error: ${result.error}`, 'error');
        }
        
    } catch (error) {
        console.error('❌ Processing error:', error);
        showToast(`Error: ${error.message}`, 'error');
    }
}

// ==================== EXPORT FOR TESTING ====================
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        appState,
        switchTab,
        refreshSystemData,
        showToast
    };
}