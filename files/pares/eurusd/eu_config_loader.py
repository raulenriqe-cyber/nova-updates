#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                 🎯 EURUSD CONFIG LOADER - CENTRALIZED CONFIGURATION          ║
║                                                                              ║
║  Loads EURUSD M15 ports and parameters from euconfig.yaml                   ║
║  Single source of truth for all EU system configuration                      ║
║                                                                              ║
║  Author: Polaricelabs © 2026                                                ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import os
import yaml
import json
from typing import Dict, Any, Optional

# Get config file path (same directory as this file)
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'euconfig.yaml')

class EUConfig:
    """Centralized configuration manager for EURUSD M15 system"""
    
    _config = None
    _loaded = False
    
    @classmethod
    def load(cls) -> Dict[str, Any]:
        """Load configuration from euconfig.yaml"""
        if cls._loaded and cls._config:
            return cls._config
        
        if not os.path.exists(CONFIG_PATH):
            raise FileNotFoundError(f"euconfig.yaml not found at {CONFIG_PATH}")
        
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            cls._config = yaml.safe_load(f)
        
        cls._loaded = True
        return cls._config
    
    @classmethod
    def get(cls, key_path: str, default: Any = None) -> Any:
        """
        Get config value by dot-separated path
        Example: get('ports.trinity.port') -> 7666
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
            return cls.get('ports.trinity.port')
        elif service.lower() == 'kraken':
            return cls.get('ports.kraken.port')
        elif service.lower() == 'ollama':
            return cls.get('ports.shared.ollama.port')
        elif service.lower() == 'sound':
            return cls.get('ports.shared.sound.port')
        else:
            # LLM service (llm1-llm9)
            llm_num = service.lower().replace('llm', '')
            if llm_num.isdigit():
                llm_key = f'llm{llm_num}'
                return cls.get(f'ports.llm_network.{llm_key}.port')
        
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
    """Get Trinity port for EURUSD"""
    return EUConfig.get_port('trinity')

def get_kraken_port() -> int:
    """Get Kraken port for EURUSD"""
    return EUConfig.get_port('kraken')

def get_llm_port(llm_num: int) -> int:
    """Get port for specific LLM (1-9)"""
    return EUConfig.get_port(f'llm{llm_num}')

def get_ollama_port() -> int:
    """Get Ollama port (shared)"""
    return EUConfig.get_port('ollama')

def get_sound_port() -> int:
    """Get Sound alert port"""
    return EUConfig.get_port('sound')

def get_all_llm_ports() -> Dict[str, int]:
    """Get all LLM ports"""
    ports = {}
    for i in range(1, 10):
        ports[f'llm{i}'] = EUConfig.get_port(f'llm{i}')
    return ports

def get_symbol() -> str:
    """Get market symbol"""
    return EUConfig.get('market.symbol', 'EURUSD')

def get_timeframe() -> str:
    """Get timeframe"""
    return EUConfig.get('market.timeframe', 'M15')

def get_sl_range() -> tuple:
    """Get SL min/max pips"""
    return (
        EUConfig.get('trading.stop_loss.min_pips'),
        EUConfig.get('trading.stop_loss.max_pips')
    )

def get_tp_range() -> tuple:
    """Get TP min/max pips"""
    return (
        EUConfig.get('trading.take_profit.min_pips'),
        EUConfig.get('trading.take_profit.max_pips')
    )

def get_atr_range() -> tuple:
    """Get ATR floor/ceiling"""
    return (
        EUConfig.get('trading.volatility.atr_floor'),
        EUConfig.get('trading.volatility.atr_ceiling')
    )

def get_cooldown_seconds() -> int:
    """Get cooldown between trades"""
    return EUConfig.get('trading.cooldown_seconds', 180)

def get_min_confidence() -> int:
    """Get minimum confidence threshold"""
    return EUConfig.get('trading.confidence.min_threshold', 65)

def get_min_adx() -> int:
    """Get minimum ADX"""
    return EUConfig.get('trading.adx.minimum', 20)

# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("═" * 80)
    print("🎯 EURUSD CONFIG LOADER - TEST")
    print("═" * 80)
    
    try:
        print("\n✅ Configuration loaded successfully\n")
        
        print("📊 PORTS:")
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
        print(f"  SL:    {sl_min}-{sl_max} pips")
        print(f"  TP:    {tp_min}-{tp_max} pips")
        print(f"  ATR:   {get_atr_range()[0]}-{get_atr_range()[1]} pips")
        print(f"  Cooldown: {get_cooldown_seconds()}s")
        print(f"  Min Confidence: {get_min_confidence()}%")
        print(f"  Min ADX: {get_min_adx()}")
        
        print("\n✨ CONFIG OK - ALL VALUES LOADED")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
