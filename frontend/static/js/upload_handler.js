/**
 * Multi-File Upload Handler untuk TDOA System
 * Menangani upload 3 files sekaligus dari berbagai receiver
 */

class TDOAMultiUploadHandler {
    constructor() {
        this.sessions = [];
        this.currentSessionIdx = 0;
        this.initUploadModal();
    }

    // ==================== CREATE UPLOAD MODAL ====================
    initUploadModal() {
        // Check if modal sudah exist
        if (document.getElementById('tdoa-upload-modal')) {
            return;
        }

        const modal = document.createElement('div');
        modal.id = 'tdoa-upload-modal';
        modal.className = 'modal';
        modal.style.display = 'none';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 900px; max-height: 90vh; overflow-y: auto;">
                <div class="modal-header">
                    <h2><i class="fas fa-cloud-upload-alt"></i> Upload TDOA IQ Data Files</h2>
                    <button type="button" class="close-btn" onclick="this.closest('.modal').style.display='none';">&times;</button>
                </div>

                <div class="modal-body" style="padding: 20px;">
                    
                    <!-- Info Box -->
                    <div style="background: #e7f5ff; border-left: 4px solid #339af0; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
                        <strong><i class="fas fa-info-circle"></i> Upload Instructions:</strong><br>
                        <small>
                            Upload 3 .dat files from different receivers (Rx1, Rx2, Rx3) that were recorded at the same time.<br>
                            Recommended naming: <code>receiver_id_freq_date_time.dat</code><br>
                            Example: <code>1_1000_980_2025_11_6_14_35.dat</code>, <code>2_1000_980_2025_11_6_14_35.dat</code>, <code>3_1000_980_2025_11_6_14_35.dat</code>
                        </small>
                    </div>

                    <!-- Recording Sessions Container -->
                    <div id="upload-sessions-container">
                        <!-- Sessions akan ditambah di sini -->
                    </div>

                    <!-- Add Session Button -->
                    <button type="button" class="btn-primary" id="add-session-btn" style="margin-bottom: 20px;">
                        <i class="fas fa-plus"></i> Add Another Session
                    </button>

                    <!-- Global Config -->
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
                        <h4><i class="fas fa-cog"></i> Processing Configuration</h4>
                        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px;">
                            <div>
                                <label>Sample Rate (MSPS):</label>
                                <input type="number" id="global-sample-rate" value="2.4" min="0.1" step="0.1" 
                                       style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                                <small style="color: #999;">Default: 2.4 MSPS (RTL-SDR)</small>
                            </div>
                            <div>
                                <label>Reference Frequency (MHz):</label>
                                <input type="number" id="global-ref-freq" value="100.0" min="87" max="108" step="0.1"
                                       style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                                <small style="color: #999;">FM Band: 87-108 MHz</small>
                            </div>
                            <div>
                                <label>Target Frequency (MHz):</label>
                                <input type="number" id="global-target-freq" value="93.8" min="87" max="108" step="0.1"
                                       style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                                <small style="color: #999;">Signal to localize</small>
                            </div>
                        </div>
                    </div>

                    <!-- Progress -->
                    <div id="upload-progress-container" style="display: none; margin-bottom: 20px;">
                        <p><strong>Uploading:</strong> <span id="upload-progress-text">0/0</span></p>
                        <div class="progress-bar" style="margin-bottom: 10px;">
                            <div id="upload-progress-fill" class="progress-fill" style="width: 0%;"></div>
                        </div>
                        <p id="upload-status-text" style="font-size: 12px; color: #666;"></p>
                    </div>

                    <!-- Status Display -->
                    <div id="upload-status-display" style="display: none; margin-bottom: 20px; padding: 15px; border-radius: 6px;"></div>

                </div>

                <div class="modal-footer" style="border-top: 1px solid #ddd; padding: 15px; display: flex; gap: 10px; justify-content: flex-end;">
                    <button type="button" class="btn-secondary" onclick="document.getElementById('tdoa-upload-modal').style.display='none';">
                        Cancel
                    </button>
                    <button type="button" class="btn-primary" id="start-upload-btn" disabled>
                        <i class="fas fa-upload"></i> Upload & Process All
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Event listeners
        document.getElementById('add-session-btn').addEventListener('click', () => this.addSession());
        document.getElementById('start-upload-btn').addEventListener('click', () => this.startUpload());

        // Add default session
        this.addSession();
    }

