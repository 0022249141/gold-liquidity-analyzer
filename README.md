# 🌍 Gold Liquidity Analyzer
## Professional Multi-Timeframe Liquidity-Driven Technical Analysis System for XAU/USD

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

---

## 📋 Overview

**Gold Liquidity Analyzer** is a professional-grade trading analysis system designed for institutional-level traders who use **liquidity-driven technical analysis** to trade gold (XAU/USD).

### 🎯 Key Features

✅ **Multi-Timeframe Analysis** - Simultaneous analysis across M15, H1, H4, and D1  
✅ **Institutional Order Flow Detection** - Identify buy/sell zones based on order flow  
✅ **Fair Value Gaps (FVG)** - Automatic FVG detection and tracking  
✅ **Order Block Analysis** - Find institutional order blocks for continuation trades  
✅ **Previous Highs/Lows** - Track significant swing points  
✅ **Real-time Alerts** - Instant notifications when price approaches liquidity zones  
✅ **Trading Sessions Monitor** - Track Asian, European, and American sessions  
✅ **Live Dashboard** - Real-time market status and analysis  
✅ **MT5 Integration** - Direct connection to MetaTrader 5  

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│          Gold Liquidity Analyzer                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   MT5        │  │  Liquidity   │  │  Sessions    │  │
│  │ Integration  │  │  Analysis    │  │  Clock       │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│         ▲                  ▲                  ▲          │
│         └──────────────────┴──────────────────┘          │
│                     │                                    │
│                ┌────▼────────────┐                      │
│                │  Real-time      │                      │
│                │  Alerts System  │                      │
│                └─────────────────┘                      │
│                     │                                    │
│                ┌────▼────────────┐                      │
│                │  Main App &     │                      │
│                │  Dashboard      │                      │
│                └─────────────────┘                      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 Module Structure

### 1. **mt5_integration.py**
Handles all MetaTrader 5 connections and data retrieval
- Real-time price data
- OHLC historical data
- Multi-timeframe support
- Swing highs/lows detection
- Market structure analysis
- Volume analysis

### 2. **liquidity_analysis.py**
Core liquidity detection algorithms
- Fair Value Gaps (FVG) detection
- Order Block identification
- Breaker Block analysis
- Institutional buy/sell zones
- Support/Resistance levels
- Confluence analysis

### 3. **trading_sessions.py**
Trading session monitoring
- Asian session tracking
- European session tracking
- American session tracking
- Session status display
- Liquidity/volatility per session
- Countdown to next session

### 4. **real_time_alerts.py**
Real-time monitoring and alerting
- Price-based alerts
- Liquidity zone alerts
- Order block alerts
- FVG alerts
- Session change alerts
- Volume anomaly alerts

### 5. **main.py**
Main application orchestrator
- Interactive menu
- Live monitoring mode
- Analysis mode
- Report generation
- Alert display

### 6. **config.py**
Centralized configuration
- MT5 settings
- Monitoring parameters
- Alert thresholds
- Risk management settings
- Output options

---

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.8+
python --version

# Required packages
pip install MetaTrader5 pandas numpy pytz
```

### Installation

```bash
# Clone repository
git clone https://github.com/0022249141/gold-liquidity-analyzer.git
cd gold-liquidity-analyzer

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

#### Interactive Mode
```bash
python main.py
```

Then select from menu:
- 1: Analyze Current Market
- 2: Start Live Monitoring
- 3: View Alert History
- 4: Generate Report
- 5: Display Sessions Clock

#### Live Monitoring Mode
```bash
python main.py --mode monitor
```

#### Analysis Mode (One-time Analysis)
```bash
python main.py --mode analyze
```

---

## 📊 Example: Using the Analyzer

```python
from main import GoldLiquidityAnalyzer

# Initialize
analyzer = GoldLiquidityAnalyzer()

if analyzer.initialize():
    # Display current status
    analyzer.display_current_status()
    
    # Perform analysis
    analysis = analyzer.analyze_multi_timeframe()
    
    # Generate report
    analyzer.generate_report('analysis_report.txt')
    
    # Start live monitoring
    analyzer.start_live_monitoring()
    
    # Stop when done
    analyzer.stop()
```

---

## 🔧 Configuration Guide

Edit `config.py` to customize:

### Alert Thresholds (pips)
```python
config.alerts.liquidity_zone_threshold = 50
config.alerts.order_block_threshold = 30
config.alerts.fvg_threshold = 40
```

### Monitoring Settings
```python
config.monitoring.check_interval = 5  # seconds
config.monitoring.timeframes = ['M15', 'H1', 'H4', 'D1']
config.monitoring.lookback_bars = 100
```

### Risk Management
```python
config.risk_management.risk_percentage = 1.0  # % per trade
config.risk_management.tp_to_sl_ratio = 2.0
config.risk_management.max_open_positions = 3
```

---

## 📈 Analysis Examples

### Detecting Liquidity Zones
```python
from liquidity_analysis import LiquidityDetector
from mt5_integration import MT5Connection

mt5 = MT5Connection()
detector = LiquidityDetector()

# Get data
ohlc = mt5.get_ohlc_data('H4', bars=100)

# Analyze
analysis = detector.analyze_liquidity_confluence(ohlc, 'H4')

# Get zones
print("Buy Zones:", analysis['buy_zones'])
print("Sell Zones:", analysis['sell_zones'])
```

