"""
Configuration Loader
Loads and manages configuration from files and environment variables
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
from loguru import logger

from config.defaults import DEFAULT_CONFIG
from config.schema import validate_config


class ConfigLoader:
    """Load and manage application configuration"""
    
    def __init__(self, config_file: str = "config.json"):
        """
        Initialize config loader
        
        Args:
            config_file: Path to config JSON file
        """
        self.config_file = config_file
        self.config = None
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file and environment
        
        Priority:
        1. config.json file
        2. Environment variables
        3. Default values
        
        Returns:
            Configuration dictionary
        """
        logger.info(f"Loading configuration from {self.config_file}")
        
        # Start with defaults
        config = DEFAULT_CONFIG.copy()
        
        # Override with file if exists
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                    config = self._deep_merge(config, file_config)
                    logger.info(f"✓ Configuration loaded from {self.config_file}")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in config file: {e}")
                raise
            except Exception as e:
                logger.error(f"Error loading config file: {e}")
                raise
        else:
            logger.warning(f"Config file not found: {self.config_file}")
            logger.info("Using default configuration")
        
        # Override with environment variables
        config = self._override_from_env(config)
        
        # Validate configuration
        is_valid, errors = validate_config(config)
        if not is_valid:
            for error in errors:
                logger.error(f"Configuration error: {error}")
            raise ValueError("Invalid configuration")
        
        logger.info("✓ Configuration validated successfully")
        
        self.config = config
        return config
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """
        Deep merge override dict into base dict
        
        Args:
            base: Base dictionary
            override: Override dictionary
            
        Returns:
            Merged dictionary
        """
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _override_from_env(self, config: Dict) -> Dict:
        """
        Override configuration from environment variables
        
        Environment variables format:
        TDOA_{SECTION}_{KEY}
        
        Example:
        TDOA_API_PORT=8000
        TDOA_LOGGING_LEVEL=DEBUG
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Updated configuration
        """
        for key, value in os.environ.items():
            if key.startswith("TDOA_"):
                # Parse key: TDOA_SECTION_SUBSECTION_KEY
                parts = key[5:].lower().split('_')
                
                # Navigate/create nested structure
                current = config
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                
                # Set value
                final_key = parts[-1]
                # Try to parse as number or boolean
                if value.lower() == 'true':
                    current[final_key] = True
                elif value.lower() == 'false':
                    current[final_key] = False
                elif value.isdigit():
                    current[final_key] = int(value)
                else:
                    try:
                        current[final_key] = float(value)
                    except ValueError:
                        current[final_key] = value
                
                logger.debug(f"Override from env: {key} = {value}")
        
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        
        Example:
        config.get('signal_processing.bandwidth_khz')
        
        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        if not self.config:
            self.load_config()
        
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        
        return value if value is not None else default
    
    def get_receivers(self) -> list:
        """Get list of receiver configurations"""
        return self.config.get('network', {}).get('receivers', [])
    
    def get_receiver(self, receiver_id: int) -> Optional[Dict]:
        """Get specific receiver configuration"""
        receivers = self.get_receivers()
        for rx in receivers:
            if rx.get('id') == receiver_id:
                return rx
        return None
    
    def get_output_dir(self, dir_type: str = 'base') -> str:
        """
        Get output directory path
        
        Args:
            dir_type: 'base', 'data', 'maps', 'results', 'logs'
            
        Returns:
            Directory path
        """
        output_config = self.config.get('output', {})
        
        dir_map = {
            'base': 'base_dir',
            'data': 'data_dir',
            'maps': 'map_dir',
            'results': 'results_dir',
            'logs': 'log_dir',
        }
        
        key = dir_map.get(dir_type, 'base_dir')
        dir_path = output_config.get(key, './output')
        
        # Create directory if doesn't exist
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        return dir_path
    
    def create_output_directories(self) -> bool:
        """
        Create all output directories
        
        Returns:
            True if successful
        """
        try:
            for dir_type in ['base', 'data', 'maps', 'results', 'logs']:
                self.get_output_dir(dir_type)
            logger.info("✓ Output directories created")
            return True
        except Exception as e:
            logger.error(f"Failed to create output directories: {e}")
            return False
    
    def to_dict(self) -> Dict:
        """Get entire configuration as dictionary"""
        return self.config.copy()
    
    def to_json(self, indent: int = 2) -> str:
        """Get configuration as JSON string"""
        return json.dumps(self.config, indent=indent)


# Singleton instance
_loader: Optional[ConfigLoader] = None


def get_config_loader(config_file: str = "config.json") -> ConfigLoader:
    """
    Get or create singleton config loader
    
    Args:
        config_file: Path to config file
        
    Returns:
        ConfigLoader instance
    """
    global _loader
    
    if _loader is None:
        _loader = ConfigLoader(config_file)
    
    return _loader


def get_config() -> Dict[str, Any]:
    """Get entire configuration"""
    return get_config_loader().to_dict()
