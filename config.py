"""
Configuration Settings
Centralized configuration for Gold Liquidity Analyzer
"""

import os
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class MT5Config:
    """MetaTrader 5 Configuration"""
    # Terminal path (None for default)
    terminal_path: str = None
    
    # Symbol to trade
    symbol: str = "XAUUSD"
    
    # Connection timeout (seconds)
    timeout: int = 30
    
    # Auto-reconnect enabled
    auto_reconnect: bool = True

@dataclass
class MonitoringConfig:
    """Monitoring Configuration"""
    # Check interval (seconds)
    check_interval: int = 5
    
    # Timeframes to monitor
    timeframes: List[str] = None
    
    # Number of bars for analysis
    lookback_bars: int = 100
    
    def __post_init__(self):
        if self.timeframes is None:
            self.timeframes = ['M15', 'H1', 'H4', 'D1']

@dataclass
class AlertConfig:
    """Alert Configuration"""
    # Alert thresholds (in pips)
    liquidity_zone_threshold: float = 50
    order_block_threshold: float = 30
    fvg_threshold: float = 40
    support_resistance_threshold: float = 60
    
    # Alert history size
    max_alert_history: int = 1000
    
    # Duplicate alert prevention (seconds)
    duplicate_alert_timeout: int = 300
    
    # Severity levels
    alert_severities: Dict[str, str] = None
    
    def __post_init__(self):
        if self.alert_severities is None:
            self.alert_severities = {
                'liquidity_zone': 'WARNING',
                'order_block': 'CRITICAL',
                'fvg': 'CRITICAL',
                'breakout': 'WARNING',
                'volume': 'INFO'
            }

@dataclass
class LiquidityConfig:
    """Liquidity Detection Configuration"""
    # Minimum candles for order block
    min_candles_ob: int = 2
    
    # FVG detection enabled
    detect_fvg: bool = True
    
    # Order block detection enabled
    detect_order_blocks: bool = True
    
    # Breaker block detection enabled
    detect_breaker_blocks: bool = True
    
    # Support/Resistance detection enabled
    detect_support_resistance: bool = True
    
    # Confluence factor weight
    confluence_weight: float = 0.8

@dataclass
class SessionConfig:
    """Trading Session Configuration"""
    # Session times (UTC)
    sessions: Dict[str, Dict[str, int]] = None
    
    # Alert on session change
    alert_on_session_change: bool = True
    
    # Highlight high volatility periods
    highlight_eu_us_overlap: bool = True
    
    def __post_init__(self):
        if self.sessions is None:
            self.sessions = {
                'asian': {'start': 0, 'end': 8},
                'european': {'start': 8, 'end': 16},
                'american': {'start': 13, 'end': 21}
            }

@dataclass
class OutputConfig:
    """Output and Export Configuration"""
    # Alert export format
    alert_export_format: str = 'json'  # json, csv, txt
    
    # Report output directory
    report_directory: str = './reports'
    
    # Alert log file
    alert_log_file: str = './logs/alerts.log'
    
    # Enable console output
    console_output: bool = True
    
    # Console output verbosity (DEBUG, INFO, WARNING, ERROR)
    console_verbosity: str = 'INFO'
    
    # Enable file logging
    file_logging: bool = True
    
    # Create directories if not exist
    auto_create_dirs: bool = True
    
    def ensure_directories(self):
        """Create necessary directories if they don't exist"""
        if self.auto_create_dirs:
            os.makedirs(self.report_directory, exist_ok=True)
            os.makedirs(os.path.dirname(self.alert_log_file), exist_ok=True)

@dataclass
class RiskManagementConfig:
    """Risk Management Configuration"""
    # Risk per trade (percentage of account)
    risk_percentage: float = 1.0
    
    # Maximum daily loss (percentage)
    max_daily_loss: float = 5.0
    
    # Position size calculation
    # 'fixed': Fixed lot size
    # 'dynamic': Based on ATR or volatility
    position_sizing: str = 'dynamic'
    
    # Stop loss type
    # 'fixed': Fixed pips
    # 'atr': Based on ATR
    # 'liquidity': At nearest liquidity level
    stop_loss_type: str = 'liquidity'
    
    # Take profit multiplier (vs stop loss)
    tp_to_sl_ratio: float = 2.0
    
    # Maximum open positions
    max_open_positions: int = 3
    
    # Trailing stop enabled
    trailing_stop_enabled: bool = True
    
    # Trailing stop distance (pips)
    trailing_stop_distance: int = 20

class Config:
    """Main Configuration Class"""
    
    def __init__(self):
        """Initialize all configuration sections"""
        self.mt5 = MT5Config()
        self.monitoring = MonitoringConfig()
        self.alerts = AlertConfig()
        self.liquidity = LiquidityConfig()
        self.sessions = SessionConfig()
        self.output = OutputConfig()
        self.risk_management = RiskManagementConfig()
        
        # Ensure output directories exist
        self.output.ensure_directories()
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary"""
        return {
            'mt5': vars(self.mt5),
            'monitoring': vars(self.monitoring),
            'alerts': vars(self.alerts),
            'liquidity': vars(self.liquidity),
            'sessions': vars(self.sessions),
            'output': vars(self.output),
            'risk_management': vars(self.risk_management)
        }
    
    def print_config(self):
        """Print current configuration"""
        print("\n" + "="*80)
        print("CONFIGURATION SETTINGS".center(80))
        print("="*80)
        
        import json
        config_dict = self.to_dict()
        print(json.dumps(config_dict, indent=2, default=str))

# Global configuration instance
_config = None

def get_config() -> Config:
    """Get global configuration instance"""
    global _config
    if _config is None:
        _config = Config()
    return _config

def reset_config():
    """Reset configuration to defaults"""
    global _config
    _config = Config()

# Example usage
if __name__ == "__main__":
    config = get_config()
    config.print_config()
    
    # Customize settings
    config.alerts.liquidity_zone_threshold = 75
    config.monitoring.check_interval = 10
    config.risk_management.risk_percentage = 2.0
    
    print("\n✅ Configuration loaded successfully")
