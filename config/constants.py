"""
Application Constants
Define all fixed constants used throughout the application
"""

from enum import Enum
from typing import Dict, List


class CorrelationType(str, Enum):
    """Signal correlation types"""
    DPHASE = "dphase"
    COMPLEX = "complex"
    MAGNITUDE = "magnitude"


class ProcessingStatus(str, Enum):
    """Processing job status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReceiverStatus(str, Enum):
    """Receiver connection status"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    ERROR = "error"


class MapTileProvider(str, Enum):
    """Available map tile providers"""
    OPENSTREETMAP = "openstreetmap"
    CARTODB = "cartodb"
    STAMEN = "stamen"
    USGS = "usgs"


class LogLevel(str, Enum):
    """Logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# ==================== APPLICATION CONSTANTS ====================

class ApplicationConstants:
    """Application-wide constants"""
    
    # Version
    VERSION = "1.0.0"
    APP_NAME = "TDOA Localization System"
    DESCRIPTION = "Time Difference of Arrival based RF source localization"
    
    # HTTP
    DEFAULT_HOST = "0.0.0.0"
    DEFAULT_PORT = 5000
    
    # Timeouts
    SSH_TIMEOUT = 30
    API_TIMEOUT = 300
    CONNECTION_TIMEOUT = 10
    
    # File handling
    ALLOWED_FILE_EXTENSIONS = {'.dat', '.bin', '.raw', '.iq'}
    MAX_FILE_SIZE = 5 * 1024 * 1024 * 1024  # 5GB
    UPLOAD_CHUNK_SIZE = 1024 * 1024  # 1MB chunks
    
    # Processing
    MIN_RECEIVERS = 3
    MAX_RECEIVERS = 10
    DEFAULT_BANDWIDTH_KHZ = 40
    DEFAULT_SAMPLE_RATE = 2048000  # 2.048 MSPS
    
    # Heatmap
    DEFAULT_HEATMAP_RESOLUTION = 200
    DEFAULT_HEATMAP_THRESHOLD = 0.70
    HEATMAP_COLORMAP = "viridis"
    
    # Map
    DEFAULT_MAP_ZOOM = 13
    DEFAULT_MAP_TILE_PROVIDER = MapTileProvider.OPENSTREETMAP
    
    # Processing parameters
    CORRELATION_TYPES = [ct.value for ct in CorrelationType]
    DEFAULT_CORRELATION_TYPE = CorrelationType.DPHASE.value
    
    # Timing
    PROCESSING_TIMEOUT = 300  # 5 minutes
    BATCH_PROCESSING_TIMEOUT = 3600  # 1 hour
    STATUS_CHECK_INTERVAL = 5  # seconds
    
    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # Cache
    CACHE_TTL = 3600  # 1 hour
    HEATMAP_CACHE_TTL = 86400  # 1 day


# ==================== SIGNAL PROCESSING CONSTANTS ====================

class SignalProcessingConstants:
    """Signal processing related constants"""
    
    # Sample rates (from RTL-SDR)
    RTLSDR_SAMPLE_RATE = 2048000  # 2.048 MHz
    
    # Bandwidth options (kHz)
    BANDWIDTH_OPTIONS = [10, 20, 40, 80, 160, 320]
    
    # Correlation peak detection
    PEAK_PROMINENCE_MIN = 0.1
    PEAK_DISTANCE_MIN = 10
    
    # Smoothing
    SMOOTHING_WINDOW_SIZE = 5
    SMOOTHING_METHODS = ["gaussian", "hamming", "blackman"]
    
    # Interpolation
    INTERPOLATION_FACTORS = [1, 2, 4, 8, 16]
    
    # Heatmap resolution
    MIN_HEATMAP_RESOLUTION = 50
    MAX_HEATMAP_RESOLUTION = 1000
    
    # Threshold
    MIN_THRESHOLD = 0.0
    MAX_THRESHOLD = 1.0
    DEFAULT_THRESHOLD = 0.70


# ==================== LOCATION CONSTANTS ====================

class LocationConstants:
    """Geographic and location related constants"""
    
    # Earth
    EARTH_RADIUS_M = 6371000  # meters
    EARTH_RADIUS_KM = 6371  # kilometers
    
    # Coordinate boundaries
    LAT_MIN = -90.0
    LAT_MAX = 90.0
    LON_MIN = -180.0
    LON_MAX = 180.0
    
    # Default center (Surabaya, Indonesia - example)
    DEFAULT_CENTER_LAT = -7.2884674
    DEFAULT_CENTER_LON = 112.6983234
    DEFAULT_CENTER_ALT = 50  # meters
    
    # Accuracy estimation
    MIN_ACCURACY_M = 10
    MAX_ACCURACY_M = 10000
    DEFAULT_ACCURACY_M = 100


# ==================== DATABASE CONSTANTS ====================

class DatabaseConstants:
    """Database related constants"""
    
    # Connection pool
    POOL_SIZE = 10
    MAX_OVERFLOW = 20
    POOL_TIMEOUT = 30
    POOL_RECYCLE = 3600
    
    # Query limits
    DEFAULT_QUERY_LIMIT = 100
    MAX_QUERY_LIMIT = 1000


# ==================== ERROR MESSAGES ====================

class ErrorMessages:
    """Standard error messages"""
    
    # File errors
    FILE_NOT_FOUND = "File not found: {filename}"
    INVALID_FILE_FORMAT = "Invalid file format. Expected: {expected}"
    FILE_TOO_LARGE = "File size exceeds maximum limit: {max_size}MB"
    
    # Processing errors
    PROCESSING_FAILED = "Processing failed: {reason}"
    INVALID_PARAMETERS = "Invalid processing parameters: {details}"
    
    # Connection errors
    CONNECTION_FAILED = "Failed to connect to {host}:{port}"
    SSH_AUTHENTICATION_FAILED = "SSH authentication failed"
    
    # Validation errors
    INVALID_COORDINATES = "Invalid coordinates: lat must be -90 to 90, lon must be -180 to 180"
    MISSING_REQUIRED_FIELD = "Missing required field: {field}"
    
    # API errors
    UNAUTHORIZED = "Unauthorized access"
    NOT_FOUND = "Resource not found"
    INTERNAL_ERROR = "Internal server error"


# ==================== SUCCESS MESSAGES ====================

class SuccessMessages:
    """Standard success messages"""
    
    PROCESSING_COMPLETED = "Processing completed successfully"
    FILE_UPLOADED = "File uploaded successfully: {filename}"
    CONFIGURATION_SAVED = "Configuration saved successfully"
    RESULTS_EXPORTED = "Results exported successfully: {filename}"


# ==================== EXPORT ====================

class Constants:
    """Main Constants class for easy access"""
    
    Application = ApplicationConstants
    SignalProcessing = SignalProcessingConstants
    Location = LocationConstants
    Database = DatabaseConstants
    Errors = ErrorMessages
    Success = SuccessMessages
    
    # Enums
    CorrelationType = CorrelationType
    ProcessingStatus = ProcessingStatus
    ReceiverStatus = ReceiverStatus
    MapTileProvider = MapTileProvider
    LogLevel = LogLevel
