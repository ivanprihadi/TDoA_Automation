# backend/signal_processor.py

"""
Signal Processing Module
Menerjemahkan semua MATLAB functions untuk Python
"""

import numpy as np
from scipy import signal as scipy_signal
from scipy.signal import butter, filtfilt, correlate, firwin, remez
from pathlib import Path
from loguru import logger
import struct

class SignalProcessor:
    """
    Core signal processor untuk TDOA analysis
    Translate MATLAB gabungan_kode.m functions
    """
    
    SAMPLING_RATE = 2_048_000  # 2 MSps dari pewaktu_new
    
    def __init__(self):
        self.fs = self.SAMPLING_RATE
        logger.info(f"✓ SignalProcessor initialized (Fs={self.fs/1e6}MHz)")
    
    # ======================== FILE I/O ========================
    
    def read_file_iq(self, filename: str) -> np.ndarray:
        """
        Read IQ data dari RTL-SDR .dat file
        Format: 8-bit unsigned interleaved I/Q samples
        
        Example:
            [128, 130, 135, 132, ...] → I=[0, 2, 7, 4, ...], Q=[2, 5, 4, ...]
        
        Returns:
            Complex IQ signal (3.6M samples dari pewaktu_new)
        """
        try:
            filepath = Path(filename)
            if not filepath.exists():
                raise FileNotFoundError(f"IQ file not found: {filename}")
            
            # Read 8-bit unsigned samples
            with open(filepath, 'rb') as f:
                data = np.fromfile(f, dtype=np.uint8)
            
            # Extract I and Q (alternating samples, subtract 128 for centering)
            inphase = data[0::2].astype(np.float32) - 128
            quadrature = data[1::2].astype(np.float32) - 128
            
            # Combine into complex signal
            iq_signal = inphase + 1j * quadrature
            
            logger.info(f"✓ Read {len(iq_signal):,} IQ samples from {filepath.name}")
            logger.debug(f"  Signal shape: {iq_signal.shape}, dtype: {iq_signal.dtype}")
            
            return iq_signal
            
        except Exception as e:
            logger.error(f"✗ Failed to read IQ file: {str(e)}")
            raise
    
    # ======================== FILTERING ========================
    
    def filter_iq(self, signal_iq: np.ndarray, bandwidth_khz: float = 0) -> np.ndarray:
        """
        Apply FIR lowpass filter ke IQ signal
        
        Parameters:
        -----------
        signal_iq : ndarray
            Complex IQ signal
        bandwidth_khz : float
            Filter bandwidth dalam kHz (0=no filter, 12, 40, 200, 400)
        
        Returns:
            Filtered complex signal
        
        Notes:
            Dari MATLAB filter_iq.m
        """
        
        if bandwidth_khz == 0:
            logger.debug("No filtering applied")
            return signal_iq
        
        try:
            # Nyquist frequency (normalized: 1.0 = Fs/2)
            nyquist = self.fs / 2
            
            # Filter coefficients based on bandwidth
            filter_params = {
                400: {
                    'Fpass': 200,    # kHz
                    'Fstop': 300,    # kHz
                    'Dpass': 0.0057563991496,
                    'Dstop': 0.001
                },
                200: {
                    'Fpass': 100,
                    'Fstop': 150,
                    'Dpass': 0.028774368332,
                    'Dstop': 0.001
                },
                40: {
                    'Fpass': 20,
                    'Fstop': 100,
                    'Dpass': 0.0057563991496,
                    'Dstop': 0.001
                },
                12: {
                    'Fpass': 6.25,
                    'Fstop': 50,
                    'Dpass': 0.028774368332,
                    'Dstop': 0.001
                }
            }
            
            if bandwidth_khz not in filter_params:
                logger.warning(f"Unknown bandwidth {bandwidth_khz}kHz, no filtering")
                return signal_iq
            
            params = filter_params[bandwidth_khz]
            
            # Design FIR filter using remez (equivalent to MATLAB firpm)
            # Normalize frequencies to Nyquist
            bands = [0, params['Fpass'], params['Fstop'], nyquist/1000]
            bands = np.array(bands) / (nyquist/1000)
            
            desired = [1, 1, 0, 0]
            weights = [1/params['Dpass'], 1/params['Dstop']]
            
            # Calculate filter order
            N = int(np.ceil(2 / (params['Fstop'] - params['Fpass']) * nyquist/1000))
            
            # Design filter
            b = remez(N, bands, desired, weight=weights)
            
            # Apply filter to real and imaginary parts separately
            filtered_real = filtfilt(b, 1, signal_iq.real)
            filtered_imag = filtfilt(b, 1, signal_iq.imag)
            
            filtered_signal = filtered_real + 1j * filtered_imag
            
            logger.info(f"✓ Filtered signal to {bandwidth_khz}kHz")
            
            return filtered_signal
            
        except Exception as e:
            logger.error(f"✗ Filtering failed: {str(e)}")
            raise
    
    # ======================== CORRELATION ========================
    
    def remove_mean(self, signal: np.ndarray) -> np.ndarray:
        """Remove DC component from signal"""
        return signal - np.mean(signal)
    
    def correlate_iq(self, 
                     iq1: np.ndarray, 
                     iq2: np.ndarray, 
                     corr_type: str = 'dphase',
                     smoothing_factor: int = 0) -> np.ndarray:
        """
        Cross-correlate two complex IQ signals
        
        Parameters:
        -----------
        iq1, iq2 : ndarray
            Complex IQ signals
        corr_type : str
            'abs' - use absolute values
            'dphase' - use differential phase (recommended)
        smoothing_factor : int
            Smoothing window size (0=no smoothing)
        
        Returns:
            Normalized correlation (0..1)
        
        Notes:
            Dari MATLAB correlate_iq.m
        """
        
        try:
            if corr_type == 'abs':
                # Use absolute values (magnitude)
                abs1 = self.remove_mean(np.abs(iq1))
                abs2 = self.remove_mean(np.abs(iq2))
                
                # Cross-correlation
                corr = correlate(abs1, abs2, mode='full')
                
                # Autocorrelations for normalization
                ref1 = np.max(correlate(abs1, abs1, mode='full'))
                ref2 = np.max(correlate(abs2, abs2, mode='full'))
                cor_max = np.max(corr)
                
                percentage = 100 * 2 * cor_max / (ref1 + ref2)
                logger.debug(f"abs cross-correlation: {cor_max:.3f}, "
                           f"autocorr: {ref1:.3f}/{ref2:.3f}, ratio: {percentage:.1f}%")
                
            elif corr_type == 'dphase':
                # Use differential phase (lebih akurat untuk sinyal band-limited)
                phase1 = np.unwrap(np.angle(iq1))
                phase2 = np.unwrap(np.angle(iq2))
                
                # Differential phase
                dphase1 = np.diff(phase1)
                dphase2 = np.diff(phase2)
                
                # Prepend zero untuk matching length
                dphase1 = np.concatenate([[0], dphase1])
                dphase2 = np.concatenate([[0], dphase2])
                
                # Remove mean
                dphase1 = self.remove_mean(dphase1)
                dphase2 = self.remove_mean(dphase2)
                
                # Cross-correlation
                corr = correlate(dphase1, dphase2, mode='full')
                
                # Autocorrelations
                ref1 = np.max(correlate(dphase1, dphase1, mode='full'))
                ref2 = np.max(correlate(dphase2, dphase2, mode='full'))
                cor_max = np.max(corr)
                
                percentage = 100 * 2 * cor_max / (ref1 + ref2)
                logger.debug(f"dphase cross-correlation: {cor_max:.3f}, "
                           f"autocorr: {ref1:.3f}/{ref2:.3f}, ratio: {percentage:.1f}%")
            else:
                raise ValueError(f"Unknown correlation type: {corr_type}")
            
            # Apply smoothing jika diperlukan
            if smoothing_factor > 0:
                corr = self._smooth(np.abs(corr), smoothing_factor)
            
            # Normalize (0..1)
            corr_normalized = corr / np.max(np.abs(corr))
            
            return corr_normalized
            
        except Exception as e:
            logger.error(f"✗ Correlation failed: {str(e)}")
            raise
    
    def _smooth(self, signal: np.ndarray, window_size: int) -> np.ndarray:
        """Simple moving average smoothing"""
        if window_size <= 1:
            return signal
        
        # Use uniform window
        window = np.ones(window_size) / window_size
        smoothed = np.convolve(signal, window, mode='same')
        return smoothed
    
    def corr_reliability(self, correlation: np.ndarray) -> float:
        """
        Calculate reliability score (0..1) of correlation
        Based on ratio between main peak and 2nd peak
        
        Returns:
            reliability = 1 - (peak2 / peak_main)
        
        Notes:
            Dari MATLAB corr_reliability.m
        """
        
        try:
            corr_max = np.max(correlation)
            idx_max = np.argmax(correlation)
            
            # Zero out main peak and decaying values
            temp = correlation.copy()
            temp[idx_max] = 0
            
            # Remove decreasing values on right side
            bin_right_old = corr_max
            for ii in range(idx_max + 1, len(temp)):
                if temp[ii] < bin_right_old:
                    bin_right_old = temp[ii]
                    temp[ii] = 0
                else:
                    break
            
            # Remove decreasing values on left side
            bin_left_old = corr_max
            for ii in range(idx_max - 1, -1, -1):
                if temp[ii] < bin_left_old:
                    bin_left_old = temp[ii]
                    temp[ii] = 0
                else:
                    break
            
            # Find 2nd peak
            peak2 = np.max(temp)
            
            # Reliability score
            reliability = 1 - (peak2 / corr_max) if corr_max > 0 else 0
            
            return np.clip(reliability, 0, 1)
            
        except Exception as e:
            logger.warning(f"Reliability calculation failed: {str(e)}")
            return 0.5  # Return neutral score on error
    
    # ======================== TDOA CALCULATION ========================
    
    def slice_signal(self, signal: np.ndarray) -> tuple:
        """
        Slice 3.6M sample signal into 3 parts:
        - Slice 1 (ref): samples 0..1M
        - Slice 2 (measure): samples 1.2M+200k..2.2M+200k
        - Slice 3 (ref check): samples 2.4M+200k..3.4M+200k
        
        Returns:
            (slice1, slice2, slice3)
        """
        
        num_samples_per_freq = int(1.2e6)
        num_samples_per_slice = int(1e6)
        guard_interval = int(200e3)
        
        slice1 = signal[0:num_samples_per_slice]
        slice2 = signal[num_samples_per_freq + guard_interval : 
                       num_samples_per_freq + guard_interval + num_samples_per_slice]
        slice3 = signal[2*num_samples_per_freq + guard_interval : 
                       2*num_samples_per_freq + guard_interval + num_samples_per_slice]
        
        return slice1, slice2, slice3
    
    def calculate_tdoa(self,
                      signal1: np.ndarray,
                      signal2: np.ndarray,
                      rx_distance_diff: float,
                      rx_distance: float,
                      smoothing_factor: int = 0,
                      corr_type: str = 'dphase',
                      signal_bandwidth_khz: float = 40,
                      ref_bandwidth_khz: float = 40) -> dict:
        """
        Calculate Time Difference of Arrival (TDOA) antara 2 RX
        
        Parameters:
        -----------
        signal1, signal2 : ndarray
            3.6M sample complex IQ signals dari 2 receiver
        rx_distance_diff : float
            Known distance difference to reference TX (meters)
        rx_distance : float
            Distance between RX1 dan RX2 (meters)
        smoothing_factor : int
            Smoothing window
        corr_type : str
            'abs' atau 'dphase'
        signal_bandwidth_khz : float
            Filter bandwidth untuk measurement
        ref_bandwidth_khz : float
            Filter bandwidth untuk reference
        
        Returns:
            dict dengan keys:
                'doa_meters': TDOA dalam meters
                'doa_samples': TDOA dalam samples
                'reliability': Correlation reliability (0..1)
        
        Notes:
            Dari MATLAB tdoa2.m
        """
        
        try:
            # Integrity checks
            if len(signal1) != 3.6e6 or len(signal2) != 3.6e6:
                raise ValueError("Signal length must be 3.6M samples")
            
            logger.info("=" * 80)
            logger.info("TDOA CALCULATION")
            logger.info("=" * 80)
            
            # Slice signals
            sig11, sig12, sig13 = self.slice_signal(signal1)
            sig21, sig22, sig23 = self.slice_signal(signal2)
            
            # Filter
            sig12_filtered = self.filter_iq(sig12, signal_bandwidth_khz)
            sig22_filtered = self.filter_iq(sig22, signal_bandwidth_khz)
            
            sig11_filtered = self.filter_iq(sig11, ref_bandwidth_khz)
            sig13_filtered = self.filter_iq(sig13, ref_bandwidth_khz)
            sig21_filtered = self.filter_iq(sig21, ref_bandwidth_khz)
            sig23_filtered = self.filter_iq(sig23, ref_bandwidth_khz)
            
            # Correlation slice 1 (reference)
            logger.info("-" * 80)
            logger.info("CORRELATION SLICE 1 (Reference)")
            corr_sig1 = self.correlate_iq(sig11_filtered, sig21_filtered, 
                                         corr_type, smoothing_factor)
            reliability1 = self.corr_reliability(corr_sig1)
            idx1 = np.argmax(corr_sig1)
            delay1 = idx1 - len(sig11_filtered)
            
            logger.info(f"  Delay: {delay1} samples, Reliability: {reliability1:.3f}")
            
            # Correlation slice 2 (measurement)
            logger.info("-" * 80)
            logger.info("CORRELATION SLICE 2 (Measurement)")
            corr_sig2 = self.correlate_iq(sig12_filtered, sig22_filtered, 
                                         corr_type, smoothing_factor)
            
            # Truncate to valid area based on RX distance
            valid_samples_right = (rx_distance - rx_distance_diff) / (3e8 / self.fs)
            valid_samples_left = (-rx_distance - rx_distance_diff) / (3e8 / self.fs)
            
            corr_sig2_valid = np.ones_like(corr_sig2) * -1
            
            # Fill valid area
            for ii in range(int(valid_samples_right) + 1 + 2):
                if idx1 + ii < len(corr_sig2):
                    corr_sig2_valid[idx1 + ii] = corr_sig2[idx1 + ii]
            
            for ii in range(int(valid_samples_left) + 1 + 2):
                if idx1 - ii >= 0:
                    corr_sig2_valid[idx1 - ii] = corr_sig2[idx1 - ii]
            
            reliability2 = self.corr_reliability(corr_sig2_valid)
            idx2 = np.argmax(corr_sig2_valid)
            delay2 = idx2 - len(sig12_filtered)
            
            logger.info(f"  Delay: {delay2} samples, Reliability: {reliability2:.3f}")
            
            # Correlation slice 3 (reference check)
            logger.info("-" * 80)
            logger.info("CORRELATION SLICE 3 (Reference Check)")
            corr_sig3 = self.correlate_iq(sig13_filtered, sig23_filtered, 
                                         corr_type, smoothing_factor)
            reliability3 = self.corr_reliability(corr_sig3)
            idx3 = np.argmax(corr_sig3)
            delay3 = idx3 - len(sig13_filtered)
            
            logger.info(f"  Delay: {delay3} samples, Reliability: {reliability3:.3f}")
            
            # Merge ref and ref check
            logger.info("-" * 80)
            if abs(delay1 - delay3) <= 2:
                avg_delay13 = (delay1 + delay3) / 2
                logger.info(f"Reference delays aligned: {delay1} vs {delay3}")
            else:
                logger.warning(f"Reference delays differ: {delay1} vs {delay3}")
                if reliability1 > reliability3:
                    avg_delay13 = delay1
                    logger.info(f"Using slice 1 (reliability: {reliability1:.3f})")
                else:
                    avg_delay13 = delay3
                    logger.info(f"Using slice 3 (reliability: {reliability3:.3f})")
            
            # Calculate final TDOA
            ref_signal_diff_samples = (rx_distance_diff / 3e8) * self.fs
            doa_samples = delay2 - avg_delay13 + ref_signal_diff_samples
            doa_meters = (doa_samples / self.fs) * 3e8
            
            # Overall reliability (minimum of all 3)
            overall_reliability = min([reliability1, reliability2, reliability3])
            
            # Log results
            logger.info("-" * 80)
            logger.info("FINAL RESULTS:")
            logger.info(f"  TDOA (samples): {doa_samples:.1f}")
            logger.info(f"  TDOA (meters): {doa_meters:.1f}")
            logger.info(f"  Reliability: {overall_reliability:.3f}")
            logger.info("=" * 80)
            
            return {
                'doa_meters': float(doa_meters),
                'doa_samples': float(doa_samples),
                'reliability': float(overall_reliability),
                'delay1': float(delay1),
                'delay2': float(delay2),
                'delay3': float(delay3),
                'reliability1': float(reliability1),
                'reliability2': float(reliability2),
                'reliability3': float(reliability3)
            }
            
        except Exception as e:
            logger.error(f"✗ TDOA calculation failed: {str(e)}", exc_info=True)
            raise