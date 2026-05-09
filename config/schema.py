"""
Configuration Schema Validation
Validates configuration structure and types
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


# ==================== DATACLASSES ====================

@dataclass
class Receiver:
    """Receiver configuration"""
    id: int
    name: str
    host: str
    port: int = 22
    username: str = "pi"
    latitude: float = None
    longitude: float = None
    altitude_m: float = 0
    
    def validate(self) -> bool:
        """Validate receiver config"""
        if not self.name or not self.host:
            return False
        if self.latitude is None or self.longitude is None:
            return False
        if not (-90 <= self.latitude <= 90):
            return False
        if not (-180 <= self.longitude <= 180):
            return False
        return True


@dataclass
class SignalProcessing:
    """Signal processing configuration"""
    sample_rate: int = 2048000
    bandwidth_khz: int = 40
    correlation_type: str = "dphase"
    smoothing_factor: int = 0
    interpolation_factor: int = 0
    
    def validate(self) -> bool:
        """Validate signal processing config"""
        if self.sample_rate <= 0:
            return False
        if self.bandwidth_khz <= 0:
            return False
        if self.correlation_type not in ["dphase", "complex", "magnitude"]:
            return False
        if not (0 <= self.smoothing_factor <= 100):
            return False
        return True


@dataclass
class Visualization:
    """Visualization configuration"""
    heatmap_resolution: int = 200
    heatmap_threshold: float = 0.70
    map_zoom_level: int = 13
    map_tile_provider: str = "openstreetmap"
    
    def validate(self) -> bool:
        """Validate visualization config"""
        if not (50 <= self.heatmap_resolution <= 1000):
            return False
        if not (0.0 <= self.heatmap_threshold <= 1.0):
            return False
        if not (1 <= self.map_zoom_level <= 20):
            return False
        return True


@dataclass
class Output:
    """Output configuration"""
    base_dir: str = "./output"
    data_dir: str = "./output/recorded_data"
    map_dir: str = "./output/maps"
    results_dir: str = "./output/results"
    log_dir: str = "./logs"


@dataclass
class Logging:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str = "./logs/app.log"
    console: bool = True
    
    def validate(self) -> bool:
        """Validate logging config"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.level not in valid_levels:
            return False
        return True


# ==================== VALIDATION FUNCTIONS ====================

def validate_receiver(data: Dict[str, Any]) -> bool:
    """Validate receiver configuration"""
    required_fields = ["name", "host", "latitude", "longitude"]
    
    for field in required_fields:
        if field not in data:
            return False
    
    # Validate coordinates
    lat = data.get("latitude")
    lon = data.get("longitude")
    
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return False
    
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        return False
    
    return True


def validate_receivers_list(receivers: List[Dict[str, Any]]) -> bool:
    """Validate list of receivers"""
    if not isinstance(receivers, list):
        return False
    
    if len(receivers) < 3:
        return False
    
    for receiver in receivers:
        if not validate_receiver(receiver):
            return False
    
    return True


def validate_signal_processing(data: Dict[str, Any]) -> bool:
    """Validate signal processing configuration"""
    if "sample_rate" in data and data["sample_rate"] <= 0:
        return False
    
    if "bandwidth_khz" in data and data["bandwidth_khz"] <= 0:
        return False
    
    if "correlation_type" in data:
        valid_types = ["dphase", "complex", "magnitude"]
        if data["correlation_type"] not in valid_types:
            return False
    
    return True


def validate_visualization(data: Dict[str, Any]) -> bool:
    """Validate visualization configuration"""
    if "heatmap_threshold" in data:
        threshold = data["heatmap_threshold"]
        if not (0.0 <= threshold <= 1.0):
            return False
    
    if "map_zoom_level" in data:
        zoom = data["map_zoom_level"]
        if not (1 <= zoom <= 20):
            return False
    
    return True


def validate_config(config: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate entire configuration
    
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Check required top-level keys
    required_keys = ["application", "receivers", "signal_processing"]
    for key in required_keys:
        if key not in config:
            errors.append(f"Missing required configuration: {key}")
    
    # Validate receivers
    if "network" in config and "receivers" in config["network"]:
        if not validate_receivers_list(config["network"]["receivers"]):
            errors.append("Invalid receivers configuration")
    
    # Validate signal processing
    if "signal_processing" in config:
        if not validate_signal_processing(config["signal_processing"]):
            errors.append("Invalid signal processing configuration")
    
    # Validate visualization
    if "visualization" in config:
        if not validate_visualization(config["visualization"]):
            errors.append("Invalid visualization configuration")
    
    return len(errors) == 0, errors