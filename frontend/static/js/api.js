/**
 * Logging utility
 */
function logDebug(message, data = null) {
    const timestamp = new Date().toLocaleTimeString();
    if (data) {
        console.log(`[${timestamp}] ${message}`, data);
    } else {
        console.log(`[${timestamp}] ${message}`);
    }
}

/**
 * API Communication Layer
 * Handles all HTTP requests to backend with error handling and logging
 */

const API = {
    baseURL: 'http://localhost:5000',
    timeout: 10000,  // 10 seconds timeout

    /**
     * Generic fetch wrapper with timeout
     */
    async request(endpoint, options = {}) {
        try {
            const url = `${this.baseURL}${endpoint}`;
            
            // Set default method
            const method = options.method || 'GET';

            // Build config
            const config = {
                method: method,
                timeout: this.timeout
            };

            // Set headers only if not FormData
            if (!(options.body instanceof FormData)) {
                config.headers = {
                    'Content-Type': 'application/json',
                    ...options.headers
                };
            }

            // Add body if present
            if (options.body) {
                if (options.body instanceof FormData) {
                    config.body = options.body;
                    // Don't set Content-Type for FormData - browser will set it
                    delete config.headers;
                } else {
                    config.body = typeof options.body === 'string' 
                        ? options.body 
                        : JSON.stringify(options.body);
                }
            }

            logDebug(`🔗 API Request: ${method} ${endpoint}`);

            // Create abort controller for timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.timeout);

            // Make request
            const response = await fetch(url, { ...config, signal: controller.signal });
            clearTimeout(timeoutId);

            // Check response status
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
            }

            // Parse response
            const data = await response.json();
            logDebug(`✓ API Response: ${endpoint}`, data);
            
            return { success: true, data };

        } catch (error) {
            if (error.name === 'AbortError') {
                logDebug(`❌ API Timeout: ${endpoint}`, `Request exceeded ${this.timeout}ms`);
                return { success: false, error: 'Request timeout' };
            }

            logDebug(`❌ API Error: ${endpoint}`, error.message);
            return { success: false, error: error.message };
        }
    },

    /**
     * GET request
     */
    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    },

    /**
     * POST request
     */
    async post(endpoint, body) {
        return this.request(endpoint, {
            method: 'POST',
            body: body
        });
    },

    /**
     * PUT request
     */
    async put(endpoint, body) {
        return this.request(endpoint, {
            method: 'PUT',
            body: body
        });
    },

    /**
     * DELETE request
     */
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    },

    // ==================== SYSTEM ENDPOINTS ====================

    /**
     * Get system status
     */
    async getStatus() {
        return this.get('/api/status');
    },

    /**
     * Get list of receivers
     */
    async getReceivers() {
        return this.get('/api/receivers');
    },

    /**
     * Get configuration
     */
    async getConfig() {
        return this.get('/api/config');
    },

    /**
     * Get dashboard statistics
     */
    async getDashboardStats() {
        return this.get('/api/dashboard-stats');
    },

    // ==================== RECORDING ENDPOINTS ====================

    /**
     * Start recording session
     */
    async startRecording(fref, fcari, loops, syncMode) {
        return this.post('/api/recording/start', {
            fref_mhz: fref,
            fcari_mhz: fcari,
            loops: loops,
            sync_mode: syncMode
        });
    },

    /**
     * Get recording status
     */
    async getRecordingStatus(sessionId) {
        return this.get(`/api/recording/status/${sessionId}`);
    },

    /**
     * Cancel recording
     */
    async cancelRecording(sessionId) {
        return this.post(`/api/recording/cancel/${sessionId}`, {});
    },

    /**
     * Get list of recorded files
     */
    async getRecordedFiles() {
        return this.get('/api/recorded-files');
    },

    // ==================== FILE PROCESSING ENDPOINTS ====================

    /**
     * Get list of imported IQ files
     */
    async getImportedFiles() {
        return this.get('/api/imported-files');
    },

    /**
     * Import raw IQ file for processing
     * @param {File} file - The .dat or .iq file to import
     * @param {number} sampleRate - Sample rate in Hz (default: 2.4e6)
     */
    async importFile(file, sampleRate = 2.4e6) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('sample_rate', sampleRate);
        
        return this.request('/api/import-file', {
            method: 'POST',
            body: formData
        });
    },

    /**
     * Delete imported file
     */
    async deleteFile(fileId) {
        return this.delete(`/api/delete-file/${fileId}`);
    },

    /**
     * Get spectrum data for visualization
     */
    async getSpectrum(fileId) {
        return this.get(`/api/spectrum/${fileId}`);
    },

    // ==================== TDOA PROCESSING ENDPOINTS ====================

    /**
     * Process multiple files for TDOA localization
     * @param {Array} fileIds - List of file IDs to process
     * @param {number} refFreq - Reference frequency in MHz
     * @param {number} targetFreq - Target frequency in MHz
     */
    async processMultipleFiles(fileIds, refFreq, targetFreq) {
        return this.post('/api/process-multiple-files', {
            file_ids: fileIds,
            ref_freq_mhz: refFreq,
            target_freq_mhz: targetFreq
        });
    },

    /**
     * Get processing job status
     */
    async getProcessingStatus(jobId) {
        return this.get(`/api/processing/status/${jobId}`);
    },

    // ==================== RESULTS & MAPS ENDPOINTS ====================

    /**
     * Get generated maps
     */
    async getMaps() {
        return this.get('/api/maps');
    },

    /**
     * Get localization results
     */
    async getResults() {
        return this.get('/api/results');
    },

    /**
     * Get files list
     */
    async getFiles() {
        return this.get('/api/files');
    },

    async downloadResult(filename) {
        window.location.href = `/api/results/${filename}`;
    },
    
    async getDashboardStats() {
    return this.get('/api/dashboard-stats');
    }
};

// Log API initialization
logDebug('✓ API layer initialized', { baseURL: API.baseURL, timeout: API.timeout });