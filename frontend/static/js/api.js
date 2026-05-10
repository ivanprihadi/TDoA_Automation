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
            
            // Set default headers
            const headers = {
                'Content-Type': 'application/json',
                ...options.headers
            };

            // Set default method
            const method = options.method || 'GET';

            // Build config
            const config = {
                method: method,
                headers: headers,
                timeout: this.timeout
            };

            // Add body if present
            if (options.body) {
                config.body = typeof options.body === 'string' 
                    ? options.body 
                    : JSON.stringify(options.body);
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
     * Get recorded files
     */
    async getFiles() {
        return this.get('/api/files');
    },

    /**
     * Get generated maps
     */
    async getMaps() {
        return this.get('/api/maps');
    },

    /**
     * Get dashboard statistics
     */
    async getDashboardStats() {
        return this.get('/api/dashboard-stats');
    },

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
     * Start processing
     */
    async startProcessing(files, params) {
        return this.post('/api/processing/start', {
            files: files,
            parameters: params
        });
    },

    /**
     * Get processing status
     */
    async getProcessingStatus(sessionId) {
        return this.get(`/api/processing/status/${sessionId}`);
    }
};

/**
 * Helper function for logging (used by API)
 */
function logDebug(message, data = null) {
    const timestamp = new Date().toLocaleTimeString();
    if (data) {
        console.log(`[${timestamp}] ${message}`, data);
    } else {
        console.log(`[${timestamp}] ${message}`);
    }
}