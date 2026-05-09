"""
TDOA Automation System - Complete Version
"""

from pathlib import Path
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from loguru import logger
import json

# Configure logging
logger.remove()
logger.add("logs/tdoa_system.log", rotation="500 MB", level="INFO")

# Initialize Flask app
app = Flask(__name__, template_folder='frontend/templates', static_folder='frontend/static')
CORS(app)

# Global config
CONFIG = {}

def load_config():
    """Load configuration from config.json"""
    global CONFIG
    try:
        if Path("config.json").exists():
            with open("config.json", "r") as f:
                CONFIG = json.load(f)
        else:
            CONFIG = {
                "app": {"version": "1.0.0", "debug": True},
                "network": {
                    "receivers": [
                        {
                            "name": "RX-1",
                            "hostname": "192.168.1.10",
                            "port": 5005,
                            "latitude": -6.2088,
                            "longitude": 106.8456,
                            "altitude": 50
                        },
                        {
                            "name": "RX-2",
                            "hostname": "192.168.1.11",
                            "port": 5005,
                            "latitude": -6.2100,
                            "longitude": 106.8470,
                            "altitude": 60
                        },
                        {
                            "name": "RX-3",
                            "hostname": "192.168.1.12",
                            "port": 5005,
                            "latitude": -6.2050,
                            "longitude": 106.8440,
                            "altitude": 55
                        }
                    ]
                }
            }
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        CONFIG = {}


# ===== ROUTES =====

@app.route('/')
def index():
    """Main dashboard"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering index: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/status')
def get_status():
    """Get system status"""
    try:
        receivers = CONFIG.get('network', {}).get('receivers', [])
        status = {
            'system': 'running ✓',
            'config_loaded': True,
            'receivers_count': len(receivers),
            'version': CONFIG.get('app', {}).get('version', '1.0.0'),
            'environment': 'development'
        }
        logger.info("Status requested")
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/config')
def get_config():
    """Get full configuration"""
    try:
        return jsonify(CONFIG)
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/receivers')
def get_receivers():
    """Get receivers list"""
    try:
        receivers = CONFIG.get('network', {}).get('receivers', [])
        logger.info(f"Receivers requested - {len(receivers)} found")
        return jsonify(receivers)
    except Exception as e:
        logger.error(f"Error getting receivers: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/files')
def get_files():
    """Get recorded IQ files"""
    try:
        output_dir = Path('output/recorded_data')
        files = []
        
        if output_dir.exists():
            for file in output_dir.glob('*.bin'):
                files.append({
                    'name': file.name,
                    'path': str(file),
                    'size': file.stat().st_size
                })
        
        logger.info(f"Files requested - {len(files)} found")
        return jsonify(files)
    except Exception as e:
        logger.error(f"Error getting files: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/results')
def get_results():
    """Get TDOA calculation results"""
    try:
        output_dir = Path('output/results')
        results = []
        
        if output_dir.exists():
            for file in output_dir.glob('*.json'):
                try:
                    with open(file, 'r') as f:
                        result = json.load(f)
                        results.append(result)
                except Exception as e:
                    logger.error(f"Error reading result {file}: {e}")
        
        logger.info(f"Results requested - {len(results)} found")
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error getting results: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/maps')
def get_maps():
    """Get generated maps"""
    try:
        map_dir = Path('output/maps')
        maps = []
        
        if map_dir.exists():
            for file in map_dir.glob('*.html'):
                maps.append({
                    'name': file.name,
                    'path': f'/output/maps/{file.name}'
                })
        
        logger.info(f"Maps requested - {len(maps)} found")
        return jsonify(maps)
    except Exception as e:
        logger.error(f"Error getting maps: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/tdoa/calculate', methods=['POST'])
def calculate_tdoa():
    """Calculate TDOA from IQ files"""
    try:
        data = request.json
        
        logger.info(f"TDOA calculation requested with files: {data}")
        
        # Dummy result
        result = {
            'success': True,
            'tx_location': {
                'latitude': -6.2070,
                'longitude': 106.8455,
                'accuracy': 50
            },
            'tdoa_results': {
                'tdoa_12': 0.000245,
                'tdoa_13': 0.000378,
                'reliability': 0.95
            }
        }
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error calculating TDOA: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})


@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 Not found: {request.path}")
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def server_error(error):
    logger.error(f"Server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    try:
        print("\n🛰️  TDOA Automation System Starting...")
        print("=" * 60)
        
        # Create required directories
        Path('logs').mkdir(exist_ok=True)
        Path('output').mkdir(exist_ok=True)
        Path('output/recorded_data').mkdir(exist_ok=True)
        Path('output/maps').mkdir(exist_ok=True)
        Path('output/results').mkdir(exist_ok=True)
        
        # Load configuration
        load_config()
        
        receivers = CONFIG.get('network', {}).get('receivers', [])
        env = "development" if CONFIG.get('app', {}).get('debug') else "production"
        
        print(f"Environment: {env}")
        print(f"Receivers: {len(receivers)}")
        print("=" * 60)
        print("Running on http://localhost:5000")
        print("=" * 60 + "\n")
        
        # Run Flask app
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True
        )
    except Exception as e:
        print(f"✗ Error: {e}")
        logger.error(f"Failed to start: {e}")
        raise
