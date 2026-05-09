"""
Default Configuration Values
Used when config.json is not fully populated
"""

from typing import Dict, Any


# ==================== APPLICATION DEFAULTS ====================

DEFAULT_CONFIG: Dict[str, Any] = {
    "version": "1.0.0",
    
    "application": {
        "name": "TDOA Automation System",
        "description": "Time Difference of Arrival based RF source localization",
        "version": "1.0.0",
        "environment": "development",
        "debug": False,
    },
    
    # ==================== NETWORK ====================
    "network": {
        "receivers": [
            {
                "id": 1,
                "name": "RX1",
                "host": "192.168.1.101",
                "port": 22,
                "username": "pi",
                "latitude": -7.2884674,
                "longitude": 112.6983234,
                "altitude_m": 50,
            },
            {
                "id": 2,
                "name": "RX2",
                "host": "192.168.1.102",
                "port": 22,
                "username": "pi",
                "latitude": -7.2886674,
                "longitude": 112.7003234,
                "altitude_m": 50,
            },
            {
                "id": 3,
                "name": "RX3",
                "host": "192.168.1.103",
                "port": 22,
                "username": "pi",
                "latitude": -7.2895674,
                "longitude": 112.6993234,
                "altitude_m": 50,
            },
        ]
    },
    
    # ==================== RECEIVERS ====================
    "receivers": {
        "rx1": {
            "name": "RX1",
            "latitude": -7.2884674,
            "longitude": 112.6983234,
            "altitude_m": 50,
            "ssh_host": "192.168.1.101",
            "ssh_port": 22,
            "ssh_user": "pi",
            "remote_data_dir": "/home/pi/recorded_data",
        },
        "rx2": {
            "name": "RX2",
            "latitude": -7.2886674,
            "longitude": 112.7003234,
            "altitude_m": 50,
            "ssh_host": "192.168.1.102",
            "ssh_port": 22,
            "ssh_user": "pi",
            "remote_data_dir": "/home/pi/recorded_data",
        },
        "rx3": {
            "name": "RX3",
            "latitude": -7.2895674,
            "longitude": 112.6993234,
            "altitude_m": 50,
            "ssh_host": "192.168.1.103",
            "ssh_port": 22,
            "ssh_user": "pi",
            "remote_data_dir": "/home/pi/recorded_data",
        },
    },
    
    # ==================== TRANSMITTER ====================
    "transmitter": {
        "reference": {
            "name": "Reference TX",
            "latitude": -7.2885674,
            "longitude": 112.6993234,
            "altitude_m": 50,
            "frequency_mhz": 915,
        }
    },
    
    # ==================== CENTER POINT ====================
    "center_point": {
        "latitude": -7.2885674,
        "longitude": 112.6993234,
        "altitude_m": 50,
    },
    
    # ==================== SIGNAL PROCESSING ====================
    "signal_processing": {
        "sample_rate": 2048000,
        "bandwidth_khz": 40,
        "correlation_type": "dphase",
        "smoothing_factor": 0,
        "interpolation_factor": 0,
        "peak_detection": {
            "prominence": 0.1,
            "distance": 10,
        },
    },
    
    # ==================== VISUALIZATION ====================
    "visualization": {
        "heatmap_resolution": 200,
        "heatmap_threshold": 0.70,
        "heatmap_colormap": "viridis",
        "map_zoom_level": 13,
        "map_tile_provider": "openstreetmap",
        "confidence_levels": [0.50, 0.60, 0.70, 0.80, 0.90],
    },
    
    # ==================== OUTPUT ====================
    "output": {
        "base_dir": "./output",
        "data_dir": "./output/recorded_data",
        "map_dir": "./output/maps",
        "results_dir": "./output/results",
        "log_dir": "./logs",
    },
    
    # ==================== LOGGING ====================
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file": "./logs/app.log",
        "max_bytes": 10485760,  # 10MB
        "backup_count": 5,
        "console": True,
    },
    
    # ==================== DATABASE ====================
    "database": {
        "type": "sqlite",
        "path": "./tdoa.db",
        # Uncomment untuk PostgreSQL:
        # "type": "postgresql",
        # "host": "localhost",
        # "port": 5432,
        # "user": "tdoa_user",
        # "password": "tdoa_pass",
        # "database": "tdoa_db",
    },
    
    # ==================== CACHE ====================
    "cache": {
        "type": "memory",
        "ttl": 3600,
        # Uncomment untuk Redis:
        # "type": "redis",
        # "host": "localhost",
        # "port": 6379,
        # "db": 0,
    },
    
    # ==================== API ====================
    "api": {
        "host": "0.0.0.0",
        "port": 5000,
        "debug": False,
        "workers": 4,
        "timeout": 300,
    },
    
    # ==================== SECURITY ====================
    "security": {
        "secret_key": "change-me-in-production",
        "session_timeout": 3600,
        "enable_cors": True,
        "cors_origins": ["*"],
    },
    
    # ==================== FEATURES ====================
    "features": {
        "enable_batch_processing": True,
        "enable_realtime_monitoring": True,
        "enable_export": True,
        "enable_api": True,
    },
}