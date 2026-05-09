"""
Configuration Validators
Additional validation functions for config values
"""

from typing import Any, Callable, List, Tuple


class ConfigValidator:
    """Configuration value validator"""
    
    @staticmethod
    def validate_coordinate(value: Any, coord_type: str = 'latitude') -> Tuple[bool, str]:
        """
        Validate latitude or longitude
        
        Args:
            value: Coordinate value
            coord_type: 'latitude' or 'longitude'
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(value, (int, float)):
            return False, f"{coord_type} must be numeric"
        
        if coord_type == 'latitude':
            if not (-90 <= value <= 90):
                return False, "Latitude must be between -90 and 90"
        elif coord_type == 'longitude':
            if not (-180 <= value <= 180):
                return False, "Longitude must be between -180 and 180"
        
        return True, ""
    
    @staticmethod
    def validate_bandwidth(value: Any) -> Tuple[bool, str]:
        """Validate bandwidth value"""
        if not isinstance(value, (int, float)):
            return False, "Bandwidth must be numeric (kHz)"
        
        valid_bandwidths = [10, 20, 40, 80, 160, 320]
        
        if value not in valid_bandwidths:
            return False, f"Bandwidth must be one of: {valid_bandwidths}"
        
        return True, ""
    
    @staticmethod
    def validate_threshold(value: Any) -> Tuple[bool, str]:
        """Validate threshold value (0-1)"""
        if not isinstance(value, (int, float)):
            return False, "Threshold must be numeric"
        
        if not (0.0 <= value <= 1.0):
            return False, "Threshold must be between 0.0 and 1.0"
        
        return True, ""
    
    @staticmethod
    def validate_port(value: Any) -> Tuple[bool, str]:
        """Validate port number"""
        if not isinstance(value, int):
            return False, "Port must be integer"
        
        if not (1 <= value <= 65535):
            return False, "Port must be between 1 and 65535"
        
        return True, ""
    
    @staticmethod
    def validate_directory_path(value: Any) -> Tuple[bool, str]:
        """Validate directory path"""
        if not isinstance(value, str):
            return False, "Path must be string"
        
        if not value:
            return False, "Path cannot be empty"
        
        return True, ""
    
    @staticmethod
    def validate_log_level(value: Any) -> Tuple[bool, str]:
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        if not isinstance(value, str):
            return False, "Log level must be string"
        
        if value.upper() not in valid_levels:
            return False, f"Log level must be one of: {valid_levels}"
        
        return True, ""


def validate_config_section(section: dict, validators: dict) -> Tuple[bool, List[str]]:
    """
    Validate a config section
    
    Args:
        section: Configuration section dict
        validators: Dict of {key: validator_func}
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    for key, validator_func in validators.items():
        if key not in section:
            continue
        
        value = section[key]
        is_valid, error_msg = validator_func(value)
        
        if not is_valid:
            errors.append(f"{key}: {error_msg}")
    
    return len(errors) == 0, errors
