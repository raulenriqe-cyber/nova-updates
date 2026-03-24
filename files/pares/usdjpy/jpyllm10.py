#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ✨ NOVA TRADING AI - LLM10 (EU VERSION)                   ║
║                    Market State Auditor for USDJPY M15                       ║
║                                                                              ║
║  LLM10 NOVA (USDJPY): Audita TODOS los huecos del sistema en tiempo real     ║
║  - 7 categorías de detección (Liquidity, Divergence, Macros, Volume, etc)    ║
║  - 47+ huecos específicos documentados en análisis profundo                   ║
║  - Quality score (0-100) + multiplier (0.5x-1.2x)                            ║
║  - Deterministic analysis + statistical scoring                              ║
║                                                                              ║
║  USDJPY SPECIFIC CONFIG:                                                     ║
║  - Spread threshold: 0.0005 pips (vs 0.5 for XAUUSD)                         ║
║  - Micro pip spread handling                                                 ║
║  - Session overlap logic (London-NY)                                         ║
║  - Currency pair dynamics                                                    ║
║                                                                              ║
║  Author: Polar Trading Systems by Polaricelabs © 2026                        ║
║  Port: 7865 | Edition: Missing Information Engine | Production               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import socket, struct, json, logging, threading, time, sys
import numpy as np
from collections import deque
from datetime import datetime
import signal

# ═══════════════════════════════════════════════════════════════════════════════
# LOGGING CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | 🧠 LLM10-NOVA (EU) | %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# LLM10: MARKET STATE AUDITOR (NOVA) - USDJPY VERSION
# ═══════════════════════════════════════════════════════════════════════════════