### Detecting Order Blocks
```python
# Find order blocks
order_blocks = detector.detect_order_blocks(ohlc, 'H4')

for ob in order_blocks:
    print(f"OB Level: {ob.center_price:.2f}")
    print(f"Strength: {ob.strength:.0f}%")
```

### Finding FVGs
```python
# Detect Fair Value Gaps
fvgs = detector.detect_fair_value_gaps(ohlc, 'H1')

for fvg in fvgs:
    print(f"FVG Type: {fvg['type']}")
    print(f"Range: {fvg['bottom_price']:.2f} - {fvg['top_price']:.2f}")
```

---

## 🎯 Trading Strategy Integration

The analyzer is designed to support institutional trading strategies:

### Multi-Timeframe Confirmation
1. **Analyze Daily (D1)** - Identify major trend and key levels
2. **Check 4H** - Find order blocks and FVGs
3. **Monitor H1** - Entry signals and liquidity zones
4. **Watch M15** - Precise entry execution

### Alert-Based Trading
1. System alerts when price approaches liquidity zones
2. Trader evaluates confluence of multiple timeframes
3. Entry at institutional buy/sell zones
4. Stop loss at higher timeframe order blocks
5. Take profit at next liquidity level

---

## 📊 Output Examples

### Real-time Alerts
```
🚨 ORDER BLOCK HIT (H4)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Price has entered order block zone (2045.50 - 2048.30)
💰 Price Level: 2046.90
💹 Current Price: 2046.85
📏 Distance: 0.0 pips
⏰ TimeFrame: H4
🎯 Action: BUY
📈 Confidence: 82%
🕐 Time: 2026-09-15 10:30:45
```

### Analysis Report
```
GOLD LIQUIDITY ANALYSIS REPORT
Generated: 2026-09-15 10:45:30

Current Price: 2046.85
Spread: 0.3 pips

H4 TIMEFRAME
================
Trend: UPTREND
Nearest Buy Zone: 2044.50
Nearest Sell Zone: 2050.20
Fair Value Gaps: 3 identified
Order Blocks: 2 identified
```

---

## ⚙️ Advanced Features

### Multi-Timeframe Monitoring
The system simultaneously tracks:
- **M15**: Entry confirmation
- **H1**: Support/resistance zones
- **H4**: Order blocks and major structure
- **D1**: Macro trend and key levels

### Confluence Analysis
Alerts only when multiple factors align:
- Price near support/resistance
- Volume confirmation
- Order block zone
- FVG confluence
- Session timing

### Real-time Synchronization
- Updates every 5 seconds (configurable)
- Non-blocking alerts
- Historical alert tracking
- Export capabilities

---

## 📝 Logging & Reports

### Alert History
```python
# Get recent alerts
alerts = analyzer.alerts_system.get_alert_history(limit=20)

# Export to JSON
analyzer.alerts_system.export_alerts_to_json('alerts.json')
```

### Detailed Reports
```bash
# Generate analysis report
python main.py --mode analyze
# Creates: gold_analysis_report.txt
```

---

## 🔐 Risk Management

Built-in risk management features:
- Maximum daily loss limit
- Position sizing based on risk
- Stop loss at liquidity levels
- Trailing stop support
- Maximum open positions limit

---

## 🐛 Troubleshooting

### MT5 Connection Issues
```python
# Check connection
mt5 = MT5Connection()
if not mt5.connected:
    print("Failed to connect. Check MT5 terminal is running")
```

### Data Retrieval Problems
```python
# Verify symbol
price = mt5.get_current_price()
if 'error' in price:
    print("Error:", price['error'])
```

### Alert Not Triggering
- Check alert thresholds in config.py
- Verify monitoring is running
- Check MT5 data update frequency

---

## 📚 Documentation

- [Configuration Guide](docs/CONFIG.md)
- [API Reference](docs/API.md)
- [Strategy Examples](docs/STRATEGIES.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional liquidity detection algorithms
- Machine learning confluence detection
- Web dashboard UI
- Mobile alerts
- Strategy backtester

---

## ⚠️ Disclaimer

**Important:** This tool is for educational and analysis purposes. 

⚠️ **Risk Warning:**
- Trading in gold and derivatives involves significant risk
- This is NOT financial advice
- Always use proper risk management
- Paper trade before live trading
- Consult with financial advisors

---

## 📄 License

MIT License - See LICENSE file for details

---

## 📞 Support

For issues and questions:
- Open GitHub issues
- Check documentation
- Review example code

---

## 🎓 Learning Resources

### Liquidity-Driven Trading Concepts
- Order Blocks: Where institutional orders accumulate
- Fair Value Gaps: Unfilled price gaps in market
- Swing Points: Previous highs and lows
- Confluence: Multiple factors aligning

### Related Tools
- MetaTrader 5: Trading platform
- TradingView: Chart analysis
- Economic Calendar: Event tracking

---

## 🚀 Roadmap

- [ ] WebSocket real-time data
- [ ] Advanced confluence scoring
- [ ] Machine learning pattern recognition
- [ ] Web-based dashboard
- [ ] Mobile app notifications
- [ ] Discord/Telegram integration
- [ ] Performance backtester
- [ ] Risk analyzer
- [ ] Multi-symbol support

---

## 👨‍💻 Author

Developed for professional traders using institutional-grade liquidity analysis.

**Repository:** [gold-liquidity-analyzer](https://github.com/0022249141/gold-liquidity-analyzer)

---

**Last Updated:** 2026-09-15  
**Version:** 1.0.0  
**Status:** Production Ready
