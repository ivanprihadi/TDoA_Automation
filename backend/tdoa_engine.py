"""
TDOA Engine - Complete TDOA Processing
Master orchestrator untuk signal processing, TDOA calculation, hyperbola generation
Translate MATLAB: tdoa2.m + gen_hyperbola.m + create_heatmap.m + evaluation_main.m
"""

import numpy as np
from pathlib import Path
from loguru import logger
from typing import Dict, List, Tuple, Optional
import json
from dataclasses import dataclass

# Import submodules
from .signal_processor import SignalProcessor
from .geometry_engine import GeometryEngine


@dataclass
class TDOAResult:
    """TDOA calculation result"""
    doa_meters: float
    doa_samples: float
    reliability: float
    delay1: float
    delay2: float
    delay3: float
    details: Dict


class TDOAEngine:  
    """
    Complete TDOA Processing Engine
    Combines: signal reading -> filtering -> correlation -> TDOA calc -> hyperbola gen -> heatmap
    """
    
    # Default constants (dapat di-override via config)
    SAMPLE_RATE = 2.048e6  # 2.048 MHz
    SPEED_OF_LIGHT = 3e8   # m/s
    NUM_SAMPLES_PER_FREQ = int(1.2e6)
    NUM_SAMPLES_PER_SLICE = int(1.0e6)
    GUARD_INTERVAL = int(200e3)
    
    def __init__(self, config_dict: Dict = None):
        """
        Initialize TDOA Engine
        
        Parameters:
        -----------
        config_dict : Dict
            Configuration dictionary
        """
        
        self.config = config_dict or {}
        self._validate_config()  # ✅ NEW: Validate config
        
        self.signal_processor = SignalProcessor()
        
        # Extract configuration
        self.receivers = self.config.get('network', {}).get('receivers', [])
        self.signal_bandwidth_khz = self.config.get('signal_processing', {}).get('bandwidth_khz', 40)
        self.ref_bandwidth_khz = self.config.get('signal_processing', {}).get('ref_bandwidth_khz', 40)
        self.smoothing_factor = self.config.get('signal_processing', {}).get('smoothing_factor', 0)
        self.smoothing_factor_ref = self.config.get('signal_processing', {}).get('smoothing_factor_ref', 0)
        self.corr_type = self.config.get('signal_processing', {}).get('correlation_type', 'dphase')
        self.interpol_factor = self.config.get('signal_processing', {}).get('interpol_factor', 0)
        self.heatmap_resolution = self.config.get('visualization', {}).get('heatmap_resolution', 100)  # ✅ Reduced default
        self.heatmap_threshold = self.config.get('visualization', {}).get('heatmap_threshold', 0.7)
        
        logger.info("✓ TDOAEngine initialized")  # ✅ FIXED: class name
    
    def _validate_config(self):  # ✅ NEW: Validation method
        """Validate configuration"""
        
        if not self.config:
            logger.warning("Empty configuration, using defaults")
            self.config = self._get_default_config()
        
        # Check required keys
        if 'network' not in self.config:
            logger.warning("'network' key missing in config, using default")
            self.config['network'] = {'receivers': []}
        
        if 'signal_processing' not in self.config:
            logger.warning("'signal_processing' key missing, using defaults")
            self.config['signal_processing'] = {}
        
        if 'visualization' not in self.config:
            self.config['visualization'] = {}
    
    def _get_default_config(self) -> Dict:  # ✅ NEW: Default config method
        """Get default configuration"""
        return {
            "network": {"receivers": []},
            "signal_processing": {
                "bandwidth_khz": 40,
                "ref_bandwidth_khz": 40,
                "correlation_type": "dphase"
            },
            "visualization": {
                "heatmap_resolution": 100
            }
        }
    
    def load_configuration(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
            
            self._validate_config()  # ✅ NEW: Validate after loading
            logger.info(f"✓ Loaded configuration from {config_path}")
            return self.config
            
        except FileNotFoundError:
            logger.error(f"✗ Config file not found: {config_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"✗ Invalid JSON in config: {e}")
            raise
        except Exception as e:
            logger.error(f"✗ Failed to load config: {str(e)}")
            raise
    
    def prepare_receiver_geometry(self) -> Dict:
        """
        Calculate receiver positions dan distances
        Dari MATLAB: evaluation_main.m lines 53-80
        
        Returns:
            Dictionary dengan receiver geometry info
        """
        
        try:
            logger.info("Preparing receiver geometry...")
            
            # ✅ NEW: Better error handling
            if len(self.receivers) < 3:
                raise ValueError(f"Expected 3 receivers, got {len(self.receivers)}")
            
            try:
                rx1_lat = float(self.receivers[0].get('latitude', 0.0))
                rx1_lon = float(self.receivers[0].get('longitude', 0.0))
                rx2_lat = float(self.receivers[1].get('latitude', 0.0))
                rx2_lon = float(self.receivers[1].get('longitude', 0.0))
                rx3_lat = float(self.receivers[2].get('latitude', 0.0))
                rx3_lon = float(self.receivers[2].get('longitude', 0.0))
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid receiver coordinates: {e}")
                raise
            
            # Reference TX position - ✅ FIXED: Better config handling
            freq_config = self.config.get('frequencies', {})
            tx_ref = freq_config.get('reference_tx', {})
            
            # ✅ NEW: Default coordinates if not in config
            tx_ref_lat = float(tx_ref.get('latitude', -7.2885674))
            tx_ref_lon = float(tx_ref.get('longitude', 112.6993234))
            
            # Geodetic reference point (mean of receiver positions)
            geo_ref_lat = (rx1_lat + rx2_lat + rx3_lat) / 3
            geo_ref_lon = (rx1_lon + rx2_lon + rx3_lon) / 3
            
            logger.debug(f"  Geodetic reference: ({geo_ref_lat:.8f}, {geo_ref_lon:.8f})")
            
            # Calculate distance differences
            rx_dist_to_tx_ref_1 = GeometryEngine.dist_latlong(
                tx_ref_lat, tx_ref_lon, rx1_lat, rx1_lon, geo_ref_lat, geo_ref_lon
            )
            rx_dist_to_tx_ref_2 = GeometryEngine.dist_latlong(
                tx_ref_lat, tx_ref_lon, rx2_lat, rx2_lon, geo_ref_lat, geo_ref_lon
            )
            rx_dist_to_tx_ref_3 = GeometryEngine.dist_latlong(
                tx_ref_lat, tx_ref_lon, rx3_lat, rx3_lon, geo_ref_lat, geo_ref_lon
            )
            
            rx_distance_diff_12 = rx_dist_to_tx_ref_1 - rx_dist_to_tx_ref_2
            rx_distance_diff_13 = rx_dist_to_tx_ref_1 - rx_dist_to_tx_ref_3
            rx_distance_diff_23 = rx_dist_to_tx_ref_2 - rx_dist_to_tx_ref_3
            
            rx_distance_12 = GeometryEngine.dist_latlong(
                rx1_lat, rx1_lon, rx2_lat, rx2_lon, geo_ref_lat, geo_ref_lon
            )
            rx_distance_13 = GeometryEngine.dist_latlong(
                rx1_lat, rx1_lon, rx3_lat, rx3_lon, geo_ref_lat, geo_ref_lon
            )
            rx_distance_23 = GeometryEngine.dist_latlong(
                rx2_lat, rx2_lon, rx3_lat, rx3_lon, geo_ref_lat, geo_ref_lon
            )
            
            logger.info(f"✓ Geometry prepared:")
            logger.info(f"  RX1: ({rx1_lat:.8f}, {rx1_lon:.8f})")
            logger.info(f"  RX2: ({rx2_lat:.8f}, {rx2_lon:.8f})")
            logger.info(f"  RX3: ({rx3_lat:.8f}, {rx3_lon:.8f})")
            logger.info(f"  Ref TX: ({tx_ref_lat:.8f}, {tx_ref_lon:.8f})")
            logger.info(f"  RX distances: {rx_distance_12:.1f}m, {rx_distance_13:.1f}m, {rx_distance_23:.1f}m")
            
            geometry = {
                'rx1_lat': rx1_lat, 'rx1_lon': rx1_lon,
                'rx2_lat': rx2_lat, 'rx2_lon': rx2_lon,
                'rx3_lat': rx3_lat, 'rx3_lon': rx3_lon,
                'geo_ref_lat': geo_ref_lat, 'geo_ref_lon': geo_ref_lon,
                'tx_ref_lat': tx_ref_lat, 'tx_ref_lon': tx_ref_lon,
                'rx_distance_12': rx_distance_12,
                'rx_distance_13': rx_distance_13,
                'rx_distance_23': rx_distance_23,
                'rx_distance_diff_12': rx_distance_diff_12,
                'rx_distance_diff_13': rx_distance_diff_13,
                'rx_distance_diff_23': rx_distance_diff_23
            }
            
            return geometry
            
        except Exception as e:
            logger.error(f"✗ Failed to prepare geometry: {str(e)}")
            raise
    
    def calculate_tdoa_pair(self, signal1: np.ndarray, signal2: np.ndarray,
                           rx_distance_diff: float, rx_distance: float,
                           rx_pair_name: str = "RX1-RX2") -> TDOAResult:
        """
        Calculate TDOA untuk 1 pair dari 2 receivers
        Translate MATLAB: tdoa2.m function
        
        Parameters:
        -----------
        signal1, signal2 : ndarray
            3.6M sample complex IQ signals
        rx_distance_diff : float
            Distance difference to reference TX (meters)
        rx_distance : float
            Distance between RX1 dan RX2 (meters)
        rx_pair_name : str
            Name untuk logging
        
        Returns:
            TDOAResult object
        """
        
        try:
            logger.info(f"\n{'='*80}")
            logger.info(f"TDOA CALCULATION: {rx_pair_name}")
            logger.info(f"{'='*80}")
            
            # ✅ NEW: Better signal validation
            expected_length = int(3.6e6)
            if len(signal1) != expected_length or len(signal2) != expected_length:
                raise ValueError(
                    f"Signals must be {expected_length} samples, "
                    f"got {len(signal1)}, {len(signal2)}"
                )
            
            # ==================== SLICE SIGNALS ====================
            logger.info("Slicing signals into 3 parts...")
            
            signal11 = signal1[0:self.NUM_SAMPLES_PER_SLICE]
            signal12 = signal1[self.NUM_SAMPLES_PER_FREQ + self.GUARD_INTERVAL :
                              self.NUM_SAMPLES_PER_FREQ + self.GUARD_INTERVAL + self.NUM_SAMPLES_PER_SLICE]
            signal13 = signal1[2*self.NUM_SAMPLES_PER_FREQ + self.GUARD_INTERVAL :
                              2*self.NUM_SAMPLES_PER_FREQ + self.GUARD_INTERVAL + self.NUM_SAMPLES_PER_SLICE]
            
            signal21 = signal2[0:self.NUM_SAMPLES_PER_SLICE]
            signal22 = signal2[self.NUM_SAMPLES_PER_FREQ + self.GUARD_INTERVAL :
                              self.NUM_SAMPLES_PER_FREQ + self.GUARD_INTERVAL + self.NUM_SAMPLES_PER_SLICE]
            signal23 = signal2[2*self.NUM_SAMPLES_PER_FREQ + self.GUARD_INTERVAL :
                              2*self.NUM_SAMPLES_PER_FREQ + self.GUARD_INTERVAL + self.NUM_SAMPLES_PER_SLICE]
            
            logger.debug(f"  Slice 1 (ref): {len(signal11)} samples")
            logger.debug(f"  Slice 2 (measurement): {len(signal12)} samples")
            logger.debug(f"  Slice 3 (ref check): {len(signal13)} samples")
            
            # ==================== FILTER SIGNALS ====================
            logger.info("Filtering signals...")
            
            signal12_filtered = self.signal_processor.filter_iq(signal12, self.signal_bandwidth_khz)
            signal22_filtered = self.signal_processor.filter_iq(signal22, self.signal_bandwidth_khz)
            signal11_filtered = self.signal_processor.filter_iq(signal11, self.ref_bandwidth_khz)
            signal13_filtered = self.signal_processor.filter_iq(signal13, self.ref_bandwidth_khz)
            signal21_filtered = self.signal_processor.filter_iq(signal21, self.ref_bandwidth_khz)
            signal23_filtered = self.signal_processor.filter_iq(signal23, self.ref_bandwidth_khz)
            
            # ==================== CORRELATE SLICE 1 (Reference) ====================
            logger.info("-" * 80)
            logger.info("SLICE 1 CORRELATION (Reference)")
            
            corr_signal_1 = self.signal_processor.correlate_iq(
                signal11_filtered, signal21_filtered,
                corr_type=self.corr_type,
                smoothing_factor=self.smoothing_factor_ref
            )
            
            delay1_idx = np.argmax(corr_signal_1)
            delay1 = delay1_idx - len(signal11)
            reliability1 = self.signal_processor.corr_reliability(corr_signal_1)
            
            logger.info(f"  Delay: {delay1} samples")
            logger.info(f"  Reliability: {reliability1:.4f}")
            
            # ==================== CORRELATE SLICE 2 (Measurement) ====================
            logger.info("-" * 80)
            logger.info("SLICE 2 CORRELATION (Measurement)")
            
            valid_samples_right = (rx_distance - rx_distance_diff) / (self.SPEED_OF_LIGHT / self.SAMPLE_RATE)
            valid_samples_left = (-rx_distance - rx_distance_diff) / (self.SPEED_OF_LIGHT / self.SAMPLE_RATE)
            
            logger.debug(f"  Valid sample range: {int(valid_samples_left)} to {int(valid_samples_right)}")
            
            corr_signal_2 = self.signal_processor.correlate_iq(
                signal12_filtered, signal22_filtered,
                corr_type=self.corr_type,
                smoothing_factor=self.smoothing_factor
            )
            
            corr_signal_2_valid = np.full_like(corr_signal_2, -1.0)
            
            valid_right = int(min(valid_samples_right + 1 + 2, len(corr_signal_2) - delay1_idx - 1))
            valid_left = int(min(abs(valid_samples_left) + 1 + 2, delay1_idx))
            
            corr_signal_2_valid[delay1_idx - valid_left : delay1_idx + valid_right] = \
                corr_signal_2[delay1_idx - valid_left : delay1_idx + valid_right]
            
            delay2_idx = np.argmax(corr_signal_2_valid)
            delay2 = delay2_idx - len(signal12)
            reliability2 = self.signal_processor.corr_reliability(corr_signal_2_valid)
            
            logger.info(f"  Delay: {delay2} samples")
            logger.info(f"  Reliability: {reliability2:.4f}")
            
            # ==================== CORRELATE SLICE 3 (Reference Check) ====================
            logger.info("-" * 80)
            logger.info("SLICE 3 CORRELATION (Reference Check)")
            
            corr_signal_3 = self.signal_processor.correlate_iq(
                signal13_filtered, signal23_filtered,
                corr_type=self.corr_type,
                smoothing_factor=self.smoothing_factor_ref
            )
            
            delay3_idx = np.argmax(corr_signal_3)
            delay3 = delay3_idx - len(signal13)
            reliability3 = self.signal_processor.corr_reliability(corr_signal_3)
            
            logger.info(f"  Delay: {delay3} samples")
            logger.info(f"  Reliability: {reliability3:.4f}")
            
            # ==================== MERGE REFERENCE SIGNALS ====================
            logger.info("-" * 80)
            logger.info("MERGING REFERENCE SIGNALS")
            
            if abs(delay1 - delay3) <= 2:
                avg_delay13 = (delay1 + delay3) / 2
                logger.info(f"  Delays match (diff={abs(delay1-delay3):.1f}), using average")
            else:
                logger.warning(f"  Delay mismatch: ref={delay1}, check={delay3} (diff={abs(delay1-delay3)})")
                if reliability1 > reliability3:
                    avg_delay13 = delay1
                    logger.info(f"  Using ref (reliability={reliability1:.4f} > {reliability3:.4f})")
                else:
                    avg_delay13 = delay3
                    logger.info(f"  Using check (reliability={reliability3:.4f} >= {reliability1:.4f})")
            
            # ==================== CALCULATE FINAL TDOA ====================
            logger.info("-" * 80)
            logger.info("CALCULATING FINAL TDOA")
            
            ref_signal_diff_samples = (rx_distance_diff / self.SPEED_OF_LIGHT) * self.SAMPLE_RATE
            
            doa_samples = delay2 - avg_delay13 + ref_signal_diff_samples
            doa_meters = (doa_samples / self.SAMPLE_RATE) * self.SPEED_OF_LIGHT
            
            overall_reliability = min([reliability1, reliability2, reliability3])
            
            logger.info(f"  TDOA: {doa_meters:.2f} m ({doa_samples:.1f} samples)")
            logger.info(f"  Overall Reliability: {overall_reliability:.4f}")
            logger.info("=" * 80)
            
            result = TDOAResult(
                doa_meters=float(doa_meters),
                doa_samples=float(doa_samples),
                reliability=float(overall_reliability),
                delay1=float(delay1),
                delay2=float(delay2),
                delay3=float(delay3),
                details={
                    'avg_delay13': float(avg_delay13),
                    'ref_signal_diff_samples': float(ref_signal_diff_samples),
                    'reliability1': float(reliability1),
                    'reliability2': float(reliability2),
                    'reliability3': float(reliability3),
                    'corr_type': self.corr_type,
                    'bandwidth_khz': self.signal_bandwidth_khz,
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"✗ TDOA calculation failed: {str(e)}", exc_info=True)
            raise
    
    def process_recording(self, iq_file_1: str, iq_file_2: str, iq_file_3: str,
                         output_dir: str = "./output/") -> Dict:
        """
        Process 3 IQ recordings dan calculate TDOA + generate output
        Main orchestration function
        Translate MATLAB: evaluation_main.m
        
        Parameters:
        -----------
        iq_file_1, iq_file_2, iq_file_3 : str
            Path ke 3 IQ data files
        output_dir : str
            Output directory
        
        Returns:
            Complete TDOA analysis results
        """
        
        try:
            logger.info("\n" + "="*100)
            logger.info("TDOA PROCESSING PIPELINE START")
            logger.info("="*100)
            
            # ==================== READ IQ FILES ====================
            logger.info("\nReading IQ files...")
            
            # ✅ NEW: Better error handling for file reading
            try:
                signal1 = self.signal_processor.read_iq_file(iq_file_1)
                signal2 = self.signal_processor.read_iq_file(iq_file_2)
                signal3 = self.signal_processor.read_iq_file(iq_file_3)
            except FileNotFoundError as e:
                logger.error(f"✗ IQ file not found: {e}")
                raise
            except Exception as e:
                logger.error(f"✗ Error reading IQ file: {e}")
                raise
            
            # ==================== PREPARE GEOMETRY ====================
            geometry = self.prepare_receiver_geometry()
            
            # ==================== CALCULATE TDOA FOR 3 PAIRS ====================
            logger.info("\n" + "-"*100)
            tdoa_12 = self.calculate_tdoa_pair(
                signal1, signal2,
                geometry['rx_distance_diff_12'],
                geometry['rx_distance_12'],
                "RX1-RX2"
            )
            
            logger.info("\n" + "-"*100)
            tdoa_13 = self.calculate_tdoa_pair(
                signal1, signal3,
                geometry['rx_distance_diff_13'],
                geometry['rx_distance_13'],
                "RX1-RX3"
            )
            
            logger.info("\n" + "-"*100)
            tdoa_23 = self.calculate_tdoa_pair(
                signal2, signal3,
                geometry['rx_distance_diff_23'],
                geometry['rx_distance_23'],
                "RX2-RX3"
            )
            
            # ==================== GENERATE HYPERBOLAS ====================
            logger.info("\n" + "-"*100)
            logger.info("GENERATING HYPERBOLAS...")
            
            hyp12_lat, hyp12_lon = GeometryEngine.generate_hyperbola(
                tdoa_12.doa_meters,
                geometry['rx1_lat'], geometry['rx1_lon'],
                geometry['rx2_lat'], geometry['rx2_lon'],
                geometry['geo_ref_lat'], geometry['geo_ref_lon'],
                'RX1', 'RX2'
            )
            
            hyp13_lat, hyp13_lon = GeometryEngine.generate_hyperbola(
                tdoa_13.doa_meters,
                geometry['rx1_lat'], geometry['rx1_lon'],
                geometry['rx3_lat'], geometry['rx3_lon'],
                geometry['geo_ref_lat'], geometry['geo_ref_lon'],
                'RX1', 'RX3'
            )
            
            hyp23_lat, hyp23_lon = GeometryEngine.generate_hyperbola(
                tdoa_23.doa_meters,
                geometry['rx2_lat'], geometry['rx2_lon'],
                geometry['rx3_lat'], geometry['rx3_lon'],
                geometry['geo_ref_lat'], geometry['geo_ref_lon'],
                'RX2', 'RX3'
            )
            
            # ==================== FIND TX LOCATION ====================
            logger.info("\n" + "-"*100)
            logger.info("FINDING TX LOCATION FROM HYPERBOLAS...")
            
            tx_lat, tx_lon = GeometryEngine.find_tx_location_from_3_hyperbolas(
                hyp12_lat, hyp12_lon,
                hyp13_lat, hyp13_lon,
                hyp23_lat, hyp23_lon,
                geometry['geo_ref_lat'], geometry['geo_ref_lon']
            )
            
            # ==================== CREATE HEATMAP ====================
            logger.info("\n" + "-"*100)
            logger.info("CREATING MSE HEATMAP...")
            
            heatmap_data = self._create_heatmap(
                tdoa_12.doa_meters,
                tdoa_13.doa_meters,
                tdoa_23.doa_meters,
                geometry
            )
            
            # ==================== COMPILE RESULTS ====================
            results = {
                'geometry': geometry,
                'tdoa_12': {
                    'doa_meters': tdoa_12.doa_meters,
                    'doa_samples': tdoa_12.doa_samples,
                    'reliability': tdoa_12.reliability,
                    'details': tdoa_12.details
                },
                'tdoa_13': {
                    'doa_meters': tdoa_13.doa_meters,
                    'doa_samples': tdoa_13.doa_samples,
                    'reliability': tdoa_13.reliability,
                    'details': tdoa_13.details
                },
                'tdoa_23': {
                    'doa_meters': tdoa_23.doa_meters,
                    'doa_samples': tdoa_23.doa_samples,
                    'reliability': tdoa_23.reliability,
                    'details': tdoa_23.details
                },
                'hyperbolas': {
                    'hyp12': {'lat': hyp12_lat, 'lon': hyp12_lon},
                    'hyp13': {'lat': hyp13_lat, 'lon': hyp13_lon},
                    'hyp23': {'lat': hyp23_lat, 'lon': hyp23_lon}
                },
                'tx_location': {
                    'latitude': tx_lat,
                    'longitude': tx_lon
                },
                'heatmap': heatmap_data
            }
            
            # ✅ NEW: Save results to file
            self._save_results(results, output_dir)
            
            logger.info("\n" + "="*100)
            logger.info("TDOA PROCESSING PIPELINE COMPLETED SUCCESSFULLY")
            logger.info("="*100)
            
            return results
            
        except Exception as e:
            logger.error(f"✗ Processing failed: {str(e)}", exc_info=True)
            raise
    
    def _save_results(self, results: Dict, output_dir: str) -> None:  # ✅ NEW: Save method
        """Save results to JSON file"""
        
        try:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            output_file = Path(output_dir) / "tdoa_results.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"✓ Results saved to {output_file}")
        except Exception as e:
            logger.error(f"✗ Failed to save results: {e}")
    
    def _create_heatmap(self, doa_12_meters: float, doa_13_meters: float,
                       doa_23_meters: float, geometry: Dict) -> Dict:
        """
        Create MSE-based heatmap untuk TX localization
        Translate MATLAB: create_heatmap.m
        
        Parameters:
        -----------
        doa_*_meters : float
            TDOA values untuk 3 pairs
        geometry : Dict
            Receiver geometry
        
        Returns:
            Heatmap data dictionary
        """
        
        try:
            # ✅ NEW: Validate heatmap resolution
            if self.heatmap_resolution < 10 or self.heatmap_resolution > 500:
                logger.warning(f"Heatmap resolution {self.heatmap_resolution} out of range, using 100")
                self.heatmap_resolution = 100
            
            logger.info(f"Creating {self.heatmap_resolution}x{self.heatmap_resolution} heatmap...")
            
            # Define grid area (±0.03° around geo_ref)
            lat_span = 0.03
            lon_span = 0.03
            
            start_lat = geometry['geo_ref_lat'] - lat_span
            stop_lat = geometry['geo_ref_lat'] + lat_span
            start_lon = geometry['geo_ref_lon'] - lon_span
            stop_lon = geometry['geo_ref_lon'] + lon_span
            
            # Create grid points
            heat_lat = np.linspace(start_lat, stop_lat, self.heatmap_resolution)
            heat_lon = np.linspace(start_lon, stop_lon, self.heatmap_resolution)
            
            mse_doa = np.zeros((self.heatmap_resolution, self.heatmap_resolution))
            
            # ✅ NEW: Progress logging
            total_points = self.heatmap_resolution ** 2
            processed = 0
            
            # For each grid point, calculate MSE
            for lat_idx in range(self.heatmap_resolution):
                for lon_idx in range(self.heatmap_resolution):
                    lat = heat_lat[lat_idx]
                    lon = heat_lon[lon_idx]
                    
                    # Calculate theoretical distances from this point to each RX
                    dist_to_rx1 = GeometryEngine.dist_latlong(
                        lat, lon,
                        geometry['rx1_lat'], geometry['rx1_lon'],
                        geometry['geo_ref_lat'], geometry['geo_ref_lon']
                    )
                    dist_to_rx2 = GeometryEngine.dist_latlong(
                        lat, lon,
                        geometry['rx2_lat'], geometry['rx2_lon'],
                        geometry['geo_ref_lat'], geometry['geo_ref_lon']
                    )
                    dist_to_rx3 = GeometryEngine.dist_latlong(
                        lat, lon,
                        geometry['rx3_lat'], geometry['rx3_lon'],
                        geometry['geo_ref_lat'], geometry['geo_ref_lon']
                    )
                    
                    # Calculate theoretical DOA
                    theoretical_doa_12 = dist_to_rx1 - dist_to_rx2
                    theoretical_doa_13 = dist_to_rx1 - dist_to_rx3
                    theoretical_doa_23 = dist_to_rx2 - dist_to_rx3
                    
                    # Calculate MSE
                    error_12 = (theoretical_doa_12 - doa_12_meters) ** 2
                    error_13 = (theoretical_doa_13 - doa_13_meters) ** 2
                    error_23 = (theoretical_doa_23 - doa_23_meters) ** 2
                    
                    mse = error_12 + error_13 + error_23
                    mse_doa[lon_idx, lat_idx] = mse
                    
                    processed += 1
                    if processed % max(1, total_points // 10) == 0:
                        logger.debug(f"  Heatmap progress: {processed}/{total_points}")
            
            # Invert MSE
            mse_doa_inverted = 1.0 / (mse_doa + 1e-10)
            
            # Normalize to 0..1
            max_mse = np.max(mse_doa_inverted)
            if max_mse > 0:
                mse_normalized = mse_doa_inverted / max_mse
            else:
                mse_normalized = mse_doa_inverted
            
            # Find peak
            peak_idx = np.argmax(mse_normalized)
            peak_lat_idx, peak_lon_idx = np.unravel_index(peak_idx, mse_normalized.shape)
            peak_lat = heat_lat[peak_lat_idx]
            peak_lon = heat_lon[peak_lon_idx]
            peak_magnitude = mse_normalized[peak_lat_idx, peak_lon_idx]
            
            logger.info(f"✓ Heatmap created")
            logger.info(f"  Peak at: ({peak_lat:.8f}, {peak_lon:.8f})")
            logger.info(f"  Peak magnitude: {peak_magnitude:.4f}")
            
            return {
                'heat_lat': heat_lat.tolist(),
                'heat_lon': heat_lon.tolist(),
                'magnitude': mse_normalized.tolist(),
                'peak_lat': peak_lat,
                'peak_lon': peak_lon,
                'peak_magnitude': peak_magnitude,
                'start_lat': start_lat,
                'stop_lat': stop_lat,
                'start_lon': start_lon,
                'stop_lon': stop_lon
            }
            
        except Exception as e:
            logger.error(f"✗ Heatmap creation failed: {str(e)}")
            raise