    // ==================== ADD SESSION ====================
    addSession() {
        const sessionIdx = this.sessions.length;
        const sessionId = `session_${Date.now()}_${sessionIdx}`;
        
        this.sessions.push({
            id: sessionId,
            receiver1: null,
            receiver2: null,
            receiver3: null
        });

        const container = document.getElementById('upload-sessions-container');
        
        const sessionDiv = document.createElement('div');
        sessionDiv.id = sessionId;
        sessionDiv.className = 'upload-session-card';
        sessionDiv.style.cssText = `
            background: white;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            transition: all 0.3s ease;
        `;

        sessionDiv.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h4 style="margin: 0;">
                    <i class="fas fa-folder"></i> Recording Session #${sessionIdx + 1}
                </h4>
                ${sessionIdx > 0 ? `
                    <button type="button" class="btn-secondary btn-sm" onclick="window.tdoaUploader.removeSession('${sessionId}')">
                        <i class="fas fa-trash"></i> Remove
                    </button>
                ` : ''}
            </div>

            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 15px;">
                ${this.createReceiverUploadBox(sessionId, 'receiver1', 'Receiver 1')}
                ${this.createReceiverUploadBox(sessionId, 'receiver2', 'Receiver 2')}
                ${this.createReceiverUploadBox(sessionId, 'receiver3', 'Receiver 3')}
            </div>

            <div id="session-status-${sessionId}" style="font-size: 12px; color: #999; text-align: center; padding: 10px;">
                ⏳ Waiting for files...
            </div>
        `;

        container.appendChild(sessionDiv);

        // Setup drag & drop
        this.setupDropZones(sessionId);
    }

    // ==================== CREATE RECEIVER UPLOAD BOX ====================
    createReceiverUploadBox(sessionId, receiverId, label) {
        return `
            <div class="receiver-upload-box" data-session="${sessionId}" data-receiver="${receiverId}"
                 style="
                    border: 2px dashed #ccc;
                    border-radius: 8px;
                    padding: 20px;
                    text-align: center;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    background: #fafafa;
                 ">
                <div style="color: #666; margin-bottom: 10px;">
                    <i class="fas fa-microchip" style="font-size: 24px; color: #667eea;"></i>
                </div>
                <strong style="display: block; margin-bottom: 5px;">${label}</strong>
                <small style="color: #999; display: block; margin-bottom: 10px;">Drag .dat file or click</small>
                
                <div class="file-selected-info" style="display: none; margin-top: 10px; color: #51cf66;">
                    <i class="fas fa-check-circle"></i>
                    <span class="file-name"></span><br>
                    <small class="file-size"></small>
                </div>

                <input type="file" accept=".dat,.iq" style="display: none;" class="file-input">
            </div>
        `;
    }

    // ==================== SETUP DROP ZONES ====================
    setupDropZones(sessionId) {
        const sessionDiv = document.getElementById(sessionId);
        const boxes = sessionDiv.querySelectorAll('.receiver-upload-box');

        boxes.forEach(box => {
            const receiverId = box.dataset.receiver;
            const fileInput = box.querySelector('.file-input');

            // Click to browse
            box.addEventListener('click', () => {
                box.querySelector('input[type="file"]').click();
            });

            // File input change
            box.querySelector('input[type="file"]').addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.selectFile(sessionId, receiverId, e.target.files[0], box);
                }
            });

            // Drag over
            box.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.stopPropagation();
                box.style.borderColor = '#667eea';
                box.style.background = 'rgba(102, 126, 234, 0.05)';
            });

            // Drag leave
            box.addEventListener('dragleave', () => {
                box.style.borderColor = '#ccc';
                box.style.background = '#fafafa';
            });

            // Drop
            box.addEventListener('drop', (e) => {
                e.preventDefault();
                e.stopPropagation();
                box.style.borderColor = '#ccc';
                box.style.background = '#fafafa';

                if (e.dataTransfer.files.length > 0) {
                    const file = e.dataTransfer.files[0];
                    this.selectFile(sessionId, receiverId, file, box);
                    box.querySelector('input[type="file"]').files = e.dataTransfer.files;
                }
            });
        });
    }

    // ==================== SELECT FILE ====================
    selectFile(sessionId, receiverId, file, box) {
        // Validate file
        if (!file.name.endsWith('.dat') && !file.name.endsWith('.iq')) {
            showAlert('❌ Only .dat or .iq files allowed', 'error');
            return;
        }

        // Store file
        const sessionIdx = this.sessions.findIndex(s => s.id === sessionId);
        this.sessions[sessionIdx][receiverId] = {
            file: file,
            name: file.name,
            size: file.size
        };

        // Update UI
        box.style.borderColor = '#51cf66';
        const info = box.querySelector('.file-selected-info');
        info.style.display = 'block';
        info.querySelector('.file-name').textContent = file.name;
        info.querySelector('.file-size').textContent = `${(file.size / (1024 * 1024)).toFixed(2)} MB`;

        // Check session completion
        this.checkSessionCompletion(sessionId);
    }

    // ==================== CHECK SESSION COMPLETION ====================
    checkSessionCompletion(sessionId) {
        const sessionIdx = this.sessions.findIndex(s => s.id === sessionId);
        const session = this.sessions[sessionIdx];

        const isComplete = session.receiver1 && session.receiver2 && session.receiver3;
        const statusDiv = document.getElementById(`session-status-${sessionId}`);

        if (isComplete) {
            const totalSize = (session.receiver1.size + session.receiver2.size + session.receiver3.size) / (1024 * 1024);
            statusDiv.innerHTML = `<span style="color: #51cf66;">✓ Complete (${totalSize.toFixed(1)} MB)</span>`;
            statusDiv.style.color = '#51cf66';
        } else {
            const count = [session.receiver1, session.receiver2, session.receiver3].filter(Boolean).length;
            statusDiv.innerHTML = `<span style="color: #ffc107;">⚠ ${count}/3 files selected</span>`;
            statusDiv.style.color = '#ffc107';
        }

        // Check if all sessions complete
        this.updateUploadButton();
    }

    // ==================== UPDATE UPLOAD BUTTON ====================
    updateUploadButton() {
        const allComplete = this.sessions.every(s => s.receiver1 && s.receiver2 && s.receiver3);
        const btn = document.getElementById('start-upload-btn');
        
        btn.disabled = !allComplete;
        
        if (allComplete) {
            btn.style.opacity = '1';
            btn.style.cursor = 'pointer';
        } else {
            btn.style.opacity = '0.5';
            btn.style.cursor = 'not-allowed';
        }
    }

    // ==================== REMOVE SESSION ====================
    removeSession(sessionId) {
        const idx = this.sessions.findIndex(s => s.id === sessionId);
        if (idx > -1) {
            this.sessions.splice(idx, 1);
        }

        const div = document.getElementById(sessionId);
        if (div) {
            div.remove();
        }

        if (this.sessions.length === 0) {
            this.addSession();
        }

        this.updateUploadButton();
    }

    // ==================== START UPLOAD ====================
    async startUpload() {
        const sampleRate = parseFloat(document.getElementById('global-sample-rate').value);
        const refFreq = parseFloat(document.getElementById('global-ref-freq').value);
        const targetFreq = parseFloat(document.getElementById('global-target-freq').value);

        // Validate
        if (isNaN(sampleRate) || sampleRate <= 0) {
            showAlert('Invalid sample rate', 'error');
            return;
        }

        if (isNaN(refFreq) || refFreq < 87 || refFreq > 108) {
            showAlert('Invalid reference frequency', 'error');
            return;
        }

        if (isNaN(targetFreq) || targetFreq < 87 || targetFreq > 108) {
            showAlert('Invalid target frequency', 'error');
            return;
        }

        if (refFreq === targetFreq) {
            showAlert('Reference and target frequencies must be different', 'error');
            return;
        }

        // Start upload
        console.log('Starting upload with config:', { sampleRate, refFreq, targetFreq });

        const totalSessions = this.sessions.length;
        let completedSessions = 0;

        document.getElementById('upload-progress-container').style.display = 'block';
        document.getElementById('start-upload-btn').disabled = true;

        for (const session of this.sessions) {
            await this.uploadSession(session, sampleRate, refFreq, targetFreq);
            completedSessions++;
            
            const progress = Math.round((completedSessions / totalSessions) * 100);
            document.getElementById('upload-progress-fill').style.width = `${progress}%`;
            document.getElementById('upload-progress-text').textContent = `${completedSessions}/${totalSessions}`;
        }

        showAlert(`✓ Uploaded ${totalSessions} session(s)!`, 'success');
        
        document.getElementById('upload-progress-container').style.display = 'none';
        document.getElementById('start-upload-btn').disabled = false;

        setTimeout(() => {
            document.getElementById('tdoa-upload-modal').style.display = 'none';
            // Reload imported files
            if (window.loadImportedFiles) {
                window.loadImportedFiles();
            }
        }, 1500);
    }

    // ==================== UPLOAD SESSION ====================
    async uploadSession(session, sampleRate, refFreq, targetFreq) {
        const fileIds = [];
        const files = [session.receiver1, session.receiver2, session.receiver3];

        for (let i = 0; i < files.length; i++) {
            const fileObj = files[i];
            const statusText = document.getElementById('upload-status-text');
            
            statusText.textContent = `Uploading: ${fileObj.name}...`;

            try {
                const formData = new FormData();
                formData.append('file', fileObj.file);
                formData.append('sample_rate', sampleRate * 1e6);

                const response = await fetch('/api/import-file', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    throw new Error(`Upload failed: ${response.statusText}`);
                }

                const result = await response.json();

                if (result.file_id) {
                    fileIds.push(result.file_id);
                }

            } catch (error) {
                console.error(`Error uploading ${fileObj.name}:`, error);
                showAlert(`❌ Failed to upload ${fileObj.name}`, 'error');
            }
        }

        // Process files if all uploaded
        if (fileIds.length === 3) {
            document.getElementById('upload-status-text').textContent = 
                `Processing ${fileIds.length} files for TDOA...`;

            try {
                const response = await fetch('/api/process-multiple-files', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        file_ids: fileIds,
                        ref_freq_mhz: refFreq,
                        target_freq_mhz: targetFreq
                    })
                });

                if (!response.ok) {
                    throw new Error(`Processing failed: ${response.statusText}`);
                }

                const result = await response.json();
                console.log('✓ Processing result:', result);

            } catch (error) {
                console.error('Processing error:', error);
                showAlert('❌ Processing failed', 'error');
            }
        }
    }

    // ==================== SHOW MODAL ====================
    show() {
        // Reset
        this.sessions = [];
        document.getElementById('upload-sessions-container').innerHTML = '';
        document.getElementById('start-upload-btn').disabled = true;
        
        this.addSession();
        document.getElementById('tdoa-upload-modal').style.display = 'block';
    }
}

// Initialize
typeof window !== 'undefined' && (window.tdoaUploader = null);
document.addEventListener('DOMContentLoaded', () => {
    window.tdoaUploader = new TDOAMultiUploadHandler();
    console.log('✓ TDOA Multi-Upload Handler Initialized');
});

