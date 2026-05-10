"""
Automation Orchestrator Module - COMPLETE
Main controller untuk orchestrate: Recording → Processing → Visualization
Exact translation dari MATLAB evaluation_main.m + run_batch_evaluation.m
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np
from loguru import logger

from .signal_processor import SignalProcessor
from .geometry_engine import GeometryEngine
from .map_generator import MapGenerator


class AutomationOrchestrator:
    """
    Main orchestrator untuk TDOA automation:
    1. Recording (via SSH ke RPi)
    2. IQ Signal Processing
    3. TDOA Calculation (3 pairs)
    4. Hyperbola Generation
    5. Map Visualization
    
    Dari MATLAB: evaluation_main.m + run_batch_evaluation.m
    """
    
    # Sampling rate & constants dari MATLAB
    SAMPLE_RATE = 2.048e6  # 2 MSps
    SPEED_OF_LIGHT = 3e8
    NUM_SAMPLES_TOTAL = 3.6e6
    NUM_SAMPLES_PER_FREQ = 1.2e6
    NUM_SAMPLES_PER_SLICE = 1e6
    GUARD_INTERVAL = 200e3
    
    def __init__(self, config_path: str):
        """
        Initialize orchestrator dengan configuration
        
        Args:
            config_path: Path ke JSON config file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # Initialize components
        self.signal_processor = SignalProcessor()
        self.map_generator = MapGenerator(
            output_dir=self.config.get('output', {}).get('map_dir', 'output')
        )
        
        # Setup logging
        log_dir = Path(self.config.get('output', {}).get('log_dir', 'logs'))
        log_dir.mkdir(exist_ok=True)
        
        logger.info("✓ AutomationOrchestrator initialized")
    
    def _load_config(self) -> Dict:
        """Load and parse configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"✓ Configuration loaded: {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {str(e)}")
            raise
    
    def process_triplet(self, 
                       file1: str,
                       file2: str,
                       file3: str,
                       signal_bandwidth_khz: int = 40,
                       ref_bandwidth_khz: int = 40,
                       smoothing_factor: int = 0,
                       smoothing_factor_ref: int = 0,
                       corr_type: str = 'dphase',
                       interpol_factor: int = 0,
                       heatmap_resolution: int = 200,
                       heatmap_threshold: float = 0.70) -> Dict:
        """
        Process satu triplet file (3 RX recordings)
        Exact translation dari MATLAB evaluation_main.m
        
        Args:
            file1, file2, file3: Path ke 3 IQ files
            signal_bandwidth_khz: Filter bandwidth untuk measurement signal
            ref_bandwidth_khz: Filter bandwidth untuk reference signal
            
        Returns:
            Dictionary dengan hasil lengkap TDOA + maps
        """
        
        try:
            logger.info("="*100)
            logger.info("TRIPLET PROCESSING START")
            logger.info("="*100)
            logger.info(f"File 1: {Path(file1).name}")
            logger.info(f"File 2: {Path(file2).name}")
            logger.info(f"File 3: {Path(file3).name}")
            
            # Extract RX positions dari config
            rx1_lat = self.config['receivers']['rx1']['latitude']
            rx1_lon = self.config['receivers']['rx1']['longitude']
            rx2_lat = self.config['receivers']['rx2']['latitude']
            rx2_lon = self.config['receivers']['rx2']['longitude']
            rx3_lat = self.config['receivers']['rx3']['latitude']
            rx3_lon = self.config['receivers']['rx3']['longitude']
            
            tx_ref_lat = self.config['transmitter']['reference']['latitude']
            tx_ref_lon = self.config['transmitter']['reference']['longitude']
            tx_cari_lat = self.config['transmitter']['target']['latitude']
            tx_cari_lon = self.config['transmitter']['target']['longitude']
            
            center_point_lat = self.config['center_point']['latitude']
            center_point_lon = self.config['center_point']['longitude']
            
            # Calculate geodetic reference point (mean dari 3 RX)
            geo_ref_lat = np.mean([rx1_lat, rx2_lat, rx3_lat])
            geo_ref_lon = np.mean([rx1_lon, rx2_lon, rx3_lon])
            
            logger.debug(f"Geodetic reference: ({geo_ref_lat:.8f}, {geo_ref_lon:.8f})")
            
            # Calculate known signal path differences
            rx_distance_diff12 = (
                GeometryEngine.dist_latlong(
                    tx_ref_lat, tx_ref_lon, rx1_lat, rx1_lon,
                    geo_ref_lat, geo_ref_lon
                ) -
                GeometryEngine.dist_latlong(
                    tx_ref_lat, tx_ref_lon, rx2_lat, rx2_lon,
                    geo_ref_lat, geo_ref_lon
                )
            )
            
            rx_distance_diff13 = (
                GeometryEngine.dist_latlong(
                    tx_ref_lat, tx_ref_lon, rx1_lat, rx1_lon,
                    geo_ref_lat, geo_ref_lon
                ) -
                GeometryEngine.dist_latlong(
                    tx_ref_lat, tx_ref_lon, rx3_lat, rx3_lon,
                    geo_ref_lat, geo_ref_lon
                )
            )
            
            rx_distance_diff23 = (
                GeometryEngine.dist_latlong(
                    tx_ref_lat, tx_ref_lon, rx2_lat, rx2_lon,
                    geo_ref_lat, geo_ref_lon
                ) -
                GeometryEngine.dist_latlong(
                    tx_ref_lat, tx_ref_lon, rx3_lat, rx3_lon,
                    geo_ref_lat, geo_ref_lon
                )
            )
            
            # Distance antara 2 RX
            rx_distance12 = GeometryEngine.dist_latlong(
                rx1_lat, rx1_lon, rx2_lat, rx2_lon,
                geo_ref_lat, geo_ref_lon
            )
            
            rx_distance13 = GeometryEngine.dist_latlong(
                rx1_lat, rx1_lon, rx3_lat, rx3_lon,
                geo_ref_lat, geo_ref_lon
            )
            
            rx_distance23 = GeometryEngine.dist_latlong(
                rx2_lat, rx2_lon, rx3_lat, rx3_lon,
                geo_ref_lat, geo_ref_lon
            )
            
            logger.info("-"*100)
            logger.info("READ IQ DATA FILES")
            
            # Read signals
            signal1 = self.signal_processor.read_file_iq(file1)
            signal2 = self.signal_processor.read_file_iq(file2)
            signal3 = self.signal_processor.read_file_iq(file3)
            
            # Verify lengths
            if len(signal1) != self.NUM_SAMPLES_TOTAL:
                raise ValueError(f"Signal 1 length {len(signal1)} != {self.NUM_SAMPLES_TOTAL}")
            if len(signal2) != self.NUM_SAMPLES_TOTAL:
                raise ValueError(f"Signal 2 length {len(signal2)} != {self.NUM_SAMPLES_TOTAL}")
            if len(signal3) != self.NUM_SAMPLES_TOTAL:
                raise ValueError(f"Signal 3 length {len(signal3)} != {self.NUM_SAMPLES_TOTAL}")
            
            logger.info("-"*100)
            logger.info("CORRELATION 1 & 2")
            
            # Calculate TDOA para RX1 vs RX2
            result12 = self.signal_processor.calculate_tdoa(
                signal1, signal2,
                rx_distance_diff12, rx_distance12,
                smoothing_factor, corr_type,
                signal_bandwidth_khz, ref_bandwidth_khz,
                smoothing_factor_ref, interpol_factor
            )
            
            logger.info("-"*100)
            logger.info("CORRELATION 1 & 3")
            
            # Calculate TDOA para RX1 vs RX3
            result13 = self.signal_processor.calculate_tdoa(
                signal1, signal3,
                rx_distance_diff13, rx_distance13,
                smoothing_factor, corr_type,
                signal_bandwidth_khz, ref_bandwidth_khz,
                smoothing_factor_ref, interpol_factor
            )
            
            logger.info("-"*100)
            logger.info("CORRELATION 2 & 3")
            
            # Calculate TDOA para RX2 vs RX3
            result23 = self.signal_processor.calculate_tdoa(
                signal2, signal3,
                rx_distance_diff23, rx_distance23,
                smoothing_factor, corr_type,
                signal_bandwidth_khz, ref_bandwidth_khz,
                smoothing_factor_ref, interpol_factor
            )
            
            logger.info("-"*100)
            logger.info("GENERATING HYPERBOLAS")
            
            # Generate hyperbolas
            hyp_lat12, hyp_lon12 = GeometryEngine.generate_hyperbola(
                result12['doa_meters'],
                rx1_lat, rx1_lon, rx2_lat, rx2_lon,
                geo_ref_lat, geo_ref_lon,
                'RX1', 'RX2'
            )
            
            hyp_lat13, hyp_lon13 = GeometryEngine.generate_hyperbola(
                result13['doa_meters'],
                rx1_lat, rx1_lon, rx3_lat, rx3_lon,
                geo_ref_lat, geo_ref_lon,
                'RX1', 'RX3'
            )
            
            hyp_lat23, hyp_lon23 = GeometryEngine.generate_hyperbola(
                result23['doa_meters'],
                rx2_lat, rx2_lon, rx3_lat, rx3_lon,
                geo_ref_lat, geo_ref_lon,
                'RX2', 'RX3'
            )
            
            logger.info("-"*100)
            logger.info("FINDING INTERSECTION POINTS")
            
            # Find intersection points (dari MATLAB evaluation_main line 245-267)
            hyp_lat12_arr = np.array(hyp_lat12)
            hyp_lon12_arr = np.array(hyp_lon12)
            hyp_lat13_arr = np.array(hyp_lat13)
            hyp_lon13_arr = np.array(hyp_lon13)
            hyp_lat23_arr = np.array(hyp_lat23)
            hyp_lon23_arr = np.array(hyp_lon23)
            
            # Find closest points between hyperbolas
            logger.debug("Finding closest pairs between hyperbola 12 & 13...")
            dist12_matrix = np.zeros((len(hyp_lat12_arr), len(hyp_lat13_arr)))
            for i in range(len(hyp_lat12_arr)):
                for j in range(len(hyp_lat13_arr)):
                    dist12_matrix[i, j] = GeometryEngine.dist_latlong(
                        hyp_lat12_arr[i], hyp_lon12_arr[i],
                        hyp_lat13_arr[j], hyp_lon13_arr[j],
                        geo_ref_lat, geo_ref_lon
                    )
            
            min_idx12 = np.argmin(dist12_matrix)
            row_idx12, col_idx12 = np.unravel_index(min_idx12, dist12_matrix.shape)
            avg_lat12 = (hyp_lat12_arr[row_idx12] + hyp_lat13_arr[col_idx12]) / 2
            avg_lon12 = (hyp_lon12_arr[row_idx12] + hyp_lon13_arr[col_idx12]) / 2
            
            logger.debug("Finding closest pairs between hyperbola 12 & 23...")
            dist13_matrix = np.zeros((len(hyp_lat12_arr), len(hyp_lat23_arr)))
            for i in range(len(hyp_lat12_arr)):
                for j in range(len(hyp_lat23_arr)):
                    dist13_matrix[i, j] = GeometryEngine.dist_latlong(
                        hyp_lat12_arr[i], hyp_lon12_arr[i],
                        hyp_lat23_arr[j], hyp_lon23_arr[j],
                        geo_ref_lat, geo_ref_lon
                    )
            
            min_idx13 = np.argmin(dist13_matrix)
            row_idx13, col_idx13 = np.unravel_index(min_idx13, dist13_matrix.shape)
            avg_lat13 = (hyp_lat12_arr[row_idx13] + hyp_lat23_arr[col_idx13]) / 2
            avg_lon13 = (hyp_lon12_arr[row_idx13] + hyp_lon23_arr[col_idx13]) / 2
            
            logger.debug("Finding closest pairs between hyperbola 13 & 23...")
            dist23_matrix = np.zeros((len(hyp_lat13_arr), len(hyp_lat23_arr)))
            for i in range(len(hyp_lat13_arr)):
                for j in range(len(hyp_lat23_arr)):
                    dist23_matrix[i, j] = GeometryEngine.dist_latlong(
                        hyp_lat13_arr[i], hyp_lon13_arr[i],
                        hyp_lat23_arr[j], hyp_lon23_arr[j],
                        geo_ref_lat, geo_ref_lon
                    )
            
            min_idx23 = np.argmin(dist23_matrix)
            row_idx23, col_idx23 = np.unravel_index(min_idx23, dist23_matrix.shape)
            avg_lat23 = (hyp_lat13_arr[row_idx23] + hyp_lat23_arr[col_idx23]) / 2
            avg_lon23 = (hyp_lon13_arr[row_idx23] + hyp_lon23_arr[col_idx23]) / 2
            
            # Final average from all 3 intersections
            avg_lat_final = (avg_lat12 + avg_lat13 + avg_lat23) / 3
            avg_lon_final = (avg_lon12 + avg_lon13 + avg_lon23) / 3
            
            logger.info(f"Final TX location: ({avg_lat_final:.8f}, {avg_lon_final:.8f})")
            
            logger.info("-"*100)
            logger.info("GENERATING HEATMAP")
            
            # Generate heatmap (dari MATLAB create_heatmap.m)
            heat_lat, heat_lon, heat_mag = self._create_heatmap(
                result12['doa_meters'],
                result13['doa_meters'],
                result23['doa_meters'],
                rx1_lat, rx1_lon,
                rx2_lat, rx2_lon,
                rx3_lat, rx3_lon,
                geo_ref_lat, geo_ref_lon,
                heatmap_resolution
            )
            
            logger.info("-"*100)
            logger.info("GENERATING HTML MAP")
            
            # Prepare RX positions untuk HTML (11 points dari MATLAB)
            rx_positions = {
                'RX1': (rx1_lat, rx1_lon),
                'RX2': (rx2_lat, rx2_lon),
                'RX3': (rx3_lat, rx3_lon),
                'TX_CARI': (tx_cari_lat, tx_cari_lon),
                'TX_REF': (tx_ref_lat, tx_ref_lon),
                'GEO_REF': (geo_ref_lat, geo_ref_lon),
                'AVG_FINAL': (avg_lat_final, avg_lon_final),
                'CENTER_POINT': (center_point_lat, center_point_lon),
                'AVG_12': (avg_lat12, avg_lon12),
                'AVG_13': (avg_lat13, avg_lon13),
                'AVG_23': (avg_lat23, avg_lon23)
            }
            
            # Prepare hyperbolas
            hyperbolas = {
                'RX1_RX2': (hyp_lat12, hyp_lon12),
                'RX1_RX3': (hyp_lat13, hyp_lon13),
                'RX2_RX3': (hyp_lat23, hyp_lon23)
            }
            
            # Prepare heatmap data
            heatmap_data = {
                'lat': heat_lat,
                'lon': heat_lon,
                'mag': heat_mag
            }
            
            # Generate HTML map
            html_filename = f"map_{Path(file1).stem}_{corr_type}_bw{signal_bandwidth_khz}.html"
            self.map_generator.create_osm_html(
                html_filename,
                rx_positions,
                hyperbolas,
                heatmap_data,
                heatmap_threshold
            )
            
            # Compile results
            results = {
                'timestamp': datetime.now().isoformat(),
                'files': {
                    'rx1': Path(file1).name,
                    'rx2': Path(file2).name,
                    'rx3': Path(file3).name
                },
                'geometry': {
                    'rx1': {'lat': rx1_lat, 'lon': rx1_lon},
                    'rx2': {'lat': rx2_lat, 'lon': rx2_lon},
                    'rx3': {'lat': rx3_lat, 'lon': rx3_lon},
                    'geo_ref': {'lat': geo_ref_lat, 'lon': geo_ref_lon},
                    'tx_ref': {'lat': tx_ref_lat, 'lon': tx_ref_lon},
                    'tx_cari': {'lat': tx_cari_lat, 'lon': tx_cari_lon}
                },
                'tdoa_results': {
                    'rx1_rx2': result12,
                    'rx1_rx3': result13,
                    'rx2_rx3': result23
                },
                'tx_location': {
                    'latitude': avg_lat_final,
                    'longitude': avg_lon_final,
                    'intersection_12': {'lat': avg_lat12, 'lon': avg_lon12},
                    'intersection_13': {'lat': avg_lat13, 'lon': avg_lon13},
                    'intersection_23': {'lat': avg_lat23, 'lon': avg_lon23}
                },
                'heatmap_info': {
                    'resolution': heatmap_resolution,
                    'threshold': heatmap_threshold
                },
                'html_map': html_filename
            }
            
            logger.info("="*100)
            logger.info("TRIPLET PROCESSING COMPLETED")
            logger.info("="*100)
            
            return results
            
        except Exception as e:
            logger.error(f"Processing failed: {str(e)}", exc_info=True)
            raise
    
    def _create_heatmap(self,
                       doa12_m: float,
                       doa13_m: float,
                       doa23_m: float,
                       rx1_lat: float, rx1_lon: float,
                       rx2_lat: float, rx2_lon: float,
                       rx3_lat: float, rx3_lon: float,
                       geo_ref_lat: float, geo_ref_lon: float,
                       resolution: int = 200) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Create heatmap using MSE (Mean Squared Error)
        Dari MATLAB: create_heatmap.m
        """
        
        try:
            logger.info(f"Creating heatmap ({resolution}x{resolution})...")
            
            # Define area (±0.03 degrees dari geo_ref)
            lat_span = 0.03
            lon_span = 0.03
            
            start_lat = geo_ref_lat - lat_span
            stop_lat = geo_ref_lat + lat_span
            start_lon = geo_ref_lon - lon_span
            stop_lon = geo_ref_lon + lon_span
            
            # Create grid
            heat_lat = np.linspace(start_lat, stop_lat, resolution)
            heat_lon = np.linspace(start_lon, stop_lon, resolution)
            
            # Initialize MSE matrix
            mse_doa = np.zeros((resolution, resolution))
            
            # Calculate MSE untuk setiap grid point
            for lat_idx in range(resolution):
                for lon_idx in range(resolution):
                    point_lat = heat_lat[lat_idx]
                    point_lon = heat_lon[lon_idx]
                    
                    # Distance dari point ke masing-masing RX
                    dist_to_rx1 = GeometryEngine.dist_latlong(
                        point_lat, point_lon, rx1_lat, rx1_lon,
                        geo_ref_lat, geo_ref_lon
                    )
                    
                    dist_to_rx2 = GeometryEngine.dist_latlong(
                        point_lat, point_lon, rx2_lat, rx2_lon,
                        geo_ref_lat, geo_ref_lon
                    )
                    
                    dist_to_rx3 = GeometryEngine.dist_latlong(
                        point_lat, point_lon, rx3_lat, rx3_lon,
                        geo_ref_lat, geo_ref_lon
                    )
                    
                    # Theoretical DOA at this point
                    current_doa12 = dist_to_rx1 - dist_to_rx2
                    current_doa13 = dist_to_rx1 - dist_to_rx3
                    current_doa23 = dist_to_rx2 - dist_to_rx3
                    
                    # MSE
                    doa_error = (
                        (current_doa12 - doa12_m)**2 +
                        (current_doa13 - doa13_m)**2 +
                        (current_doa23 - doa23_m)**2
                    )
                    
                    mse_doa[lon_idx, lat_idx] = doa_error
            
            # Invert MSE (1/MSE)
            mse_doa = 1.0 / (mse_doa + 1e-10)
            
            # Normalize to 0..1
            max_mse = np.max(mse_doa)
            if max_mse > 0:
                mse_doa = mse_doa / max_mse
            
            logger.info(f"✓ Heatmap created: {mse_doa.min():.6f} to {mse_doa.max():.6f}")
            
            return heat_lat, heat_lon, mse_doa
            
        except Exception as e:
            logger.error(f"Heatmap creation failed: {str(e)}")
            raise
    
    def execute_batch(self,
                     input_pattern: str,
                     num_files: int = 30,
                     signal_bandwidth_khz: int = 40,
                     **kwargs) -> List[Dict]:
        """
        Execute batch processing untuk multiple triplets
        Dari MATLAB: run_batch_evaluation.m
        
        Args:
            input_pattern: Pattern untuk nama files (e.g., "1000_980_2025_7_31_")
            num_files: Number of triplets to process
            signal_bandwidth_khz: Signal bandwidth
        
        Returns:
            List of processing results
        """
        
        try:
            logger.info("="*100)
            logger.info("BATCH PROCESSING START")
            logger.info("="*100)
            logger.info(f"Processing pattern: {input_pattern}")
            logger.info(f"Number of files: {num_files}")
            
            results = []
            success_count = 0
            failed_files = []
            
            # Base directory untuk recorded data
            data_dir = Path(self.config.get('output', {}).get('data_dir', 'recorded_data'))
            data_dir.mkdir(exist_ok=True)
            
            # Loop untuk setiap triplet
            for idx in range(num_files):
                try:
                    # Construct filenames (dari MATLAB run_batch_evaluation.m)
                    filename_base = f"{input_pattern}{str(idx).zfill(3)}.dat"
                    
                    file1 = str(data_dir / f"1_{filename_base}")
                    file2 = str(data_dir / f"2_{filename_base}")
                    file3 = str(data_dir / f"3_{filename_base}")
                    
                    # Check if files exist
                    if not (Path(file1).exists() and Path(file2).exists() and Path(file3).exists()):
                        logger.warning(f"[{idx+1}/{num_files}] Files not found, skipping")
                        continue
                    
                    logger.info(f"\n[{idx+1}/{num_files}] Processing triplet {idx}...")
                    
                    # Process triplet
                    result = self.process_triplet(
                        file1, file2, file3,
                        signal_bandwidth_khz=signal_bandwidth_khz,
                        **kwargs
                    )
                    
                    results.append(result)
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Triplet {idx} failed: {str(e)}")
                    failed_files.append(filename_base)
            
            # Summary
            logger.info("\n" + "="*100)
            logger.info("BATCH PROCESSING COMPLETED")
            logger.info("="*100)
            logger.info(f"Total processed: {num_files}")
            logger.info(f"Successful: {success_count}")
            logger.info(f"Failed: {len(failed_files)}")
            
            if failed_files:
                logger.warning("\nFailed files:")
                for f in failed_files:
                    logger.warning(f"  - {f}")
            
            return results
            
        except Exception as e:
            logger.error(f"Batch processing failed: {str(e)}", exc_info=True)
            raise


# Example usage
if __name__ == "__main__":
    orchestrator = AutomationOrchestrator("config.json")
    
    # Process single triplet
    result = orchestrator.process_triplet(
        "recorded_data/1_test.dat",
        "recorded_data/2_test.dat",
        "recorded_data/3_test.dat"
    )
    
    logger.info(f"Result: {json.dumps(result, indent=2)}")