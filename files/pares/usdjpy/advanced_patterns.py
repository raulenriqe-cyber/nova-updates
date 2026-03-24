#!/usr/bin/env python3
"""
QUANTUM CORE - ADVANCED PATTERN RECOGNITION ENGINE v1.0
Detects harmonic patterns (Gartley, Butterfly, Crab, Bat)
Williams fractals, Head & Shoulders, y más
"""

import logging
import numpy as np
from collections import deque

log = logging.getLogger("AdvancedPatterns")

class HarmonicPatternDetector:
    """Detects harmonic patterns: Gartley, Butterfly, Crab, Bat"""
    
    # Fibonacci ratios (tolerancia ±5%)
    RATIOS = {
        'fib_0.382': (0.382, 0.05),
        'fib_0.618': (0.618, 0.05),
        'fib_1.000': (1.000, 0.05),
        'fib_1.272': (1.272, 0.05),
        'fib_1.618': (1.618, 0.05),
        'fib_2.618': (2.618, 0.05),
    }
    
    def __init__(self):
        self.patterns_found = deque(maxlen=50)
    
    def detect_gartley(self, prices):
        """
        Gartley pattern: X -> A -> B -> C -> D
        A = 0.618 * XA
        B = 0.382-0.886 * XA  
        C = 1.13-1.618 * AB
        D = 0.786 * XC (completion)
        """
        if len(prices) < 5:
            return None
        
        # Últimos 5 puntos (X, A, B, C, D)
        x, a, b, c, d = prices[-5:]
        
        xa = abs(a - x)
        ab = abs(b - a)
        bc = abs(c - b)
        cd = abs(d - c)
        xc = abs(c - x)
        
        # Check ratios
        checks = [
            self._check_ratio(ab, xa, 0.618, 0.05),  # A = 0.618
            self._check_ratio(bc, xa, 1.618, 0.05),  # C leg
            self._check_ratio(cd, xc, 0.786, 0.05),  # D completion
        ]
        
        if all(checks):
            pattern = {
                'type': 'GARTLEY',
                'points': [x, a, b, c, d],
                'entry': d,
                'take_profit': d + (d - c) * 1.618,
                'stop_loss': d - (d - c) * 1.272,
                'reliability': 0.85,
            }
            self.patterns_found.append(pattern)
            return pattern
        
        return None
    
    def detect_butterfly(self, prices):
        """
        Butterfly pattern (raro, muy confiable)
        B = 0.382-0.886 de XA
        D = 1.27 * XA (extension completa)
        """
        if len(prices) < 5:
            return None
        
        x, a, b, c, d = prices[-5:]
        
        xa = abs(a - x)
        xd = abs(d - x)
        
        if self._check_ratio(xd, xa, 1.27, 0.03):
            pattern = {
                'type': 'BUTTERFLY',
                'points': [x, a, b, c, d],
                'entry': d,
                'take_profit': d + (d - x) * 0.618,
                'stop_loss': d - (d - x) * 1.618,
                'reliability': 0.90,
            }
            self.patterns_found.append(pattern)
            return pattern
        
        return None
    
    def detect_crab(self, prices):
        """
        Crab pattern (extremadamente raro, extremadamente confiable)
        D = 1.618 * XA (extension muy lejos)
        """
        if len(prices) < 5:
            return None
        
        x, a, b, c, d = prices[-5:]
        
        xa = abs(a - x)
        xd = abs(d - x)
        
        if self._check_ratio(xd, xa, 1.618, 0.02):
            pattern = {
                'type': 'CRAB',
                'points': [x, a, b, c, d],
                'entry': d,
                'take_profit': d + (d - x) * 0.382,
                'stop_loss': d - (d - x) * 1.272,
                'reliability': 0.95,
            }
            self.patterns_found.append(pattern)
            return pattern
        
        return None
    
    def detect_bat(self, prices):
        """
        Bat pattern (más común que Crab, muy confiable)
        B = 0.50 de XA
        D = 0.886 * XA
        """
        if len(prices) < 5:
            return None
        
        x, a, b, c, d = prices[-5:]
        
        xa = abs(a - x)
        ab = abs(b - a)
        xd = abs(d - x)
        
        if (self._check_ratio(ab, xa, 0.50, 0.05) and 
            self._check_ratio(xd, xa, 0.886, 0.03)):
            pattern = {
                'type': 'BAT',
                'points': [x, a, b, c, d],
                'entry': d,
                'take_profit': d + (d - x) * 0.618,
                'stop_loss': d - (d - x) * 1.618,
                'reliability': 0.88,
            }
            self.patterns_found.append(pattern)
            return pattern
        
        return None
    
    def _check_ratio(self, value, reference, expected_ratio, tolerance):
        """Verifica si ratio está dentro de tolerancia"""
        if reference == 0:
            return False
        ratio = value / reference
        return abs(ratio - expected_ratio) <= tolerance
    
    def detect_all_harmonics(self, prices):
        """Detecta todos los patrones armónicos"""
        patterns = []
        
        if pattern := self.detect_gartley(prices):
            patterns.append(pattern)
        if pattern := self.detect_butterfly(prices):
            patterns.append(pattern)
        if pattern := self.detect_crab(prices):
            patterns.append(pattern)
        if pattern := self.detect_bat(prices):
            patterns.append(pattern)
        
        return patterns