class LLM10_NOVA_EU:
    """
    🧠 Market State Detection Agent - LLM10 USDJPY Edition
    
    Audita TODOS los huecos en el análisis de mercado para USDJPY.
    Configuración específica para pares de divisas con spreads micro.
    
    REQUERIMIENTOS ENTRADA:
    - genome: Datos completos del mercado (jpyquantum_core format)
    
    RESPONDE CON:
    - quality_score: 0-100 (quality of market information)
    - quality_multiplier: 0.5x-1.2x (for Trinity confidence adjustment)
    - alerts: List of detected information gaps
    - categories: Breakdown by audit category
    - market_state: Contextual market analysis
    """
    
    def __init__(self, port=7865, symbol='USDJPY'):
        self.port = port
        self.symbol = symbol
        self.running = True
        self.history = deque(maxlen=500)  # Keep 500 analyses
        
        # Configuration for USDJPY (currency pair specific)
        self.spread_threshold_wide = 0.0005  # 5 pips is wide for USDJPY
        self.spread_threshold_frozen = 0.0  # Frozen detection
        self.micro_threshold = 0.00005  # Micro-pip precision
        
        log.info(f"═══════════════════════════════════════════════════════════════")
        log.info(f"[LLM10-NOVA-EU] 🧠 Market State Auditor initialized (USDJPY)")
        log.info(f"[LLM10-NOVA-EU] Symbol: {symbol} | Port: {port}")
        log.info(f"[LLM10-NOVA-EU] Configuration: Currency pair (micro spreads)")
        log.info(f"[LLM10-NOVA-EU] 7 Audit Categories: Liquidity, Divergence, Macros,")
        log.info(f"[LLM10-NOVA-EU]                    Volume, Momentum, Session, Saturation")
        log.info(f"═══════════════════════════════════════════════════════════════")
        
        # Setup Ctrl+C handler
        signal.signal(signal.SIGINT, self._handle_shutdown)
    
    def _handle_shutdown(self, signum, frame):
        """Graceful shutdown"""
        log.info("[LLM10-NOVA-EU] Shutting down gracefully...")
        self.running = False
        sys.exit(0)
    
    def analyze_market_state(self, genome: dict) -> dict:
        """
        Core analysis function: Audit all gaps in market information for USDJPY
        
        Returns comprehensive market state assessment with:
        - Quality metrics
        - Missing information alerts
        - Contextual adjustments
        - Severity scoring
        """
        analysis_time = time.time()
        alerts = []
        quality_score = 100.0
        categories = {}
        market_state = {}
        
        # ═══════════════════════════════════════════════════════════════════
        # EXTRACT GENOME DATA
        # ═══════════════════════════════════════════════════════════════════
        tick_data = genome.get('tick_data', {})
        indicators = genome.get('indicators', {}).get('current', {})
        velocity = genome.get('velocity', {})
        sl_history = genome.get('sl_history', [])
        timeframe_analysis = genome.get('timeframe_analysis', [])
        bar_data = genome.get('bar_data', {})
        metadata = genome.get('metadata', {})
        
        # ═══════════════════════════════════════════════════════════════════
        # CATEGORY 1: LIQUIDITY AUDIT (Currency-specific)
        # ═══════════════════════════════════════════════════════════════════
        liquidity_score, liquidity_alerts = self._audit_liquidity_eu(
            tick_data, bar_data, indicators
        )
        categories['liquidity'] = liquidity_score
        alerts.extend(liquidity_alerts)
        quality_score -= (100 - liquidity_score) * 0.18  # 18% weight
        
        # ═══════════════════════════════════════════════════════════════════
        # CATEGORY 2: STRUCTURAL DIVERGENCES
        # ═══════════════════════════════════════════════════════════════════
        divergence_score, divergence_alerts = self._audit_divergences(
            timeframe_analysis, indicators, tick_data
        )
        categories['divergence'] = divergence_score
        alerts.extend(divergence_alerts)
        quality_score -= (100 - divergence_score) * 0.16  # 16% weight
        
        # ═══════════════════════════════════════════════════════════════════
        # CATEGORY 3: MACRO CONTEXT (Includes EUR-specific macro)
        # ═══════════════════════════════════════════════════════════════════
        macro_score, macro_alerts = self._audit_macro_context_eu(
            indicators, tick_data, metadata
        )
        categories['macro'] = macro_score
        alerts.extend(macro_alerts)
        quality_score -= (100 - macro_score) * 0.14  # 14% weight
        
        # ═══════════════════════════════════════════════════════════════════
        # CATEGORY 4: VOLUME & MICROSTRUCTURE
        # ═══════════════════════════════════════════════════════════════════
        volume_score, volume_alerts = self._audit_volume(
            bar_data, tick_data, indicators
        )
        categories['volume'] = volume_score
        alerts.extend(volume_alerts)
        quality_score -= (100 - volume_score) * 0.15  # 15% weight
        
        # ═══════════════════════════════════════════════════════════════════
        # CATEGORY 5: MOMENTUM & VELOCITY
        # ═══════════════════════════════════════════════════════════════════
        momentum_score, momentum_alerts = self._audit_momentum(
            velocity, indicators, bar_data
        )
        categories['momentum'] = momentum_score
        alerts.extend(momentum_alerts)
        quality_score -= (100 - momentum_score) * 0.17  # 17% weight
        
        # ═══════════════════════════════════════════════════════════════════
        # CATEGORY 6: SESSION & TEMPORAL CONTEXT (London-NY overlap focus)
        # ═══════════════════════════════════════════════════════════════════
        session_score, session_alerts = self._audit_session_eu(
            metadata, sl_history
        )
        categories['session'] = session_score
        alerts.extend(session_alerts)
        quality_score -= (100 - session_score) * 0.10  # 10% weight
        
        # ═══════════════════════════════════════════════════════════════════
        # CATEGORY 7: INDICATOR SATURATION & EXHAUSTION
        # ═══════════════════════════════════════════════════════════════════
        saturation_score, saturation_alerts = self._audit_saturation(
            indicators, velocity
        )
        categories['saturation'] = saturation_score
        alerts.extend(saturation_alerts)
        quality_score -= (100 - saturation_score) * 0.10  # 10% weight
        
        # ═══════════════════════════════════════════════════════════════════
        # CALCULATE QUALITY MULTIPLIER
        # ═══════════════════════════════════════════════════════════════════
        quality_score = max(0, min(100, quality_score))
        quality_multiplier = self._score_to_multiplier(quality_score)
        
        # ═══════════════════════════════════════════════════════════════════
        # DETERMINE MARKET STATE CONTEXT
        # ═══════════════════════════════════════════════════════════════════
        market_state = self._analyze_market_context(
            quality_score, indicators, tick_data, timeframe_analysis
        )
        
        # Build response
        latency = (time.time() - analysis_time) * 1000
        
        response = {
            'quality_score': round(quality_score, 1),
            'quality_multiplier': round(quality_multiplier, 3),
            'alerts': alerts[:10],  # Top 10 alerts
            'alert_count': len(alerts),
            'categories': {k: round(v, 1) for k, v in categories.items()},
            'market_state': market_state,
            'latency_ms': round(latency, 1),
            'timestamp': datetime.now().isoformat(),
        }
        
        # Store in history
        self.history.append(response)
        
        return response
    
    # ═══════════════════════════════════════════════════════════════════════
    # AUDIT METHODS (One per category) - EU-SPECIFIC VERSIONS
    # ═══════════════════════════════════════════════════════════════════════
    
    def _audit_liquidity_eu(self, tick_data, bar_data, indicators):
        """Audit liquidity for USDJPY: micro spreads, currency pair dynamics"""
        score = 100.0
        alerts = []
        
        bid = float(tick_data.get('bid', 0))
        ask = float(tick_data.get('ask', 0))
        spread = abs(ask - bid) if bid > 0 and ask > 0 else 0
        tick_volume = float(tick_data.get('volume', 0))
        
        # Convert to pips for readability (4 decimal places for USDJPY)
        spread_pips = spread * 10000 if spread > 0 else 0
        
        # Frozen market
        if bid == ask and spread == 0:
            alerts.append("🚫 FROZEN_MARKET: bid==ask, market closed or no data")
            score -= 45
        
        # Wide spread for USDJPY (>0.0005 = >5 pips)
        elif spread > self.spread_threshold_wide:
            alerts.append(f"⚠️ LIQUIDITY_CRISIS: spread={spread_pips:.1f}pips (too wide for EU)")
            score -= 30
        
        # No volume
        if tick_volume == 0:
            alerts.append("⚠️ ZERO_VOLUME: tick_volume=0, no trading activity")
            score -= 20
        
        # Volume drying up
        bar_volumes = bar_data.get('volumes', [])
        if bar_volumes and len(bar_volumes) >= 3:
            recent_avg = np.mean(bar_volumes[-3:])
            if recent_avg > 0 and tick_volume < recent_avg * 0.1:
                alerts.append(f"⚠️ VOLUME_DRAIN: {tick_volume:.0f} vs avg {recent_avg:.0f}")
                score -= 15
        
        return score, alerts
    
    def _audit_divergences(self, timeframe_analysis, indicators, tick_data):
        """Audit structural divergences: TF conflicts, price-volume mismatches"""
        score = 100.0
        alerts = []
        
        # Timeframe conflicts
        if timeframe_analysis:
            tf_signals = {}
            for tf in timeframe_analysis:
                signal = tf.get('signal', 'HOLD')
                tf_signals[signal] = tf_signals.get(signal, 0) + 1
            
            if 'BUY' in tf_signals and 'SELL' in tf_signals:
                buy_count = tf_signals['BUY']
                sell_count = tf_signals['SELL']
                alerts.append(f"⚠️ TIMEFRAME_CONFLICT: {buy_count} BUY vs {sell_count} SELL")
                score -= 25
        
        # Price-volume divergence
        rsi = float(indicators.get('rsi', 50))
        adx = float(indicators.get('adx', 20))
        
        if (rsi > 80 or rsi < 20) and adx < 15:
            alerts.append(f"⚠️ PRICE_VOLUME_DIVERGENCE: RSI={rsi:.0f} extreme but ADX={adx:.0f} weak")
            score -= 20
        
        # Bid-Ask imbalance
        bid = float(tick_data.get('bid', 0))
        ask = float(tick_data.get('ask', 0))
        mid = (bid + ask) / 2 if bid > 0 and ask > 0 else 0
        
        if mid > 0:
            bid_distance = (mid - bid) / mid * 10000  # In pips
            ask_distance = (ask - mid) / mid * 10000
            if bid_distance != ask_distance:
                imbalance = abs(bid_distance - ask_distance)
                if imbalance > 5:  # >5 pips imbalance
                    alerts.append(f"⚠️ BID_ASK_IMBALANCE: {imbalance:.0f} pips skew")
                    score -= 12
        
        return score, alerts
    
    def _audit_macro_context_eu(self, indicators, tick_data, metadata):
        """Audit macro: EUR-specific indicators, ECB effects, USD correlation"""
        score = 100.0
        alerts = []
        
        # Indicator alignment
        price = float(tick_data.get('bid', 0) + tick_data.get('ask', 0)) / 2
        ma_fast = float(indicators.get('ma_fast', 0))
        ma_slow = float(indicators.get('ma_slow', 0))
        macd = float(indicators.get('macd', 0))
        
        agreement_count = 0
        if price > ma_fast > ma_slow:
            agreement_count += 1
        elif price < ma_fast < ma_slow:
            agreement_count += 1
        
        if (ma_fast > ma_slow and macd > 0) or (ma_fast < ma_slow and macd < 0):
            agreement_count += 1
        
        if agreement_count < 2:
            alerts.append(f"⚠️ WEAK_MACRO_CONTEXT: Only {agreement_count}/3 indicators aligned")
            score -= 18
        
        # Bollinger Band position
        bb_upper = float(indicators.get('bb_upper', 0))
        bb_lower = float(indicators.get('bb_lower', 0))
        
        if price > 0 and bb_upper > 0 and bb_lower > 0:
            bb_position = (price - bb_lower) / (bb_upper - bb_lower)
            if bb_position < 0.1 or bb_position > 0.9:
                alert_text = "OVERBOUGHT" if bb_position > 0.9 else "OVERSOLD"
                alerts.append(f"⚠️ BB_{alert_text}: {bb_position:.1%} position")
                score -= 10
        
        # EUR-specific macro context
        session = metadata.get('session', 'UNKNOWN')
        if session == 'LONDON_NY_OVERLAP':
            # High volatility expected, adjust score slightly down
            alerts.append("ℹ️ LONDON_NY_OVERLAP: High volatility expected")
            score -= 2
        
        return score, alerts
    
    def _audit_volume(self, bar_data, tick_data, indicators):
        """Audit volume: spikes, drains, microstructure anomalies"""
        score = 100.0
        alerts = []
        
        # Volume spike
        bar_volumes = bar_data.get('volumes', [])
        if bar_volumes and len(bar_volumes) >= 5:
            recent_vol = bar_volumes[-1]
            avg_vol = np.mean(bar_volumes[-5:])
            
            if recent_vol > avg_vol * 3:
                alerts.append(f"⚠️ VOLUME_SPIKE: {recent_vol:.0f} vs avg {avg_vol:.0f} (3x)")
                score -= 12
            elif recent_vol < avg_vol * 0.2:
                alerts.append(f"⚠️ VOLUME_DRAIN: {recent_vol:.0f} vs avg {avg_vol:.0f} (<20%)")
                score -= 15
        
        # Volume vs price move
        adx = float(indicators.get('adx', 20))
        tick_volume = float(tick_data.get('volume', 0))
        
        if adx > 30 and tick_volume < 50:
            alerts.append(f"⚠️ LOW_VOLUME_HIGH_TREND: ADX={adx:.0f} but vol={tick_volume:.0f}")
            score -= 10
        
        return score, alerts
    
    def _audit_momentum(self, velocity, indicators, bar_data):
        """Audit momentum: velocity fade, exhaustion, reversals"""
        score = 100.0
        alerts = []
        
        # Velocity fade
        rsi = float(indicators.get('rsi', 50))
        adx = float(indicators.get('adx', 20))
        rsi_delta = float(velocity.get('rsi_delta', 0))
        adx_delta = float(velocity.get('adx_delta', 0))
        
        if adx > 25 and abs(adx_delta) < 0.3:
            alerts.append(f"⚠️ MOMENTUM_FADE: ADX={adx:.0f} strong but delta={adx_delta:+.2f} weak")
            score -= 20
        
        # RSI extreme velocity (exhaustion)
        if abs(rsi_delta) > 4:
            alert_type = "OVERBOUGHT" if rsi_delta > 4 else "OVERSOLD"
            alerts.append(f"⚠️ RSI_EXHAUSTION: delta={rsi_delta:+.1f} ({alert_type})")
            score -= 15
        
        # Reversal signs
        closes = bar_data.get('closes', [])
        if closes and len(closes) >= 3:
            recent_closes = [float(c) for c in closes[-3:] if c]
            if len(recent_closes) == 3:
                if recent_closes[0] > recent_closes[1] < recent_closes[2]:
                    alerts.append("⚠️ REVERSAL_PATTERN: V-shape detected (oversold bounce)")
                    score -= 10
                elif recent_closes[0] < recent_closes[1] > recent_closes[2]:
                    alerts.append("⚠️ REVERSAL_PATTERN: ^-shape detected (overbought decline)")
                    score -= 10
        
        return score, alerts
    
    def _audit_session_eu(self, metadata, sl_history):
        """Audit session for USDJPY: London-NY overlap, session effects"""
        score = 100.0
        alerts = []
        
        # Session unknown
        session = metadata.get('session', 'UNKNOWN')
        if session == 'UNKNOWN' or not session:
            alerts.append("ℹ️ SESSION_UNKNOWN: Cannot determine market session")
            score -= 8
        
        # Limited SL history
        if not sl_history or len(sl_history) < 2:
            alerts.append(f"ℹ️ LIMITED_SL_HISTORY: Only {len(sl_history) if sl_history else 0} events")
            score -= 5
        
        # Check for overlap times (USDJPY specific: London-NY)
        hour = datetime.now().hour
        if 12 <= hour <= 16:  # London-NY overlap (1200-1600 UTC)
            alerts.append("ℹ️ LONDON_NY_OVERLAP: High volatility window (1200-1600 UTC)")
            score -= 5
        elif 8 <= hour <= 12:  # London open
            alerts.append("ℹ️ LONDON_SESSION: Moderate volatility expected")
            score -= 2
        
        return score, alerts
    
    def _audit_saturation(self, indicators, velocity):
        """Audit saturation: RSI/MACD extremes, indicator exhaustion"""
        score = 100.0
        alerts = []
        
        # RSI saturation
        rsi = float(indicators.get('rsi', 50))
        if rsi > 85:
            alerts.append(f"⚠️ RSI_OVERBOUGHT: {rsi:.0f} (reversal risk)")
            score -= 12
        elif rsi < 15:
            alerts.append(f"⚠️ RSI_OVERSOLD: {rsi:.0f} (reversal risk)")
            score -= 12
        
        # MACD saturation
        macd_hist = float(indicators.get('macd_histogram', 0))
        if abs(macd_hist) > 0.8:
            alert_type = "OVERBOUGHT" if macd_hist > 0.8 else "OVERSOLD"
            alerts.append(f"⚠️ MACD_SATURATION: hist={macd_hist:+.3f} ({alert_type})")
            score -= 10
        
        # ADX saturation
        adx = float(indicators.get('adx', 20))
        if adx > 50:
            alerts.append(f"⚠️ ADX_EXTREME: {adx:.0f} (trend may reverse)")
            score -= 8
        
        return score, alerts
    
    def _score_to_multiplier(self, quality_score):
        """Convert quality_score (0-100) to multiplier (0.5x-1.2x)"""
        if quality_score < 20:
            return 0.50
        elif quality_score < 35:
            return 0.50 + (quality_score - 20) / 15 * 0.10
        elif quality_score < 50:
            return 0.60 + (quality_score - 35) / 15 * 0.20
        elif quality_score < 70:
            return 0.80 + (quality_score - 50) / 20 * 0.20
        elif quality_score < 85:
            return 1.00 + (quality_score - 70) / 15 * 0.10
        elif quality_score < 95:
            return 1.10 + (quality_score - 85) / 10 * 0.05
        else:
            return 1.15 + (quality_score - 95) / 5 * 0.05
    
    def _analyze_market_context(self, quality_score, indicators, tick_data, timeframe_analysis):
        """Analyze broader market context for contextual adjustments"""
        rsi = float(indicators.get('rsi', 50))
        adx = float(indicators.get('adx', 20))
        macd = float(indicators.get('macd', 0))
        
        context = {}
        
        # Trend strength
        if adx > 40:
            context['trend'] = 'STRONG'
        elif adx > 25:
            context['trend'] = 'MODERATE'
        else:
            context['trend'] = 'WEAK'
        
        # Price action
        if rsi > 70:
            context['momentum'] = 'OVERBOUGHT'
        elif rsi < 30:
            context['momentum'] = 'OVERSOLD'
        elif rsi > 60:
            context['momentum'] = 'BULLISH'
        elif rsi < 40:
            context['momentum'] = 'BEARISH'
        else:
            context['momentum'] = 'NEUTRAL'
        
        # MACD signal
        if macd > 0:
            context['macd_bias'] = 'BULLISH'
        else:
            context['macd_bias'] = 'BEARISH'
        
        # Timeframe alignment
        if timeframe_analysis:
            tf_signals = [tf.get('signal') for tf in timeframe_analysis]
            buy_count = tf_signals.count('BUY')
            sell_count = tf_signals.count('SELL')
            if buy_count > sell_count:
                context['tf_alignment'] = 'BULLISH'
            elif sell_count > buy_count:
                context['tf_alignment'] = 'BEARISH'
            else:
                context['tf_alignment'] = 'MIXED'
        
        return context
    
    def handle_request(self, data: bytes) -> bytes:
        """Handle incoming request and return response"""
        try:
            genome = json.loads(data.decode('utf-8'))
            analysis = self.analyze_market_state(genome)
            return json.dumps(analysis).encode('utf-8')
        except Exception as e:
            log.error(f"[LLM10-NOVA-EU] Error processing request: {e}")
            return json.dumps({
                'quality_score': 50,
                'quality_multiplier': 1.0,
                'alerts': [f'ERROR: {str(e)}'],
                'error': str(e)
            }).encode('utf-8')
    
    def start_server(self):
        """Start TCP server"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind(('127.0.0.1', self.port))
            server_socket.listen(5)
            log.info(f"[LLM10-NOVA-EU] 🟢 Server listening on port {self.port}")
            
            while self.running:
                try:
                    client_socket, addr = server_socket.accept()
                    thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, addr),
                        daemon=True
                    )
                    thread.start()
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    log.error(f"[LLM10-NOVA-EU] Error accepting connection: {e}")
        finally:
            server_socket.close()
            log.info("[LLM10-NOVA-EU] Server shutdown complete")
    
    def _handle_client(self, client_socket, addr):
        """Handle individual client connection"""
        try:
            # Receive length header (4 bytes)
            len_header = client_socket.recv(4)
            if len(len_header) < 4:
                return
            
            msg_len = struct.unpack('>I', len_header)[0]
            if msg_len > 10_000_000:  # Max 10MB
                return
            
            # Receive data
            data = b''
            while len(data) < msg_len:
                chunk = client_socket.recv(min(8192, msg_len - len(data)))
                if not chunk:
                    break
                data += chunk
            
            # Process and respond
            response = self.handle_request(data)
            
            # Send response with length header
            response_header = struct.pack('>I', len(response))
            client_socket.sendall(response_header + response)
            
        except Exception as e:
            log.error(f"[LLM10-NOVA-EU] Error handling client: {e}")
        finally:
            client_socket.close()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN: Start LLM10 Server (USDJPY Version)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import sys
    
    # Determine symbol and port from command line
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
        symbol = 'XAUUSD' if port == 5565 else 'USDJPY'
    else:
        port = 7865
        symbol = 'USDJPY'
    
    # Start server
    nova_server = LLM10_NOVA_EU(port=port, symbol=symbol)
    nova_server.start_server()
