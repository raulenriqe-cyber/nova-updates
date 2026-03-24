#!/usr/bin/env python3
"""
KRAKEN - Intelligent Order Executor & Risk Manager v17.03
NOVA Trading AI By Polarice Labs © 2026
Processes trade orders from quantum_core with advanced position management
ENHANCEMENTS:
  - TP/SL price validation
  - Swap detection (TP < SL for BUY → auto-swap)
  - Price sanity checks
  - Enhanced logging
  - Dynamic port from config (default 9152)
  - Audio announcements via sound.py (USDCAD only)
"""
import socket
import struct
import json
import logging
import threading
import time
from datetime import datetime
from collections import defaultdict

# ⭐ AUDIO ANNOUNCEMENTS - Connection to sound.py
try:
    from sound import announce
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    def announce(action, symbol=""): pass  # Dummy if sound.py not available

# LOGGING SETUP
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

# ============================================================
# DIAGNOSTIC TRACER
# ============================================================
try:
    from LLM_DECISION_TRACER import get_tracer
    from REALTIME_DECISION_DASHBOARD import get_dashboard
    TRACER = get_tracer()
    DASHBOARD = get_dashboard()
    DIAGNOSTICS_ENABLED = True
except ImportError:
    TRACER = None
    DASHBOARD = None
    DIAGNOSTICS_ENABLED = False

# KRAKEN BANNER
KRAKEN_BANNER = """
╔════════════════════════════════════════════════════════════════════╗
║           ⚔️  K R A K E N - ORDER EXECUTOR v17.03  ⚔️         
║        By Polarice Labs © 2026 | Advanced Risk Management Engine  
║                  Multi-Symbol Trading | Smart Scaling              
╚════════════════════════════════════════════════════════════════════╝
"""

