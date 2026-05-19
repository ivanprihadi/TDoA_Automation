"""
Data Processor Module
Handles loading, processing, and analyzing raw IQ data files
"""

import numpy as np
from pathlib import Path
from loguru import logger
from datetime import datetime
import json
from scipy import signal
import struct

class IQDataFile:
    """Represents a single IQ data file"""
    
    def __init__(self, filepath):
        self.filepath = Path(filepath)
        self.filename = self.filepath.name
        self.filesize = self.filepath.stat().st_size if self.filepath.exists() else 0
        self.data = None
        self.sample_rate = 2.4e6  # Default: 2.4 MSPS
        self.loaded = False
        self.metadata = {}
        
    def load_data(self, sample_rate=2.4e6):
        """Load raw IQ data from file"""
        try:
            logger.info(f"📂 Loading IQ data: {self.filename}")
            
            # Read binary data
            with open(self.filepath, 'rb') as f:
                raw_data = f.read()
            
            # Convert bytes to complex IQ samples
            # Format: interleaved I,Q as int16
            int16_data = np.frombuffer(raw_data, dtype=np.int16)
            
            # Reshape to pairs (I, Q)
            iq_data = int16_data.reshape(-1, 2)
            
            # Convert to complex numbers
            self.data = iq_data[:, 0] + 1j * iq_data[:, 1]
            
            # Normalize
            self.data = self.data / 32768.0  # Convert from int16 range
            
            self.sample_rate = sample_rate
            self.loaded = True
            
            logger.info(f"✓ Loaded {len(self.data)} samples at {sample_rate/1e6} MSPS")
            logger.info(f"  Duration: {len(self.data) / sample_rate:.3f} seconds")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading IQ data: {str(e)}", exc_info=True)
            return False
    
    def get_statistics(self):
        """Get signal statistics"""
        if not self.loaded or self.data is None:
            return {}
        
        try:
            power = np.abs(self.data) ** 2
            
            stats = {
                'filename': self.filename,
                'filesize_bytes': self.filesize,
                'num_samples': len(self.data),
                'duration_seconds': len(self.data) / self.sample_rate,
                'sample_rate_msps': self.sample_rate / 1e6,
                'mean_power_db': 10 * np.log10(np.mean(power)),
                'peak_power_db': 10 * np.log10(np.max(power)),
                'min_power_db': 10 * np.log10(np.min(power) + 1e-10),
                'power_std_db': 10 * np.log10(np.std(power)),
                'i_mean': np.mean(self.data.real),
                'q_mean': np.mean(self.data.imag),
                'i_std': np.std(self.data.real),
                'q_std': np.std(self.data.imag)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating statistics: {str(e)}")
            return {}
    
    def get_spectrum(self, nfft=2048):
        """Calculate frequency spectrum"""
        if not self.loaded or self.data is None:
            return None, None
        
        try:
            # Calculate FFT
            fft_result = np.fft.fft(self.data, n=nfft)
            power_spectrum = np.abs(fft_result) ** 2
            
            # Shift DC component to center
            power_spectrum = np.fft.fftshift(power_spectrum)
            power_spectrum_db = 10 * np.log10(power_spectrum + 1e-10)
            
            # Create frequency axis
            freq = np.fft.fftshift(np.fft.fftfreq(nfft, 1 / self.sample_rate))
            
            return freq, power_spectrum_db
            
        except Exception as e:
            logger.error(f"Error calculating spectrum: {str(e)}")
            return None, None
    
    def detect_signal_frequency(self, ref_freq_mhz):
        """Detect signal frequency relative to reference"""
        if not self.loaded or self.data is None:
            return None
        
        try:
            # Mix with reference
            ref_freq_hz = ref_freq_mhz * 1e6
            t = np.arange(len(self.data)) / self.sample_rate
            ref_signal = np.exp(-2j * np.pi * ref_freq_hz * t)
            
            mixed = self.data * ref_signal
            
            # Low-pass filter
            nyquist_freq = self.sample_rate / 2
            cutoff_freq = 50e3  # 50 kHz cutoff
            normalized_cutoff = cutoff_freq / nyquist_freq
            
            if normalized_cutoff >= 1:
                normalized_cutoff = 0.99
            
            b, a = signal.butter(4, normalized_cutoff, btype='low')
            filtered = signal.filtfilt(b, a, mixed)
            
            # Find dominant frequency in filtered signal
            freq, power = signal.welch(filtered, fs=self.sample_rate, nperseg=1024)
            dominant_idx = np.argmax(power)
            dominant_freq_offset = freq[dominant_idx]
            
            target_freq = ref_freq_mhz + (dominant_freq_offset / 1e6)
            
            logger.info(f"✓ Detected target frequency: {target_freq:.3f} MHz")
            
            return {
                'reference_mhz': ref_freq_mhz,
                'target_mhz': target_freq,
                'offset_hz': dominant_freq_offset,
                'power_db': 10 * np.log10(power[dominant_idx] + 1e-10)
            }
            
        except Exception as e:
            logger.error(f"Error detecting frequency: {str(e)}", exc_info=True)
            return None


class DataProcessor:
    """Main data processing engine"""
    
    def __init__(self, output_dir='./output/processed_data'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.files = {}
        self.sessions = {}
        
    def import_file(self, filepath, sample_rate=2.4e6):
        """Import an IQ data file"""
        try:
            logger.info(f"📥 Importing file: {filepath}")
            
            file_path = Path(filepath)
            
            if not file_path.exists():
                logger.error(f"❌ File not found: {filepath}")
                return {'error': f'File not found: {filepath}'}
            
            # Create IQ data file object
            iq_file = IQDataFile(file_path)
            
            # Load data
            if not iq_file.load_data(sample_rate):
                return {'error': 'Failed to load IQ data'}
            
            # Store file
            file_id = file_path.stem
            self.files[file_id] = iq_file
            
            # Get statistics
            stats = iq_file.get_statistics()
            
            logger.info(f"✓ File imported successfully")
            
            return {
                'file_id': file_id,
                'filename': iq_file.filename,
                'status': 'loaded',
                'statistics': stats
            }
            
        except Exception as e:
            logger.error(f"❌ Error importing file: {str(e)}", exc_info=True)
            return {'error': str(e)}
    
    def process_file(self, file_id, ref_freq_mhz, processing_params=None):
        """Process a loaded IQ file"""
        try:
            logger.info(f"🔄 Processing file: {file_id}")
            
            if file_id not in self.files:
                return {'error': f'File not found: {file_id}'}
            
            iq_file = self.files[file_id]
            
            if not iq_file.loaded:
                return {'error': 'File not loaded'}
            
            # Get statistics
            stats = iq_file.get_statistics()
            
            # Detect signal frequency
            freq_detection = iq_file.detect_signal_frequency(ref_freq_mhz)
            
            # Get spectrum
            freq, spectrum = iq_file.get_spectrum(nfft=4096)
            
            # Save spectrum data
            spectrum_file = self.output_dir / f"{file_id}_spectrum.json"
            
            if freq is not None and spectrum is not None:
                spectrum_data = {
                    'frequencies_mhz': (freq / 1e6).tolist(),
                    'power_db': spectrum.tolist(),
                    'reference_freq_mhz': ref_freq_mhz
                }
                
                with open(spectrum_file, 'w') as f:
                    json.dump(spectrum_data, f, indent=2)
            
            result = {
                'file_id': file_id,
                'filename': iq_file.filename,
                'status': 'processed',
                'statistics': stats,
                'frequency_detection': freq_detection,
                'spectrum_file': str(spectrum_file)
            }
            
            logger.info(f"✓ File processed successfully")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error processing file: {str(e)}", exc_info=True)
            return {'error': str(e)}
        
    def process_multiple_files(self, file_ids, ref_freq_mhz, target_freq_mhz=None):
        """Process multiple files for TDOA calculation"""
        try:
            logger.info(f"🔄 Processing {len(file_ids)} files for TDOA")
            logger.info(f"   Reference: {ref_freq_mhz} MHz")
            logger.info(f"   Target: {target_freq_mhz} MHz" if target_freq_mhz else "   Target: Auto-detect")
            
            # Create results directory
            results_dir = self.output_dir / 'results'
            results_dir.mkdir(parents=True, exist_ok=True)
            
            results = []
            
            for file_id in file_ids:
                result = self.process_file(file_id, ref_freq_mhz)
                results.append(result)
            
            # ==================== SAVE RESULTS TO FILE ====================
            
            session_id = f"tdoa_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create formatted result for display
            formatted_results = []
            for idx, result in enumerate(results):
                if 'error' not in result:
                    formatted_results.append({
                        'filename': f"{session_id}_{idx}.json",
                        'created_at': datetime.now().isoformat(),
                        'data': {
                            'session_id': session_id,
                            'file_id': result.get('file_id'),
                            'location': {
                                'latitude': 0.0,  # Mock data
                                'longitude': 0.0,
                                'accuracy_meters': 100.0,
                                'altitude_meters': 0
                            }
                        }
                    })
            
            # Save session data
            session_data = {
                'session_id': session_id,
                'timestamp': datetime.now().isoformat(),
                'parameters': {
                    'file_ids': file_ids,
                    'ref_freq_mhz': ref_freq_mhz,
                    'target_freq_mhz': target_freq_mhz
                },
                'results': results,
                'status': 'completed'
            }
            
            # ✅ SAVE TO JSON FILE
            result_filename = f"{session_id}_results.json"
            result_file = results_dir / result_filename
            
            with open(result_file, 'w') as f:
                json.dump(session_data, f, indent=2, default=str)
            
            logger.info(f"✓ Results saved to: {result_file}")
            logger.info(f"  File size: {result_file.stat().st_size / 1024:.1f} KB")
            
            # Store session in memory
            self.sessions[session_id] = session_data
            
            return {
                'session_id': session_id,
                'status': 'completed',
                'processed_files': len(results),
                'results': formatted_results  # ← RETURN FORMATTED RESULTS
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing multiple files: {str(e)}", exc_info=True)
            return {'error': str(e)}

    def _calculate_tdoa(self, results, ref_freq_mhz, target_freq_mhz):
        """Calculate TDOA (Time Difference of Arrival) from multiple receivers"""
        try:
            logger.info("🔢 Calculating TDOA...")
            
            # Extract frequency detections from results
            detections = []
            for result in results:
                if 'frequency_detection' in result and result['frequency_detection']:
                    detections.append({
                        'file_id': result['file_id'],
                        'target_freq': result['frequency_detection'].get('target_mhz', target_freq_mhz or ref_freq_mhz),
                        'offset_hz': result['frequency_detection'].get('offset_hz', 0),
                        'power_db': result['frequency_detection'].get('power_db', 0)
                    })
            
            if len(detections) < 2:
                logger.warning("⚠️ Less than 2 receivers with valid detections")
                return {
                    'status': 'incomplete',
                    'detections': detections,
                    'message': 'Insufficient data for accurate TDOA'
                }
            
            # Simple TDOA calculation (mock - replace with real algorithm)
            # In production, use actual TDOA hyperbolic positioning
            
            # Calculate average frequency
            avg_freq = np.mean([d['target_freq'] for d in detections])
            
            # Calculate position (mock - use real TDOA algorithm)
            # This is a simplified calculation for demo purposes
            lat = 0.0
            lon = 0.0
            accuracy_meters = 100.0
            
            # Save localization result
            localization_result = {
                'timestamp': datetime.now().isoformat(),
                'target_frequency_mhz': avg_freq,
                'reference_frequency_mhz': ref_freq_mhz,
                'num_receivers': len(detections),
                'detections': detections,
                'location': {
                    'latitude': lat,
                    'longitude': lon,
                    'accuracy_meters': accuracy_meters,
                    'altitude_meters': 0,
                    'units': 'decimal degrees'
                }
            }
            
            logger.info(f"✓ TDOA calculation completed")
            logger.info(f"  Location: ({lat:.4f}, {lon:.4f})")
            logger.info(f"  Accuracy: ±{accuracy_meters:.1f}m")
            
            return localization_result
            
        except Exception as e:
            logger.error(f"❌ Error in TDOA calculation: {str(e)}", exc_info=True)
            return {'error': str(e)}

    def get_imported_files(self):
        """Get list of imported files"""
        return [{
            'file_id': file_id,
            'filename': iq_file.filename,
            'filesize': iq_file.filesize,
            'loaded': iq_file.loaded,
            'num_samples': len(iq_file.data) if iq_file.loaded else 0
        } for file_id, iq_file in self.files.items()]
    
    def delete_file(self, file_id):
        """Delete an imported file"""
        if file_id in self.files:
            del self.files[file_id]
            logger.info(f"✓ File deleted: {file_id}")
            return {'status': 'deleted'}
        return {'error': 'File not found'}