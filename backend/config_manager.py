"""Configuration Manager for TDOA System"""

import json
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Optional, List
from loguru import logger  # ✅ ADD THIS


@dataclass
class ReceiverConfig:
    """Configuration untuk satu receiver"""
    name: str
    hostname: str
    port: int
    username: str
    password: str
    latitude: float
    longitude: float
    altitude: float
    sdr_device_id: int = 0

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'hostname': self.hostname,
            'port': self.port,
            'username': self.username,
            'password': self.password,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'altitude': self.altitude,
            'sdr_device_id': self.sdr_device_id
        }


class ConfigManager:
    """Manage application configuration"""
    
    def __init__(self, config_path: str = 'config.json'):
        """
        Initialize ConfigManager
        
        Args:
            config_path (str): Path to config.json file
        """
        self.config_path = Path(config_path) if config_path else None  # ✅ FIXED: Accept string
        self.config = self._load_config()
        logger.info(f"ConfigManager initialized with {config_path}")
    
    def _load_config(self) -> Dict:
        """Load configuration from JSON file"""
        try:
            if self.config_path and self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"Config loaded from {self.config_path}")
                return config
            else:
                logger.warning(f"Config file not found: {self.config_path}")
                return self._default_config()
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            return self._default_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self._default_config()
    
    def _default_config(self) -> Dict:
        """Return default configuration"""
        return {
            "app": {
                "name": "TDOA Automation System",
                "version": "1.0.0",
                "debug": True,
                "port": 5000,
                "host": "0.0.0.0"
            },
            "network": {
                "receivers": []
            },
            "signal_processing": {
                "bandwidth_khz": 40,
                "ref_bandwidth_khz": 40,
                "correlation_type": "dphase",
                "smoothing_factor": 0,
                "smoothing_factor_ref": 0
            },
            "visualization": {
                "heatmap_resolution": 100,
                "heatmap_threshold": 0.7
            },
            "output": {
                "format": "json",
                "directory": "./output"
            }
        }
    
    def get(self, key: str, default=None):
        """Get config value by key"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default
    
    def get_receivers(self) -> List[Dict]:
        """Get receivers configuration"""
        return self.config.get('network', {}).get('receivers', [])
    
    def get_tdoa_config(self) -> Dict:
        """Get TDOA configuration"""
        return self.config.get('signal_processing', {})
    
    def get_visualization_config(self) -> Dict:
        """Get visualization configuration"""
        return self.config.get('visualization', {})
    
    def save(self, config: Optional[Dict] = None) -> bool:
        """Save config to file"""
        try:
            if config:
                self.config = config
            
            if not self.config_path:
                self.config_path = Path('config.json')
            
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info(f"Config saved to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False