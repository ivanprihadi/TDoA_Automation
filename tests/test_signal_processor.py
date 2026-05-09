"""
Unit tests untuk SignalProcessor
"""

import unittest
import numpy as np
from backend.signal_processor import SignalProcessor


class TestSignalProcessor(unittest.TestCase):
    """Test cases untuk signal processor"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.processor = SignalProcessor()
    
    def test_iq_filter_initialization(self):
        """Test filter initialization"""
        for bandwidth in [40, 200, 400]:
            filter_coef = self.processor._get_fir_filter(bandwidth)
            self.assertIsNotNone(filter_coef)
            self.assertTrue(len(filter_coef) > 0)
    
    def test_signal_filtering(self):
        """Test signal filtering"""
        # Create test signal
        signal = np.random.randn(10000) + 1j * np.random.randn(10000)
        
        # Filter
        filtered = self.processor.filter_iq_signal(signal, 40)
        
        # Check output
        self.assertEqual(len(filtered), len(signal))
        self.assertTrue(np.all(np.isfinite(filtered)))
    
    def test_correlation_types(self):
        """Test different correlation types"""
        sig1 = np.random.randn(1000) + 1j * np.random.randn(1000)
        sig2 = np.random.randn(1000) + 1j * np.random.randn(1000)
        
        for corr_type in ['abs', 'dphase']:
            result = self.processor.correlate_iq_signals(sig1, sig2, corr_type)
            self.assertEqual(len(result), 2 * len(sig1) - 1)
    
    def test_reliability_calculation(self):
        """Test reliability calculation"""
        # Create correlation with clear peak
        correlation = np.zeros(1000)
        correlation[500] = 1.0  # Main peak
        
        reliability = self.processor.calculate_correlation_reliability(correlation)
        
        self.assertGreaterEqual(reliability, 0)
        self.assertLessEqual(reliability, 1)


if __name__ == '__main__':
    unittest.main()