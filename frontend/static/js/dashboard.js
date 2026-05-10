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

// Initialize saat DOM loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('dashboard')) {
        DashboardManager.init();
    }
});