/**
 * Recording Dialog Handler
 * Manages recording dialog and communication with backend API
 */

class RecordingDialog {
    constructor() {
        // ==================== DOM ELEMENTS ====================
        this.modal = document.getElementById('recordingModal');
        this.form = document.getElementById('recordingForm');
        this.startBtn = document.getElementById('startBtn');
        this.cancelBtn = document.getElementById('cancelBtn');
        this.closeBtn = document.querySelector('.modal .close') || document.querySelector('.close');
        this.statusDisplay = document.getElementById('statusDisplay');
        this.progressContainer = document.getElementById('progressContainer');
        this.progressFill = document.getElementById('progressFill');
        this.progressText = document.getElementById('progressText');
        
        // ==================== STATE ====================
        this.isRecording = false;
        this.currentSessionId = null;
        this.pollInterval = null;
        this.pollAttempts = 0;
        this.maxPollAttempts = 300;  // 10 minutes max (2s * 300)
        this.recordingStartTime = null;
        
        // ==================== INITIALIZATION ====================
        if (this.modal) {
            this.initEventListeners();
            console.log('✓ RecordingDialog initialized');
        } else {
            console.warn('⚠️ Recording modal not found');
        }
    }
    
    /**
     * Initialize event listeners
     */
    initEventListeners() {
        // Start button
        if (this.startBtn) {
            this.startBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.startRecording();
            });
        }
        
        // Cancel button
        if (this.cancelBtn) {
            this.cancelBtn.addEventListener('click', () => this.close());
        }
        
        // Close button
        if (this.closeBtn) {
            this.closeBtn.addEventListener('click', () => this.close());
        }
        
        // Close modal when clicking outside
        if (this.modal) {
            window.addEventListener('click', (event) => {
                if (event.target === this.modal && !this.isRecording) {
                    this.close();
                }
            });
        }
    }
    
    /**
     * Show recording dialog
     */
    show() {
        console.log('📍 Opening recording dialog');
        if (this.modal) {
            this.modal.classList.add('show');
            this.resetForm();
        }
    }
    
    /**
     * Close recording dialog
     */
    close() {
        console.log('❌ Closing recording dialog');
        if (this.modal) {
            this.modal.classList.remove('show');
        }
        this.stopPolling();
    }
    
    /**
     * Reset form to initial state
     */
    resetForm() {
        if (this.form) {
            this.form.reset();
        }
        
        if (this.statusDisplay) {
            this.statusDisplay.style.display = 'none';
            this.statusDisplay.className = 'status-box';
        }
        
        if (this.progressContainer) {
            this.progressContainer.style.display = 'none';
        }
        
        if (this.startBtn) {
            this.startBtn.disabled = false;
        }
        
        this.isRecording = false;
        this.pollAttempts = 0;
    }
    
    /**
     * Start recording session
     */
    async startRecording() {
        console.log('🎙️ Starting recording...');
        
        // ==================== VALIDATE FORM ====================
        if (this.form && !this.form.checkValidity()) {
            console.error('❌ Form validation failed');
            this.showStatus('❌ Please fill all required fields', 'error');
            return;
        }
        
        // ==================== GET FORM VALUES ====================
        const refFreq = parseFloat(document.getElementById('refFreq')?.value || 100);
        const targetFreq = parseFloat(document.getElementById('targetFreq')?.value || 93.8);
        const numLoops = parseInt(document.getElementById('numLoops')?.value || 1);
        const syncMode = document.querySelector('input[name="syncMode"]:checked')?.value || 'ntp';
        
        console.log('📋 Form values:');
        console.log(`   Reference Frequency: ${refFreq} MHz`);
        console.log(`   Target Frequency: ${targetFreq} MHz`);
        console.log(`   Loops: ${numLoops}`);
        console.log(`   Sync Mode: ${syncMode}`);
        
        // ==================== VALIDATE FREQUENCIES ====================
        if (!Validators.isFrequency(refFreq)) {
            console.error('❌ Invalid reference frequency');
            this.showStatus('❌ Reference frequency must be between 87-108 MHz', 'error');
            return;
        }

        // DENGAN ini:
        if (!Validators.isFrequency(refFreq) || refFreq < 87 || refFreq > 108) {
            console.error('❌ Invalid reference frequency');
            this.showStatus('❌ Reference frequency must be between 87-108 MHz', 'error');
            return;
        }

        if (!Validators.isFrequency(targetFreq) || targetFreq < 87 || targetFreq > 108) {
            console.error('❌ Invalid target frequency');
            this.showStatus('❌ Target frequency must be between 87-108 MHz', 'error');
            return;
        }
        
        // ==================== PREPARE REQUEST ====================
        const payload = {
            fref_mhz: refFreq,
            fcari_mhz: targetFreq,
            loops: numLoops,
            sync_mode: syncMode
        };
        
        console.log('📤 Sending request to API:', payload);
        
        // Disable button and show status
        if (this.startBtn) this.startBtn.disabled = true;
        this.showStatus('🔄 Initializing recording session...', 'warning');
        
        try {
            // ==================== SEND API REQUEST ====================
            const response = await API.startRecording(refFreq, targetFreq, numLoops, syncMode);
            
            if (!response.success) {
                throw new Error(response.error || 'Failed to start recording');
            }
            
            const sessionId = response.data.session_id;
            
            console.log('✓ Recording started with session ID:', sessionId);
            
            this.currentSessionId = sessionId;
            this.isRecording = true;
            this.pollAttempts = 0;
            this.recordingStartTime = Date.now();
            
            // ==================== SHOW INITIAL STATUS ====================
            this.showStatus(
                `✓ Recording Session Started!\n` +
                `Session ID: ${sessionId}\n` +
                `Config: ${refFreq}/${targetFreq} MHz, Loops: ${numLoops}, Sync: ${syncMode.toUpperCase()}\n` +
                `Monitoring progress...`,
                'success'
            );
            
            // Show progress bar
            if (this.progressContainer) {
                this.progressContainer.style.display = 'block';
            }
            this.updateProgress(10, 'Initializing...');
            
            // ==================== START POLLING ====================
            this.startPolling(sessionId);
            
        } catch (error) {
            console.error('❌ Error:', error.message);
            this.showStatus(`❌ Error: ${error.message}`, 'error');
            if (this.startBtn) this.startBtn.disabled = false;
            this.isRecording = false;
        }
    }
    
    /**
     * Start polling for recording status
     */
    startPolling(sessionId) {
        console.log('⏱️ Starting status polling for session:', sessionId);
        
        this.pollInterval = setInterval(async () => {
            try {
                this.pollAttempts++;
                
                // ==================== FETCH STATUS ====================
                const response = await API.getRecordingStatus(sessionId);
                
                if (!response.success) {
                    console.warn(`[Poll ${this.pollAttempts}] Failed to get status:`, response.error);
                    return;
                }
                
                const data = response.data;
                console.log(`[Poll ${this.pollAttempts}] Status:`, data.status);
                
                // ==================== HANDLE DIFFERENT STATUSES ====================
                if (data.status === 'COMPLETE' || data.status === 'completed') {
                    this.handleRecordingCompleted(data);
                    
                } else if (data.status === 'ERROR' || data.status === 'failed') {
                    this.handleRecordingFailed(data);
                    
                } else {
                    this.handleRecordingProgress(data);
                }
                
                // ==================== CHECK MAX ATTEMPTS ====================
                if (this.pollAttempts >= this.maxPollAttempts) {
                    console.warn('⚠️ Max poll attempts reached');
                    this.handleRecordingTimeout();
                }
                
            } catch (error) {
                console.error('Polling error:', error.message);
                // Continue polling even on error
            }
        }, 2000);  // Poll every 2 seconds
    }
    
    /**
     * Stop polling
     */
    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
            console.log('⏹️ Polling stopped');
        }
    }
    
    /**
     * Handle recording progress
     */
    handleRecordingProgress(data) {
        const elapsed = data.elapsed_seconds || 0;
        const progress = Math.min(90, 10 + (this.pollAttempts * 0.3));
        
        this.updateProgress(progress, data.progress || 'Recording in progress...');
        
        const statusMsg = 
            `⏳ Recording in Progress\n` +
            `Status: ${data.progress || 'Processing...'}\n` +
            `Loop: ${data.current_loop || 1}/${data.total_loops || 1}\n` +
            `Elapsed: ${StringUtils.formatDuration(elapsed)}`;
        
        this.showStatus(statusMsg, 'warning');
    }
    
    /**
     * Handle recording completed
     */
    handleRecordingCompleted(data) {
        console.log('✓ Recording completed:', data);
        
        this.stopPolling();
        this.isRecording = false;
        if (this.startBtn) this.startBtn.disabled = false;
        
        this.updateProgress(100, 'Recording completed!');
        
        const elapsedSeconds = Math.floor((Date.now() - this.recordingStartTime) / 1000);
        const statusMsg = 
            `✓ Recording Completed Successfully!\n` +
            `Files Downloaded: ${data.files_count || 0}\n` +
            `Total Size: ${StringUtils.formatBytes(data.total_size_bytes || 0)}\n` +
            `Elapsed Time: ${StringUtils.formatDuration(elapsedSeconds)}`;
        
        this.showStatus(statusMsg, 'success');
        
        // Show toast notification
        if (typeof showToast === 'function') {
            showToast('Recording completed successfully!', 'success');
        }
        
        // Auto-close after 5 seconds
        setTimeout(() => {
            this.close();
            if (typeof location !== 'undefined') {
                location.reload();
            }
        }, 5000);
    }
    
    /**
     * Handle recording failed
     */
    handleRecordingFailed(data) {
        console.error('✗ Recording failed:', data);
        
        this.stopPolling();
        this.isRecording = false;
        if (this.startBtn) this.startBtn.disabled = false;
        
        if (this.progressContainer) {
            this.progressContainer.style.display = 'none';
        }
        
        const statusMsg = 
            `✗ Recording Failed!\n` +
            `Error: ${data.error || 'Unknown error'}\n` +
            `Elapsed: ${StringUtils.formatDuration(data.elapsed_seconds || 0)}`;
        
        this.showStatus(statusMsg, 'error');
        
        // Show toast notification
        if (typeof showToast === 'function') {
            showToast(`Recording error: ${data.error}`, 'error');
        }
    }
    
    /**
     * Handle recording timeout
     */
    handleRecordingTimeout() {
        console.error('⚠️ Recording polling timeout');
        
        this.stopPolling();
        this.isRecording = false;
        if (this.startBtn) this.startBtn.disabled = false;
        
        this.showStatus('⚠️ Recording timeout (max polling attempts exceeded)', 'error');
        
        // Show toast notification
        if (typeof showToast === 'function') {
            showToast('Recording timeout - max polling attempts reached', 'warning');
        }
    }
    
    /**
     * Show status message
     */
    showStatus(message, type = 'info') {
        if (!this.statusDisplay) return;
        
        this.statusDisplay.style.display = 'block';
        this.statusDisplay.className = `status-box ${type}`;
        this.statusDisplay.textContent = message;
    }
    
    /**
     * Update progress bar
     */
    updateProgress(percentage, text = '') {
        if (this.progressFill) {
            this.progressFill.style.width = percentage + '%';
            this.progressFill.textContent = `${Math.round(percentage)}%`;
        }
        
        if (text && this.progressText) {
            this.progressText.textContent = text;
        }
    }
}

// ==================== INITIALIZE ON DOM READY ====================
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Initializing Recording Dialog...');
    
    // Create dialog instance
    window.recordingDialog = new RecordingDialog();
    
    // Attach to "Start Recording" button
    const recordBtn = document.getElementById('recordBtn');
    if (recordBtn) {
        recordBtn.addEventListener('click', (e) => {
            e.preventDefault();
            console.log('🎙️ Record button clicked');
            if (window.recordingDialog) {
                window.recordingDialog.show();
            }
        });
        console.log('✓ Record button found and attached');
    } else {
        console.warn('⚠️ Record button not found');
    }
});