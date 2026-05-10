"""
Main Flask Application
TDOA Automation System with Recording Automation
Complete & Production-Ready Version
"""

from flask import Flask, render_template, request, jsonify, send_file
from pathlib import Path
from loguru import logger
import json
from datetime import datetime
import os
import sys

# ==================== IMPORT BACKEND MODULES ====================
try:
    from backend import ConfigManager
    from backend.recorder_manager import RecorderManager
    from backend.recording_service import RecordingService
except ImportError as e:
    logger.warning(f"Backend import error: {e}")
    ConfigManager = None
    RecorderManager = None
    RecordingService = None

# ==================== INITIALIZE FLASK ====================
app = Flask(__name__, 
           template_folder='frontend/templates',
           static_folder='frontend/static')

app.config['JSON_SORT_KEYS'] = False
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max upload

# ==================== SETUP LOGGING ====================
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

logger.add(
    str(log_dir / "app.log"),
    rotation="500 MB",
    retention="7 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)

logger.info("=" * 100)
logger.info("🚀 TDOA Automation System - Starting")
logger.info("=" * 100)

# ==================== INITIALIZE SERVICES ====================
config_manager = None
recording_service = None
recorder_manager = None

try:
    # Load configuration
    if Path('config.json').exists():
        config_manager = ConfigManager('config.json')
        logger.info("✓ ConfigManager initialized")
    else:
        logger.warning("⚠️ config.json not found - using defaults")
        config_manager = None
        
except Exception as e:
    logger.error(f"❌ Failed to initialize ConfigManager: {str(e)}", exc_info=True)
    config_manager = None

try:
    # Initialize Recording Service
    if config_manager:
        recording_service = RecordingService(config_manager)
        logger.info("✓ RecordingService initialized")
    else:
        recording_service = None
        logger.warning("⚠️ RecordingService not initialized (no config)")
        
except Exception as e:
    logger.error(f"❌ Failed to initialize RecordingService: {str(e)}", exc_info=True)
    recording_service = None

try:
    # Initialize Recorder Manager
    if config_manager:
        recorder_manager = RecorderManager(config_manager)
        logger.info("✓ RecorderManager initialized")
    else:
        recorder_manager = None
        
except Exception as e:
    logger.error(f"⚠️ RecorderManager not available: {str(e)}")
    recorder_manager = None

# ==================== HELPER FUNCTIONS ====================

def get_system_status():
    """Get current system status"""
    try:
        status = {
            'system': 'running',
            'version': '1.0.0',
            'environment': 'production' if not os.environ.get('MOCK_MODE') else 'mock',
            'services': {
                'config_manager': 'active' if config_manager else 'inactive',
                'recording_service': 'active' if recording_service else 'inactive',
                'recorder_manager': 'active' if recorder_manager else 'inactive'
            },
            'timestamp': datetime.now().isoformat()
        }
        return status
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return {'error': str(e)}

def validate_recording_request(data):
    """Validate recording request data"""
    errors = []
    
    # Check required fields
    required = ['fref_mhz', 'fcari_mhz', 'loops', 'sync_mode']
    for field in required:
        if field not in data:
            errors.append(f"Missing field: {field}")
    
    if errors:
        return {'valid': False, 'errors': errors}
    
    try:
        # Validate types and ranges
        fref = float(data['fref_mhz'])
        fcari = float(data['fcari_mhz'])
        loops = int(data['loops'])
        sync = str(data['sync_mode']).lower()
        
        # Range checks
        if not (87 <= fref <= 108):
            errors.append(f"Reference frequency {fref} out of range (87-108 MHz)")
        if not (87 <= fcari <= 108):
            errors.append(f"Target frequency {fcari} out of range (87-108 MHz)")
        if fref == fcari:
            errors.append("Frequencies must be different")
        if not (1 <= loops <= 100):
            errors.append(f"Loops {loops} out of range (1-100)")
        if sync not in ['ntp', 'gps']:
            errors.append(f"Invalid sync mode: {sync}")
        
        if errors:
            return {'valid': False, 'errors': errors}
        
        return {
            'valid': True,
            'data': {
                'fref_mhz': fref,
                'fcari_mhz': fcari,
                'loops': loops,
                'sync_mode': sync
            }
        }
        
    except (ValueError, TypeError) as e:
        return {'valid': False, 'errors': [f"Type error: {str(e)}"]}

# ==================== ROUTES - PAGES ====================

@app.route('/')
def dashboard():
    """Dashboard page"""
    logger.debug("GET /")
    return render_template('dashboard.html')

@app.route('/receivers')
def receivers():
    """Receivers page"""
    logger.debug("GET /receivers")
    return render_template('dashboard.html')  # Use dashboard for now

@app.route('/tdoa')
def tdoa():
    """TDOA page"""
    logger.debug("GET /tdoa")
    return render_template('dashboard.html')

@app.route('/results')
def results():
    """Results page"""
    logger.debug("GET /results")
    return render_template('dashboard.html')

# ==================== API ROUTES - SYSTEM ====================

@app.route('/api/status', methods=['GET'])
def api_status():
    """Get system status"""
    try:
        logger.debug("GET /api/status")
        status = get_system_status()
        return jsonify(status), 200
    except Exception as e:
        logger.error(f"Error in /api/status: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['GET'])
def api_get_config():
    """Get configuration"""
    try:
        logger.debug("GET /api/config")
        
        if not config_manager:
            return jsonify({
                'status': 'error',
                'message': 'Configuration not available'
            }), 503
        
        config_data = config_manager.get_config()
        
        return jsonify({
            'status': 'success',
            'config': config_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting config: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/receivers', methods=['GET'])
def api_get_receivers():
    """Get receivers list"""
    try:
        logger.debug("GET /api/receivers")
        
        if not config_manager:
            return jsonify({
                'status': 'error',
                'receivers': []
            }), 200
        
        config = config_manager.get_config()
        receivers = config.get('receivers', [])
        
        return jsonify({
            'status': 'success',
            'receivers': receivers
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting receivers: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

# ==================== API ROUTES - RECORDING ====================

@app.route('/api/recording/start', methods=['POST'])
def api_start_recording():
    """
    Start recording session via API
    
    POST /api/recording/start
    Content-Type: application/json
    
    Request Body:
    {
        "fref_mhz": 100.0,
        "fcari_mhz": 93.8,
        "loops": 1,
        "sync_mode": "ntp"
    }
    
    Response (200 OK):
    {
        "session_id": "abc12345",
        "status": "initializing"
    }
    
    Response (400 Bad Request):
    {
        "error": "Missing required fields"
    }
    """
    try:
        logger.info("🎙️ POST /api/recording/start - Start recording request received")
        
        # ==================== CHECK IF SERVICE INITIALIZED ====================
        if recording_service is None:
            logger.error("❌ RecordingService not initialized")
            return jsonify({'error': 'Recording service not available'}), 503
        
        # ==================== GET JSON DATA ====================
        data = request.get_json()
        
        if not data:
            logger.error("❌ No JSON data provided")
            return jsonify({'error': 'Request body must be JSON'}), 400
        
        logger.debug(f"Request data: {data}")
        
        # ==================== VALIDATE REQUEST ====================
        validation = validate_recording_request(data)
        
        if not validation['valid']:
            error_msg = "; ".join(validation['errors'])
            logger.error(f"❌ Validation failed: {error_msg}")
            return jsonify({'error': error_msg}), 400
        
        validated_data = validation['data']
        
        # ==================== LOG VALIDATED PARAMETERS ====================
        logger.info(f"📋 Recording parameters validated:")
        logger.info(f"   Reference Frequency: {validated_data['fref_mhz']} MHz")
        logger.info(f"   Target Frequency: {validated_data['fcari_mhz']} MHz")
        logger.info(f"   Loops: {validated_data['loops']}")
        logger.info(f"   Sync Mode: {validated_data['sync_mode'].upper()}")
        
        # ==================== START RECORDING ====================
        try:
            result = recording_service.start_recording(
                fref_mhz=validated_data['fref_mhz'],
                fcari_mhz=validated_data['fcari_mhz'],
                loops=validated_data['loops'],
                sync_mode=validated_data['sync_mode']
            )
            
            logger.info(f"✓ Recording session started: {result['session_id']}")
            
            return jsonify(result), 200
            
        except Exception as e:
            error_msg = f"Failed to start recording: {str(e)}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            return jsonify({'error': error_msg}), 500
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"❌ {error_msg}", exc_info=True)
        return jsonify({'error': error_msg}), 500

@app.route('/api/recording/status/<session_id>', methods=['GET'])
def api_get_recording_status(session_id):
    """
    Get status of recording session
    
    GET /api/recording/status/{session_id}
    
    Response (200 OK):
    {
        "session_id": "abc12345",
        "status": "recording",
        "progress": "Waiting for recording to complete...",
        "elapsed_seconds": 45.2,
        "files_count": 0,
        "total_size_mb": 0,
        "error": null
    }
    
    Response (404 Not Found):
    {
        "error": "Session not found",
        "session_id": "invalid_id"
    }
    """
    try:
        logger.debug(f"GET /api/recording/status/{session_id}")
        
        # ==================== CHECK IF SERVICE INITIALIZED ====================
        if recording_service is None:
            logger.error("❌ RecordingService not initialized")
            return jsonify({'error': 'Recording service not available'}), 503
        
        # ==================== GET SESSION STATUS ====================
        status = recording_service.get_session_status(session_id)
        
        # ==================== CHECK IF SESSION EXISTS ====================
        if 'error' in status:
            logger.warning(f"⚠️ Session not found: {session_id}")
            return jsonify(status), 404
        
        logger.debug(f"✓ Session status: {status.get('status', 'unknown')}")
        
        return jsonify(status), 200
        
    except Exception as e:
        error_msg = f"Error getting status: {str(e)}"
        logger.error(f"❌ {error_msg}", exc_info=True)
        return jsonify({'error': error_msg}), 500

@app.route('/api/recording/list', methods=['GET'])
def api_list_recording_sessions():
    """
    List all recording sessions
    
    GET /api/recording/list
    
    Response (200 OK):
    {
        "sessions": [
            {
                "session_id": "abc12345",
                "status": "completed",
                "files_count": 3,
                "total_size_mb": 150.5
            },
            ...
        ],
        "total_count": 2
    }
    """
    try:
        logger.debug("GET /api/recording/list")
        
        # ==================== CHECK IF SERVICE INITIALIZED ====================
        if recording_service is None:
            logger.error("❌ RecordingService not initialized")
            return jsonify({'error': 'Recording service not available'}), 503
        
        # ==================== BUILD SESSION LIST ====================
        sessions_list = []
        
        if hasattr(recording_service, 'sessions'):
            for session_id, session in recording_service.sessions.items():
                elapsed = (datetime.now() - session.start_time).total_seconds() if hasattr(session, 'start_time') else 0
                
                sessions_list.append({
                    'session_id': session_id,
                    'status': getattr(session, 'status', 'unknown'),
                    'fref_mhz': getattr(session, 'fref_mhz', 0),
                    'fcari_mhz': getattr(session, 'fcari_mhz', 0),
                    'loops': getattr(session, 'loops', 0),
                    'sync_mode': getattr(session, 'sync_mode', 'ntp'),
                    'files_count': len(getattr(session, 'files_downloaded', [])),
                    'total_size_mb': getattr(session, 'total_size_mb', 0),
                    'elapsed_seconds': elapsed
                })
        
        logger.info(f"✓ Listing {len(sessions_list)} recording sessions")
        
        return jsonify({
            'sessions': sessions_list,
            'total_count': len(sessions_list)
        }), 200
        
    except Exception as e:
        error_msg = f"Error listing sessions: {str(e)}"
        logger.error(f"❌ {error_msg}", exc_info=True)
        return jsonify({'error': error_msg}), 500

@app.route('/api/recording/cancel/<session_id>', methods=['POST'])
def api_cancel_recording(session_id):
    """Cancel a recording session"""
    try:
        logger.info(f"POST /api/recording/cancel/{session_id}")
        
        if not recording_service:
            return jsonify({'error': 'Recording service not available'}), 503
        
        # Implement cancellation logic
        result = recording_service.cancel_session(session_id)
        
        if 'error' in result:
            return jsonify(result), 400
        
        logger.info(f"✓ Recording session cancelled: {session_id}")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error cancelling session: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

# ==================== API ROUTES - FILES ====================

@app.route('/api/files', methods=['GET'])
def api_get_files():
    """Get list of recorded files"""
    try:
        logger.debug("GET /api/files")
        
        files = []
        data_dir = Path('./output/recorded_data')
        
        if data_dir.exists():
            files = [f.name for f in data_dir.glob('*.iq') if f.is_file()]
        
        return jsonify({
            'status': 'success',
            'files': files,
            'directory': str(data_dir),
            'count': len(files)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting files: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

# ==================== API ROUTES - MAPS ====================

@app.route('/api/maps', methods=['GET'])
def api_get_maps():
    """Get list of generated maps"""
    try:
        logger.debug("GET /api/maps")
        
        maps = []
        maps_dir = Path('./output/maps')
        
        if maps_dir.exists():
            maps = [f.name for f in maps_dir.glob('*.html') if f.is_file()]
        
        return jsonify({
            'status': 'success',
            'maps': sorted(maps, reverse=True),
            'directory': str(maps_dir),
            'count': len(maps)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting maps: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-map/<filename>', methods=['GET'])
def api_download_map(filename):
    """Download a specific map"""
    try:
        logger.debug(f"GET /api/download-map/{filename}")
        
        maps_dir = Path('./output/maps')
        file_path = maps_dir / filename
        
        if not file_path.exists():
            return jsonify({'error': 'Map not found'}), 404
        
        logger.info(f"✓ Downloading map: {filename}")
        return send_file(file_path, as_attachment=True, mimetype='text/html')
        
    except Exception as e:
        logger.error(f"Error downloading map: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

# ==================== API ROUTES - DOWNLOAD ====================

@app.route('/api/download-results', methods=['GET'])
def api_download_results():
    """Download all results as ZIP"""
    try:
        logger.debug("GET /api/download-results")
        
        import zipfile
        import io
        
        results_dir = Path('./output')
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in results_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(results_dir)
                    zf.write(file_path, arcname)
        
        zip_buffer.seek(0)
        
        logger.info("✓ Results downloaded")
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'tdoa-results-{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
        )
        
    except Exception as e:
        logger.error(f"Error downloading results: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    """404 Not Found handler"""
    logger.warning(f"404 Not Found: {request.path}")
    return jsonify({'error': 'Endpoint not found', 'path': request.path}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """405 Method Not Allowed handler"""
    logger.warning(f"405 Method Not Allowed: {request.method} {request.path}")
    return jsonify({'error': 'Method not allowed'}), 405

@app.errorhandler(500)
def internal_error(error):
    """500 Internal Server Error handler"""
    logger.error(f"500 Internal Server Error: {str(error)}", exc_info=True)
    return jsonify({'error': 'Internal server error', 'message': str(error)}), 500

@app.errorhandler(503)
def service_unavailable(error):
    """503 Service Unavailable handler"""
    logger.error(f"503 Service Unavailable: {str(error)}")
    return jsonify({'error': 'Service unavailable'}), 503

# ==================== REQUEST/RESPONSE HANDLERS ====================

@app.before_request
def before_request():
    """Log incoming requests"""
    logger.debug(f"{request.method} {request.path}")

@app.after_request
def after_request(response):
    """Log outgoing responses"""
    logger.debug(f"Response: {response.status_code}")
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

# ==================== MAIN ====================

if __name__ == '__main__':
    logger.info("=" * 100)
    logger.info(f"🌐 Starting Flask development server")
    logger.info(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"🔗 Access at: http://localhost:5000")
    logger.info(f"📁 Template folder: {app.template_folder}")
    logger.info(f"📁 Static folder: {app.static_folder}")
    logger.info("=" * 100)
    
    # Create necessary directories
    Path('logs').mkdir(exist_ok=True)
    Path('output/recorded_data').mkdir(parents=True, exist_ok=True)
    Path('output/maps').mkdir(parents=True, exist_ok=True)
    
    # Run Flask app
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=True,
            use_debugger=True,
            threaded=True
        )
    except Exception as e:
        logger.critical(f"Failed to start Flask app: {str(e)}", exc_info=True)
        sys.exit(1)