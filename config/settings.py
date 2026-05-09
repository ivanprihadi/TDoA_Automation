"""
Main Settings Class
Central point for accessing all configuration
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import os
from loguru import logger

from config.loader import ConfigLoader
from config.environments import get_environment_config, get_current_environment


class Settings:
    """
    Main settings class for TDOA application
    Provides easy access to all configuration
    """
    
    def __init__(self, config_file: str = "config.json"):
        """Initialize settings"""
        self.config_file = config_file
        self.loader = ConfigLoader(config_file)
        self.config = self.loader.config
        
        # Create output directories
        self.loader.create_output_directories()
    
    # ==================== APPLICATION SETTINGS ====================
    
    @property
    def app_name(self) -> str:
        """Application name"""
        return self.config.get('application', {}).get('name', 'TDOA System')
    
    @property
    def app_version(self) -> str:
        """Application version"""
        return self.config.get('application', {}).get('version', '1.0.0')
    
    @property
    def environment(self) -> str:
        """Current environment (dev, staging, prod, test)"""
        return str(get_current_environment().value)
    
    @property
    def debug(self) -> bool:
        """Debug mode enabled"""
        return self.config.get('application', {}).get('debug', False)
    
    # ==================== API SETTINGS ====================
    
    @property
    def api_host(self) -> str:
        """API host"""
        return self.config.get('api', {}).get('host', '0.0.0.0')
    
    @property
    def api_port(self) -> int:
        """API port"""
        return self.config.get('api', {}).get('port', 5000)
    
    @property
    def api_workers(self) -> int:
        """Number of API workers"""
        return self.config.get('api', {}).get('workers', 4)
    
    @property
    def api_timeout(self) -> int:
        """API timeout in seconds"""
        return self.config.get('api', {}).get('timeout', 300)
    
    # ==================== RECEIVER SETTINGS ====================
    
    @property
    def receivers(self) -> List[Dict[str, Any]]:
        """Get all receivers"""
        return self.loader.get_receivers()
    
    @property
    def num_receivers(self) -> int:
        """Number of receivers"""
        return len(self.receivers)
    
    def get_receiver(self, receiver_id: int) -> Optional[Dict]:
        """Get specific receiver by ID"""
        return self.loader.get_receiver(receiver_id)
    
    # ==================== SIGNAL PROCESSING SETTINGS ====================
    
    @property
    def sample_rate(self) -> int:
        """Sample rate in Hz"""
        return self.config.get('signal_processing', {}).get('sample_rate', 2048000)
    
    @property
    def bandwidth_khz(self) -> int:
        """Bandwidth in kHz"""
        return self.config.get('signal_processing', {}).get('bandwidth_khz', 40)
    
    @property
    def correlation_type(self) -> str:
        """Correlation type (dphase, complex, magnitude)"""
        return self.config.get('signal_processing', {}).get('correlation_type', 'dphase')
    
    @property
    def smoothing_factor(self) -> int:
        """Smoothing factor (0-100)"""
        return self.config.get('signal_processing', {}).get('smoothing_factor', 0)
    
    @property
    def interpolation_factor(self) -> int:
        """Interpolation factor"""
        return self.config.get('signal_processing', {}).get('interpolation_factor', 0)
    
    # ==================== VISUALIZATION SETTINGS ====================
    
    @property
    def heatmap_resolution(self) -> int:
        """Heatmap resolution (pixels)"""
        return self.config.get('visualization', {}).get('heatmap_resolution', 200)
    
    @property
    def heatmap_threshold(self) -> float:
        """Heatmap threshold (0-1)"""
        return self.config.get('visualization', {}).get('heatmap_threshold', 0.70)
    
    @property
    def map_zoom_level(self) -> int:
        """Map zoom level"""
        return self.config.get('visualization', {}).get('map_zoom_level', 13)
    
    @property
    def map_tile_provider(self) -> str:
        """Map tile provider"""
        return self.config.get('visualization', {}).get('map_tile_provider', 'openstreetmap')
    
    # ==================== OUTPUT DIRECTORIES ====================
    
    @property
    def base_dir(self) -> str:
        """Base output directory"""
        return self.loader.get_output_dir('base')
    
    @property
    def data_dir(self) -> str:
        """Data files directory"""
        return self.loader.get_output_dir('data')
    
    @property
    def maps_dir(self) -> str:
        """Generated maps directory"""
        return self.loader.get_output_dir('maps')
    
    @property
    def results_dir(self) -> str:
        """Results directory"""
        return self.loader.get_output_dir('results')
    
    @property
    def logs_dir(self) -> str:
        """Logs directory"""
        return self.loader.get_output_dir('logs')
    
    # ==================== LOGGING SETTINGS ====================
    
    @property
    def log_level(self) -> str:
        """Log level"""
        return self.config.get('logging', {}).get('level', 'INFO')
    
    @property
    def log_file(self) -> str:
        """Log file path"""
        return self.config.get('logging', {}).get('file', './logs/app.log')
    
    @property
    def log_to_console(self) -> bool:
        """Log to console"""
        return self.config.get('logging', {}).get('console', True)
    
    # ==================== SECURITY SETTINGS ====================
    
    @property
    def secret_key(self) -> str:
        """Secret key for sessions"""
        return self.config.get('security', {}).get('secret_key', 'change-me-in-production')
    
    @property
    def session_timeout(self) -> int:
        """Session timeout in seconds"""
        return self.config.get('security', {}).get('session_timeout', 3600)
    
    @property
    def enable_cors(self) -> bool:
        """CORS enabled"""
        return self.config.get('security', {}).get('enable_cors', True)
    
    @property
    def cors_origins(self) -> List[str]:
        """CORS origins"""
        return self.config.get('security', {}).get('cors_origins', ['*'])
    
    # ==================== UTILITY METHODS ====================
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value using dot notation"""
        return self.loader.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Get entire config as dict"""
        return self.config
    
    def to_json(self) -> str:
        """Get config as JSON"""
        return self.loader.to_json()
    
    def reload(self) -> None:
        """Reload configuration from file"""
        logger.info("Reloading configuration...")
        self.config = self.loader.load_config()
        logger.info("✓ Configuration reloaded")
