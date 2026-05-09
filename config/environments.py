"""
Environment-specific Configuration
Different configs for dev, staging, production
"""

from typing import Dict, Any
from enum import Enum


class Environment(str, Enum):
    """Supported environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


# ==================== DEVELOPMENT ENVIRONMENT ====================

DEVELOPMENT_CONFIG: Dict[str, Any] = {
    "application": {
        "environment": "development",
        "debug": True,
    },
    "api": {
        "debug": True,
        "workers": 1,
    },
    "logging": {
        "level": "DEBUG",
        "console": True,
    },
    "security": {
        "secret_key": "dev-secret-key-change-in-production",
        "enable_cors": True,
    },
}


# ==================== STAGING ENVIRONMENT ====================

STAGING_CONFIG: Dict[str, Any] = {
    "application": {
        "environment": "staging",
        "debug": False,
    },
    "api": {
        "debug": False,
        "workers": 2,
    },
    "logging": {
        "level": "INFO",
        "console": True,
    },
    "security": {
        "enable_cors": True,
    },
}


# ==================== PRODUCTION ENVIRONMENT ====================

PRODUCTION_CONFIG: Dict[str, Any] = {
    "application": {
        "environment": "production",
        "debug": False,
    },
    "api": {
        "debug": False,
        "workers": 4,
    },
    "logging": {
        "level": "WARNING",
        "console": False,
    },
    "security": {
        "enable_cors": False,
        "session_timeout": 1800,  # 30 minutes
    },
}


# ==================== TESTING ENVIRONMENT ====================

TESTING_CONFIG: Dict[str, Any] = {
    "application": {
        "environment": "testing",
        "debug": True,
    },
    "api": {
        "debug": True,
        "workers": 1,
    },
    "database": {
        "type": "sqlite",
        "path": ":memory:",
    },
    "logging": {
        "level": "DEBUG",
        "console": False,
    },
}


# ==================== ENVIRONMENT MAPPING ====================

ENVIRONMENT_CONFIGS = {
    Environment.DEVELOPMENT: DEVELOPMENT_CONFIG,
    Environment.STAGING: STAGING_CONFIG,
    Environment.PRODUCTION: PRODUCTION_CONFIG,
    Environment.TESTING: TESTING_CONFIG,
}


def get_environment_config(environment: str = None) -> Dict[str, Any]:
    """
    Get configuration for specific environment
    
    Args:
        environment: Environment name (dev, staging, prod, test)
                    If None, reads from TDOA_ENVIRONMENT env var
    
    Returns:
        Environment-specific configuration
    """
    import os
    
    if environment is None:
        environment = os.environ.get("TDOA_ENVIRONMENT", "development")
    
    environment = environment.lower()
    
    # Map shortcuts to full names
    env_map = {
        "dev": "development",
        "stage": "staging",
        "prod": "production",
        "test": "testing",
    }
    
    environment = env_map.get(environment, environment)
    
    # Get enum value
    try:
        env = Environment(environment)
        return ENVIRONMENT_CONFIGS.get(env, DEVELOPMENT_CONFIG)
    except ValueError:
        return DEVELOPMENT_CONFIG


def get_current_environment() -> Environment:
    """
    Get current environment
    
    Returns:
        Current Environment enum
    """
    import os
    env_str = os.environ.get("TDOA_ENVIRONMENT", "development").lower()
    
    env_map = {
        "dev": Environment.DEVELOPMENT,
        "stage": Environment.STAGING,
        "prod": Environment.PRODUCTION,
        "test": Environment.TESTING,
    }
    
    return env_map.get(env_str, Environment(env_str if env_str in [e.value for e in Environment] else Environment.DEVELOPMENT))


def is_production() -> bool:
    """Check if running in production"""
    return get_current_environment() == Environment.PRODUCTION


def is_development() -> bool:
    """Check if running in development"""
    return get_current_environment() == Environment.DEVELOPMENT


def is_testing() -> bool:
    """Check if running in testing"""
    return get_current_environment() == Environment.TESTING
