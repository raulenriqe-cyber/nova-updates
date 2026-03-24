#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                 💷 NZDUSD CONFIG LOADER - CENTRALIZED CONFIGURATION           ║
║                                                                              ║
║  Loads NZDUSD ports and parameters from nzdconfig.yaml                       ║
║  Single source of truth for all GBP system configuration                     ║
║                                                                              ║
║  Author: Polaricelabs © 2026                                                ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import os
import yaml
import json
from typing import Dict, Any, Optional

# Get config file path (same directory as this file)
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'nzdconfig.yaml')

class nzdconfig:
    """Centralized configuration manager for NZDUSD system"""
    
    _config = None
    _loaded = False
    
    @classmethod
    def load(cls) -> Dict[str, Any]:
        """Load configuration from nzdconfig.yaml"""
        if cls._loaded and cls._config:
            return cls._config
        
        if not os.path.exists(CONFIG_PATH):
            raise FileNotFoundError(f"nzdconfig.yaml not found at {CONFIG_PATH}")
        
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            cls._config = yaml.safe_load(f)
        
        cls._loaded = True
        return cls._config
    
    @classmethod
    def get(cls, key_path: str, default: Any = None) -> Any:
        """
        Get config value by dot-separated path
        Example: get('sockets.trinity_port') -> 9266
        """
        config = cls.load()
        
        keys = key_path.split('.')
        value = config
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    @classmethod
    def get_port(cls, service: str) -> int:
        """Get port for a specific service"""
        # Handle trinity and kraken separately
        if service.lower() == 'trinity':
            return cls.get('sockets.trinity_port')
        elif service.lower() == 'kraken':
            return cls.get('sockets.kraken_port')
        elif service.lower() == 'ollama':
            return 11434  # Default ollama port (shared)
        elif service.lower() == 'sound':
            return cls.get('sockets.sound_port')
        elif service.lower() == 'injector':
            return cls.get('sockets.injector_port')
        elif service.lower() == 'executor':
            return cls.get('sockets.executor_port')
        else:
            # LLM service (llm1-llm10)
            llm_num = service.lower().replace('llm', '')
            if llm_num.isdigit():
                # Try sockets section first
                port = cls.get(f'sockets.llm{llm_num}_port')
                if port is not None:
                    return port
                # Fallback to models section
                port = cls.get(f'llms.models.GBP_LLM{llm_num}.port')
                if port is not None:
                    return port
        
        raise ValueError(f"Unknown service: {service}")
    
    @classmethod
    def get_trading_param(cls, param: str, default: Any = None) -> Any:
        """Get trading parameter"""
        return cls.get(f'trading.{param}', default)
    
    @classmethod
    def print_config(cls):
        """Print configuration in readable format"""
        config = cls.load()
        print(json.dumps(config, indent=2))


# ═══════════════════════════════════════════════════════════════════════════════
# QUICK ACCESS FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_trinity_port() -> int:
    """Get Trinity port for NZDUSD"""
    return nzdconfig.get_port('trinity')

def get_kraken_port() -> int:
    """Get Kraken port for NZDUSD"""
    return nzdconfig.get_port('kraken')

def get_llm_port(llm_num: int) -> int:
    """Get port for specific LLM (1-10)"""
    return nzdconfig.get_port(f'llm{llm_num}')

def get_ollama_port() -> int:
    """Get Ollama port (shared)"""
    return nzdconfig.get_port('ollama')

def get_sound_port() -> int:
    """Get Sound alert port"""
    return nzdconfig.get_port('sound')

def get_injector_port() -> int:
    """Get Injector port (MT5 -> Python)"""
    return nzdconfig.get_port('injector')

def get_executor_port() -> int:
    """Get Executor port (Python -> MT5)"""
    return nzdconfig.get_port('executor')

def get_all_llm_ports() -> Dict[str, int]:
    """Get all LLM ports"""
    ports = {}
    for i in range(1, 11):
        try:
            ports[f'llm{i}'] = nzdconfig.get_port(f'llm{i}')
        except:
            pass
    return ports

def get_symbol() -> str:
    """Get market symbol"""
    return nzdconfig.get('symbol', 'NZDUSD')

def get_timeframe() -> str:
    """Get primary timeframe"""
    return nzdconfig.get('primary_timeframe', 'M5')

def get_sl_range() -> tuple:
    """Get SL min/max USD"""
    return (
        nzdconfig.get('trading.scalp_sl', 150),
        nzdconfig.get('trading.swing_sl', 800)
    )

def get_tp_range() -> tuple:
    """Get TP min/max USD"""
    return (
        nzdconfig.get('trading.scalp_tp', 100),
        nzdconfig.get('trading.swing_tp', 600)
    )

def get_cooldown_seconds() -> int:
    """Get cooldown between trades (GBP needs longer cooldown)"""
    return 300  # 5 minutes for FOREX volatility

def get_min_confidence() -> int:
    """Get minimum confidence threshold"""
    return nzdconfig.get('confidence.minimum_signal', 70)

def get_max_positions() -> int:
    """Get max positions"""
    return nzdconfig.get('trading.max_positions', 3)

def get_pip_value() -> float:
    """Get pip value for NZDUSD"""
    return nzdconfig.get('trading.pip_value', 1.0)

def get_volatility_thresholds() -> dict:
    """Get ATR thresholds for volatility regimes"""
    return {
        'low': nzdconfig.get('indicators.atr.low_volatility', 200),
        'normal': nzdconfig.get('indicators.atr.normal_volatility', 500),
        'high': nzdconfig.get('indicators.atr.high_volatility', 1200),
        'extreme': nzdconfig.get('indicators.atr.extreme_volatility', 2500)
    }

# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("═" * 80)
    print("₿ NZDUSD CONFIG LOADER - TEST")
    print("═" * 80)
    
    try:
        print("\n✅ Configuration loaded successfully\n")
        
        print("📊 PORTS:")
        print(f"  Injector: {get_injector_port()}")
        print(f"  Executor: {get_executor_port()}")
        print(f"  Trinity:  {get_trinity_port()}")
        print(f"  Kraken:   {get_kraken_port()}")
        print(f"  Ollama:   {get_ollama_port()}")
        print(f"  Sound:    {get_sound_port()}")
        
        print("\n📡 LLM PORTS:")
        for llm, port in get_all_llm_ports().items():
            print(f"  {llm}: {port}")
        
        print("\n📈 TRADING PARAMS:")
        sl_min, sl_max = get_sl_range()
        tp_min, tp_max = get_tp_range()
        print(f"  Symbol: {get_symbol()}")
        print(f"  Timeframe: {get_timeframe()}")
        print(f"  SL:    ${sl_min}-${sl_max}")
        print(f"  TP:    ${tp_min}-${tp_max}")
        print(f"  Pip Value: ${get_pip_value()}")
        print(f"  Cooldown: {get_cooldown_seconds()}s")
        print(f"  Min Confidence: {get_min_confidence()}%")
        print(f"  Max Positions: {get_max_positions()}")
        
        print("\n📊 VOLATILITY THRESHOLDS:")
        for regime, value in get_volatility_thresholds().items():
            print(f"  {regime}: ${value}")
        
        print("\n✨ CONFIG OK - ALL VALUES LOADED")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