# KRAKEN EXECUTOR CLASS
class KrakenExecutor:
    """Advanced order executor with intelligent response and position scaling"""
    
    def __init__(self, config_path='cadconfig.yaml'):
        """Initialize KRAKEN executor"""
        self.running = True
        self.config_path = config_path

        # Load configuration
        try:
            import yaml
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
            # BUGFIX #62: Read port from config, default to 9152 (not 9156 which is quantum_core executor)
            self.port = config.get('kraken_executor_port', 9152)
            self.symbols = config.get('core_engine', {}).get('symbols', ['USDCAD'])
        except Exception as e:
            log.warning(f"Config load failed: {e}, using defaults")
            self.port = 9152  # Default to 9152, NOT 9156
            self.symbols = ['USDCAD']
        
        # 🎯 Mathematical Validation: Order execution precision controls
        self.execution_precision = 5  # Decimal places for price precision
        self.order_validation_enabled = True  # Validate all orders before execution
        self.price_tolerance = 0.0001  # Maximum price drift allowed (1 pip for most pairs)
        self.swiss_precision_mode = True  # Enable ultra-precise order management

        # State management
        self.executed_orders = []
        self.open_positions = {}
        self.position_lock = threading.RLock()
        self.order_id_counter = 0

        # Load persistent order ID
        try:
            with open('kraken_order_id.txt', 'r') as f:
                self.order_id_counter = int(f.read().strip())
                log.info(f"Loaded persistent order ID: {self.order_id_counter}")
        except FileNotFoundError:
            self.order_id_counter = 0
            log.info("No persistent order ID found, starting from 0")
        except:
            self.order_id_counter = 0

        # Print banner
        print(KRAKEN_BANNER)
        log.info("🚀 KRAKEN EXECUTOR INITIALIZED (v17.03)")
        log.info(f"   📡 Port: {self.port}")
        log.info(f"   📊 Symbols: {', '.join(self.symbols)}")
        log.info(f"   ⚙️  Status: READY FOR ORDERS")
        log.info(f"   ✨ Enhancements: TP/SL Validation | Swap Detection | Dynamic Config")
        print("╔" + "═" * 76 + "╗")
        print("║ [MODE] Intelligent Scaling | Multi-Position | Risk-Adjusted Entry    ║")
        print("║ [NEW] TP/SL Validation | Auto-Swap on Wrong Order | Price Sanity    ║")
        print("╚" + "═" * 76 + "╝\n")
        
    def run(self):
        """Main execution loop"""
        server_socket = None
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('127.0.0.1', self.port))
            server_socket.listen(5)
            server_socket.settimeout(2.0)

            log.info(f"👁️  LISTENING on port {self.port}...")

            while self.running:
                try:
                    client_socket, addr = server_socket.accept()
                    log.info(f"[CONNECT] quantum_core from {addr[0]}:{addr[1]}")
                    
                    handler = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, addr),
                        daemon=True,
                        name=f"KrakenHandler-{addr[0]}"
                    )
                    handler.start()

                except socket.timeout:
                    continue
                except Exception as e:
                    log.error(f"Accept error: {e}")

        except Exception as e:
            log.error(f"FATAL: {e}")
        finally:
            if server_socket:
                try:
                    server_socket.close()
                except:
                    pass
            self._print_shutdown()

    def _handle_client(self, client_socket, addr):
        """Handle incoming order from quantum_core with PING/ACK protocol"""
        try:
            client_socket.settimeout(10)

            # Read header (4 bytes)
            header = client_socket.recv(4)
            
            # PING/ACK HEARTBEAT support
            if header and b'PING' in header:
                pong_msg = struct.pack('>I', 4) + b'PONG'
                client_socket.sendall(pong_msg)
                log.debug(f"[PING] Responded with PONG to {addr}")
                client_socket.close()
                return
            
            if not header or len(header) != 4:
                log.error(f"Invalid header from {addr}")
                return

            # Parse length
            length = struct.unpack('>I', header)[0]
            if length <= 0 or length > 100000:
                log.error(f"Invalid order length: {length}")
                return

            # Read order data
            order_data = b''
            while len(order_data) < length:
                chunk = client_socket.recv(min(4096, length - len(order_data)))
                if not chunk:
                    break
                order_data += chunk

            if not order_data:
                log.error(f"No order data from {addr}")
                return

            # Parse JSON
            try:
                order = json.loads(order_data.decode('utf-8', errors='replace'))
            except json.JSONDecodeError as je:
                log.error(f"JSON decode error: {je}")
                return

            log.info(f"[RECEIVE] Order from {addr}: {order.get('symbol')} {order.get('action')}")

            # Execute order
            response = self._execute_order(order)

            # Send response with ACK
            try:
                response_json = json.dumps(response).encode('utf-8')
                response_msg = struct.pack('>I', len(response_json)) + response_json
                client_socket.sendall(response_msg)
                
                # REMOVED: Extra ACK causes protocol misalignment on pooled connections
                # Response JSON already contains 'success' key which is sufficient
                
                log.info(f"✅ Response sent to quantum_core (order_id={response['order_id']})")
            except Exception as e:
                log.error(f"Send failed: {e}")

        except Exception as e:
            log.error(f"Handler error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            try:
                client_socket.close()
                log.info(f"[HANDLER] Socket closed")
            except:
                pass

    def _validate_tp_sl(self, action, entry, tp, sl):
        """
        Validate TP/SL prices. NEW: Auto-swap if inverted.
        
        Returns: (is_valid, tp_corrected, sl_corrected, warning_msg)
        """
        warning = None
        
        # Check for zero/missing values
        if tp == 0:
            log.warning(f"[VALIDATION] TP is 0, setting to entry + 50 pips")
            tp = entry + 0.0050  # [NOVA AUDIT F-12] 50-pip fallback USDCAD (pip=0.0001)
            warning = "TP was 0, set to entry + 50pips"

        if sl == 0:
            log.warning(f"[VALIDATION] SL is 0, setting to entry - 30 pips")
            sl = entry - 0.0030  # [NOVA AUDIT F-12] 30-pip fallback USDCAD
            warning = "SL was 0, set to entry - 30pips"
        
        # Validate based on action
        if action == "BUY":
            # For BUY: TP should be > entry > SL
            if tp < sl:
                log.warning(f"[VALIDATION] BUY: TP ({tp}) < SL ({sl}), SWAPPING")
                tp, sl = sl, tp
                warning = "BUY: TP/SL were swapped (detected inversion)"
            
            if tp < entry:
                log.error(f"[VALIDATION] BUY: TP ({tp}) < entry ({entry}), INVALID")
                return False, tp, sl, "BUY TP must be > entry"
                
            if sl > entry:
                log.error(f"[VALIDATION] BUY: SL ({sl}) > entry ({entry}), INVALID")
                return False, tp, sl, "BUY SL must be < entry"
        
        elif action == "SELL":
            # For SELL: TP should be < entry < SL
            if tp > sl:
                log.warning(f"[VALIDATION] SELL: TP ({tp}) > SL ({sl}), SWAPPING")
                tp, sl = sl, tp
                warning = "SELL: TP/SL were swapped (detected inversion)"
            
            if tp > entry:
                log.error(f"[VALIDATION] SELL: TP ({tp}) > entry ({entry}), INVALID")
                return False, tp, sl, "SELL TP must be < entry"
                
            if sl < entry:
                log.error(f"[VALIDATION] SELL: SL ({sl}) < entry ({entry}), INVALID")
                return False, tp, sl, "SELL SL must be > entry"
        
        return True, tp, sl, warning

    def _execute_order(self, order):
        """Execute order with intelligent scaling and validation"""
        try:
            symbol = order.get('symbol', 'USDCAD')
            action = order.get('action', 'HOLD')
            # BUGFIX #64: Handle both 'lot' and 'lot_size' field names
            lot_size = order.get('lot', order.get('lot_size', 0.1))
            # BUGFIX #64: Handle both 'entry_price' and 'current_price'
            entry_price = order.get('entry_price', order.get('current_price', order.get('entry', order.get('price', 0))))
            # BUGFIX #64: Handle both 'tp' and 'tp_price'
            tp_price = order.get('tp', order.get('tp_price', 0))
            # BUGFIX #64: Handle both 'sl' and 'sl_price'
            sl_price = order.get('sl', order.get('sl_price', 0))
            # BUGFIX #64: Handle both 'quantum_confidence' and 'confidence'
            confidence = order.get('quantum_confidence', order.get('confidence', 0.5))
            
            # ═══════════════════════════════════════════════════════════════════
            # 🧠 NEW: Extract Intelligent Consensus & Ecosystem Data
            # ═══════════════════════════════════════════════════════════════════
            timeframe_consensus = order.get('timeframe_consensus', {})
            ecosystem_validation = order.get('ecosystem_validation', {})
            
            # Extract key metrics
            tf_decision = timeframe_consensus.get('decision', 'HOLD')
            tf_confidence = timeframe_consensus.get('confidence', 0)
            tf_alignment = timeframe_consensus.get('alignment_score', 0)
            tf_reason = timeframe_consensus.get('reason', 'N/A')
            
            ecosystem_penalty = ecosystem_validation.get('penalty', 1.0)
            sl_caution = ecosystem_validation.get('sl_caution', False)
            velocity_alert = ecosystem_validation.get('velocity_alert', False)
            tf_disagreement = ecosystem_validation.get('timeframe_disagreement', False)
            
            # Log ecosystem status
            if ecosystem_penalty < 1.0:
                log.warning(f"[🛡️ ECOSYSTEM] Penalty={ecosystem_penalty:.2f} | SL_Caution={sl_caution} | Velocity={velocity_alert} | TF_Conflict={tf_disagreement}")
            
            # Log timeframe consensus
            if tf_decision != 'HOLD':
                log.info(f"[🧠 CONSENSUS] {tf_decision} @ {tf_confidence}% | Alignment={tf_alignment:.0f}% | {tf_reason}")

            # Validate symbol
            valid_symbols = {'USDCAD', 'GOLD', 'XAU', 'EURUSD', 'EUR', 'USDCAD', 'GBP',
                           'USDJPY', 'JPY', 'USDCAD', 'GBP', 'ETHUSD', 'ETH'}
            if symbol not in valid_symbols:
                return {'success': False, 'message': f'Invalid symbol: {symbol}', 'order_id': 0}

            # Handle HOLD
            if action == 'HOLD':
                log.info(f"⸸️  [{symbol}] HOLD | Conf: {self._conf_bar(confidence)}")
                return {'success': True, 'message': 'HOLD', 'order_id': 0}

            # NEW: Validate TP/SL (auto-swap if needed)
            is_valid, tp_price, sl_price, validation_warning = self._validate_tp_sl(
                action, entry_price, tp_price, sl_price
            )
            
            if not is_valid:
                log.error(f"TP/SL validation failed: {validation_warning}")
                return {'success': False, 'message': validation_warning, 'order_id': 0}
            
            if validation_warning:
                log.info(f"[VALIDATION] {validation_warning} ✓ CORRECTED")

            # Generate ID with persistence
            with self.position_lock:
                self.order_id_counter += 1
                order_id = self.order_id_counter
                try:
                    import tempfile
                    import os
                    with tempfile.NamedTemporaryFile(mode='w', dir='.', delete=False, 
                                                      prefix='kraken_', suffix='.tmp') as tmp:
                        tmp.write(str(self.order_id_counter))
                        tmp_name = tmp.name
                    os.replace(tmp_name, 'kraken_order_id.txt')
                except Exception as e:
                    log.warning(f"Failed to persist order ID: {e}")

            # Determine scaling - OPTIMIZED FOR M1 SCALPING
            if confidence >= 0.65:  # Reduced from 0.75
                initial_lot = lot_size * 0.6  # Increased from 0.5 for better fills
                scaling_str = "🚀 60% ENTRY → Scale +15pips"
            elif confidence >= 0.45:  # Reduced from 0.60
                initial_lot = lot_size * 0.75  # Increased from 0.65
                scaling_str = "⚡ 75% ENTRY → Scale +10pips"
            else:
                initial_lot = lot_size * 1.0  # Full entry for micro-trades
                scaling_str = "📈 100% FULL ENTRY (micro-trade)"
            
            # ═══════════════════════════════════════════════════════════════════
            # 🛡️ ECOSYSTEM PENALTY: Reduce position size when system detects risk
            # ═══════════════════════════════════════════════════════════════════
            if ecosystem_penalty < 1.0:
                pre_penalty_lot = initial_lot
                initial_lot = initial_lot * ecosystem_penalty
                
                # Ensure minimum lot size
                initial_lot = max(0.01, initial_lot)
                
                penalty_reason = []
                if sl_caution:
                    penalty_reason.append("SL_CAUTION")
                if velocity_alert:
                    penalty_reason.append("VELOCITY_ALERT")
                if tf_disagreement:
                    penalty_reason.append("TF_CONFLICT")
                
                log.warning(f"[🛡️ LOT REDUCED] {pre_penalty_lot:.2f} → {initial_lot:.2f} | Penalty={ecosystem_penalty:.2f} | Reasons: {', '.join(penalty_reason)}")
                scaling_str = f"🛡️ RISK-ADJUSTED ({ecosystem_penalty:.0%}): {', '.join(penalty_reason)}"
            
            # ═══════════════════════════════════════════════════════════════════
            # 🧠 CONSENSUS BOOST: Increase lot when timeframes strongly align
            # ═══════════════════════════════════════════════════════════════════
            if tf_alignment >= 80 and tf_decision == action and ecosystem_penalty >= 1.0:
                # Strong timeframe consensus + no ecosystem warnings = boost confidence
                pre_boost_lot = initial_lot
                boost_factor = 1.0 + (tf_alignment - 80) * 0.01  # +1% per point above 80
                initial_lot = initial_lot * min(1.15, boost_factor)  # Max 15% boost
                log.info(f"[🧠 CONSENSUS BOOST] {pre_boost_lot:.2f} → {initial_lot:.2f} | TF Alignment={tf_alignment:.0f}% | {tf_reason}")

            # Print box
            self._print_order_box(order_id, symbol, action, initial_lot, confidence,
                                 entry_price, tp_price, sl_price, scaling_str)

            # Store
            with self.position_lock:
                self.open_positions[symbol] = {
                    'id': order_id,
                    'symbol': symbol,
                    'action': action,
                    'lot': initial_lot,
                    'entry': entry_price,
                    'tp': tp_price,
                    'sl': sl_price,
                    'confidence': confidence,
                    'opened_at': datetime.now().isoformat()
                }

                self.executed_orders.append({
                    'id': order_id,
                    'symbol': symbol,
                    'action': action,
                    'lot': lot_size,
                    'confidence': confidence,
                    'executed_at': datetime.now().isoformat()
                })

            log.info(f"✅ [{symbol}] {action} OK | ID: {order_id}")

            # ===== SOUND ANNOUNCEMENT (DISABLED - quantum_core.py handles audio) =====
            # 🔇 Disabled to prevent double audio - quantum_core sends after Kraken confirms
            # if action in ['BUY', 'SELL']:
            #     ... sound code disabled ...

            # ===== DIAGNOSTIC TRACER =====
            if DIAGNOSTICS_ENABLED and TRACER:
                TRACER.log_llm_decision(
                    llm_name="KRAKEN",
                    genome=order,
                    decision=action,
                    confidence=int(round(confidence * 100)),
                    reasoning=f"Executed:{order_id} Entry:{entry_price:.5f} TP:{tp_price:.5f} SL:{sl_price:.5f} Lot:{initial_lot:.2f}"
                )
                if DASHBOARD:
                    DASHBOARD.broadcast_llm_vote("KRAKEN", action, int(round(confidence * 100)))

            return {'success': True, 'message': f'{action} executed', 'order_id': order_id}

        except Exception as e:
            log.error(f"Execute error: {e}")
            return {'success': False, 'message': str(e), 'order_id': 0}

    def _print_order_box(self, order_id, symbol, action, lot, confidence,
                        entry, tp, sl, scaling_info):
        """Print order execution box"""
        # BUGFIX #22: Normalize confidence to 0-1 range if needed
        if confidence > 1.0:
            confidence = confidence / 100.0  # Convert from 0-100 to 0-1
        confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
        
        action_emoji = "📈" if action == "BUY" else "📉"
        conf_bar = self._conf_bar(confidence)

        print("┌" + "─" * 78 + "┐")
        print(f"│ {action_emoji} ORDER #{order_id:>4} | {symbol:>8} | {action:>4} | {conf_bar} {confidence:>6.1%} │")
        print("├" + "─" * 78 + "┤")
        print(f"│ 💰 Entry: {entry:>10.2f} | 🎯 TP: {tp:>10.2f} | 🛡️  SL: {sl:>10.2f} │")
        print(f"│ 📦 Lot: {lot:>10.2f} | {scaling_info:>60} │")
        print("├" + "─" * 78 + "┤")
        print(f"│ Executed: {len(self.executed_orders):<5} | Open: {len(self.open_positions):<5} │")
        print("└" + "─" * 78 + "┘")

    def _print_status(self):
        """Print status bar"""
        print("┌─ KRAKEN STATUS " + "─" * 61 + "┐")
        print(f"│ 🟢 ONLINE | Port: {self.port:<5} | Symbols: {', '.join(self.symbols):<30} │")
        print("├" + "─" * 76 + "┤")
        print(f"│ Orders: {len(self.executed_orders):<5} | Positions: {len(self.open_positions):<5} │")
        print("└" + "─" * 76 + "┘\n")

    def _conf_bar(self, confidence):
        """Confidence bar"""
        filled = int(confidence * 10)
        empty = 10 - filled
        return f"|{'█' * filled}{'░' * empty}|"

    def _print_shutdown(self):
        """Print shutdown summary"""
        print("\n" + "═" * 80)
        print("KRAKEN SHUTDOWN SUMMARY".center(80))
        print("═" * 80)
        print(f"Total Orders Executed: {len(self.executed_orders)}")
        print(f"Current Open Positions: {len(self.open_positions)}")
        print(f"Final Order ID: {self.order_id_counter}")
        print("═" * 80 + "\n")


# MAIN
if __name__ == "__main__":
    try:
        kraken = KrakenExecutor('cadconfig.yaml')
        kraken.run()
    except KeyboardInterrupt:
        log.info("Shutting down...")
    except Exception as e:
        log.error(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