class FractalPatternDetector:
    """Detects Williams fractals and fractal breakouts"""
    
    def __init__(self, lookback=5):
        self.lookback = lookback
        self.fractals = deque(maxlen=100)
    
    def detect_fractal(self, highs, lows):
        """
        Williams Fractal:
        - High fractal: 2 bars with lower highs on both sides
        - Low fractal: 2 bars with higher lows on both sides
        """
        if len(highs) < self.lookback or len(lows) < self.lookback:
            return None
        
        mid = self.lookback // 2
        
        # Check high fractal (5 bars: [h1 < h2 > h3 < h4 < h5])
        is_high_fractal = (
            highs[-5] < highs[-4] and
            highs[-4] > highs[-3] and
            highs[-3] < highs[-2] and
            highs[-2] < highs[-1]
        )
        
        # Check low fractal
        is_low_fractal = (
            lows[-5] > lows[-4] and
            lows[-4] < lows[-3] and
            lows[-3] > lows[-2] and
            lows[-2] > lows[-1]
        )
        
        result = None
        if is_high_fractal:
            result = {'type': 'HIGH_FRACTAL', 'price': highs[-3], 'bar_idx': -3}
        elif is_low_fractal:
            result = {'type': 'LOW_FRACTAL', 'price': lows[-3], 'bar_idx': -3}
        
        if result:
            self.fractals.append(result)
        
        return result


class HeadAndShouldersDetector:
    """Detects Head & Shoulders (H&S) patterns"""
    
    def detect_hns_top(self, highs, lows):
        """
        H&S Top: Left Shoulder > Head > Right Shoulder
        Neckline: conecta los lows entre hombros
        """
        if len(highs) < 7:
            return None
        
        # Últimos 7 bars
        h = highs[-7:]
        l = lows[-7:]
        
        # Pattern: peak1 - valley1 - peak2 - valley2 - peak3
        peak1 = h[0]
        valley1 = l[1]
        peak2 = h[2]  # Should be > peak1 (head)
        valley2 = l[3]
        peak3 = h[4]  # Should be < peak1 (right shoulder)
        
        if peak2 > peak1 and peak3 < peak1 and valley1 > valley2:
            # Calcular neckline
            neckline = max(valley1, valley2)
            
            pattern = {
                'type': 'HEAD_AND_SHOULDERS_TOP',
                'left_shoulder': peak1,
                'head': peak2,
                'right_shoulder': peak3,
                'neckline': neckline,
                'entry': neckline,
                'target': peak2 - (peak2 - neckline),  # Projection down
                'stop_loss': peak3,
                'reliability': 0.80,
            }
            return pattern
        
        return None
    
    def detect_hns_bottom(self, highs, lows):
        """H&S Bottom (Inverse): Left Shoulder < Head < Right Shoulder"""
        if len(highs) < 7:
            return None
        
        h = highs[-7:]
        l = lows[-7:]
        
        # Pattern: valley1 - peak1 - valley2 - peak2 - valley3
        valley1 = l[0]
        peak1 = h[1]
        valley2 = l[2]  # Should be < valley1 (head)
        peak2 = h[3]
        valley3 = l[4]  # Should be > valley1
        
        if valley2 < valley1 and valley3 > valley1 and peak1 < peak2:
            neckline = min(peak1, peak2)
            
            pattern = {
                'type': 'HEAD_AND_SHOULDERS_BOTTOM',
                'left_shoulder': valley1,
                'head': valley2,
                'right_shoulder': valley3,
                'neckline': neckline,
                'entry': neckline,
                'target': valley2 + (neckline - valley2),  # Projection up
                'stop_loss': valley2,
                'reliability': 0.80,
            }
            return pattern
        
        return None


class AdvancedPatternEngine:
    """Central engine para toda pattern recognition"""
    
    def __init__(self):
        self.harmonics = HarmonicPatternDetector()
        self.fractals = FractalPatternDetector()
        self.h_and_s = HeadAndShouldersDetector()
        
        self.all_patterns = deque(maxlen=100)
    
    def analyze_patterns(self, closes, highs, lows):
        """Analiza todos los patrones en las últimas velas"""
        patterns = []
        
        # Harmonic patterns (últimos 5 prices)
        if len(closes) >= 5:
            harmonic_patterns = self.harmonics.detect_all_harmonics(closes[-5:])
            patterns.extend(harmonic_patterns)
        
        # Fractals
        if len(highs) >= 5 and len(lows) >= 5:
            fractal = self.fractals.detect_fractal(highs[-5:], lows[-5:])
            if fractal:
                patterns.append(fractal)
        
        # Head & Shoulders
        if len(highs) >= 7 and len(lows) >= 7:
            hns_top = self.h_and_s.detect_hns_top(highs[-7:], lows[-7:])
            hns_bottom = self.h_and_s.detect_hns_bottom(highs[-7:], lows[-7:])
            if hns_top:
                patterns.append(hns_top)
            if hns_bottom:
                patterns.append(hns_bottom)
        
        # Store all patterns
        for pattern in patterns:
            self.all_patterns.append(pattern)
        
        return patterns
    
    def get_high_reliability_patterns(self, min_reliability=0.85):
        """Retorna solo patrones con alta confiabilidad"""
        return [p for p in self.all_patterns 
                if p.get('reliability', 0) >= min_reliability]
    
    def get_pattern_statistics(self):
        """Retorna estadísticas de patrones detectados"""
        if not self.all_patterns:
            return {'total': 0, 'by_type': {}}
        
        by_type = {}
        for pattern in self.all_patterns:
            ptype = pattern.get('type', 'UNKNOWN')
            by_type[ptype] = by_type.get(ptype, 0) + 1
        
        return {
            'total': len(self.all_patterns),
            'by_type': by_type,
            'avg_reliability': np.mean([p.get('reliability', 0.5) 
                                       for p in self.all_patterns]),
        }


# Export
__all__ = [
    'HarmonicPatternDetector',
    'FractalPatternDetector', 
    'HeadAndShouldersDetector',
    'AdvancedPatternEngine'
]
