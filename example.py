"""
Example: Using Gold Liquidity Analyzer
Demonstrates basic usage of the system
"""

from main import GoldLiquidityAnalyzer
from config import get_config
from real_time_alerts import Alert
import time

def example_basic_analysis():
    """
    Example 1: Basic market analysis
    """
    print("\n" + "="*80)
    print("EXAMPLE 1: BASIC MARKET ANALYSIS".center(80))
    print("="*80)
    
    # Initialize analyzer
    analyzer = GoldLiquidityAnalyzer()
    
    if analyzer.initialize():
        # Display current status
        analyzer.display_current_status()
        
        # Perform multi-timeframe analysis
        analyzer.analyze_multi_timeframe()
        
        # Generate report
        analyzer.generate_report('example_analysis.txt')
        
        analyzer.stop()

def example_liquidity_detection():
    """
    Example 2: Detect liquidity zones
    """
    print("\n" + "="*80)
    print("EXAMPLE 2: LIQUIDITY ZONE DETECTION".center(80))
    print("="*80)
    
    from mt5_integration import MT5Connection
    from liquidity_analysis import LiquidityDetector
    
    mt5 = MT5Connection()
    detector = LiquidityDetector()
    
    if mt5.connected:
        # Get H4 data
        ohlc = mt5.get_ohlc_data('H4', bars=100)
        current_price = mt5.get_current_price()['bid']
        
        print(f"\nAnalyzing {len(ohlc)} bars of H4 data")
        print(f"Current Price: {current_price:.2f}")
        
        # Analyze liquidity
        analysis = detector.analyze_liquidity_confluence(ohlc, 'H4', current_price)
        
        print("\n🟢 BUY ZONES:")
        for zone in analysis['buy_zones']:
            print(f"  Level: {zone.center_price:.2f} (Strength: {zone.strength:.0f}%)")
        
        print("\n🔴 SELL ZONES:")
        for zone in analysis['sell_zones']:
            print(f"  Level: {zone.center_price:.2f} (Strength: {zone.strength:.0f}%)")
        
        print("\n📍 ORDER BLOCKS:")
        for ob in analysis['order_blocks'][:3]:
            print(f"  {ob.center_price:.2f} (Range: {ob.bottom_price:.2f} - {ob.top_price:.2f})")
        
        mt5.disconnect()

def example_fvg_detection():
    """
    Example 3: Detect Fair Value Gaps
    """
    print("\n" + "="*80)
    print("EXAMPLE 3: FAIR VALUE GAP DETECTION".center(80))
    print("="*80)
    
    from mt5_integration import MT5Connection
    from liquidity_analysis import LiquidityDetector
    
    mt5 = MT5Connection()
    detector = LiquidityDetector()
    
    if mt5.connected:
        # Get H1 data
        ohlc = mt5.get_ohlc_data('H1', bars=50)
        
        print(f"\nAnalyzing {len(ohlc)} bars for Fair Value Gaps")
        
        # Detect FVGs
        fvgs = detector.detect_fair_value_gaps(ohlc, 'H1')
        
        print(f"\nFound {len(fvgs)} Fair Value Gaps:\n")
        
        for i, fvg in enumerate(fvgs[:5], 1):
            print(f"{i}. {fvg['type']}")
            print(f"   Range: {fvg['bottom_price']:.2f} - {fvg['top_price']:.2f}")
            print(f"   Gap Size: {fvg['gap_size']:.2f} pips")
            print(f"   Strength: {fvg['strength']:.0f}%\n")
        
        mt5.disconnect()

def example_trading_sessions():
    """
    Example 4: Trading sessions monitoring
    """
    print("\n" + "="*80)
    print("EXAMPLE 4: TRADING SESSIONS MONITORING".center(80))
    print("="*80)
    
    from trading_sessions import TradingSessionsClock
    
    clock = TradingSessionsClock()
    
    print("\n📊 Current Session Status:\n")
    
    for status in clock.get_all_sessions_status():
        status_emoji = status['status'].split()[0]
        print(f"{status_emoji} {status['session_name']}")
        print(f"   Time: {status['local_time']} ({status['timezone']})")
        print(f"   Liquidity: {status['liquidity']} | Volatility: {status['volatility']}")
        print()
    
    # Show next session
    next_session = clock.get_next_active_session()
    print(f"Next Session: {next_session.value['name']}")

def example_configuration():
    """
    Example 5: Working with configuration
    """
    print("\n" + "="*80)
    print("EXAMPLE 5: CONFIGURATION CUSTOMIZATION".center(80))
    print("="*80)
    
    config = get_config()
    
    # Customize settings
    print("\nModifying configuration...")
    config.alerts.liquidity_zone_threshold = 75
    config.monitoring.check_interval = 10
    config.risk_management.risk_percentage = 2.0
    config.risk_management.tp_to_sl_ratio = 3.0
    
    print("\n✅ Configuration updated:")
    print(f"  Liquidity Zone Alert Threshold: {config.alerts.liquidity_zone_threshold} pips")
    print(f"  Check Interval: {config.monitoring.check_interval} seconds")
    print(f"  Risk Per Trade: {config.risk_management.risk_percentage}%")
    print(f"  TP/SL Ratio: {config.risk_management.tp_to_sl_ratio}:1")

def example_alert_callback():
    """
    Example 6: Custom alert callbacks
    """
    print("\n" + "="*80)
    print("EXAMPLE 6: CUSTOM ALERT CALLBACKS".center(80))
    print("="*80)
    
    from real_time_alerts import RealTimeAlertsSystem
    
    alerts_system = RealTimeAlertsSystem()
    
    # Define custom callback
    def my_alert_handler(alert: Alert):
        """Custom alert handler"""
        print(f"\n🚨 CUSTOM ALERT: {alert.title}")
        print(f"   Price: {alert.current_price:.2f}")
        print(f"   Action: {alert.action_suggested}")
        print(f"   Confidence: {alert.confidence:.0f}%")
    
    # Register callback
    alerts_system.register_alert_callback(my_alert_handler)
    
    print("\n✅ Custom alert callback registered")
    print("   When alerts occur, your callback will be triggered")

def example_market_structure():
    """
    Example 7: Market structure analysis
    """
    print("\n" + "="*80)
    print("EXAMPLE 7: MARKET STRUCTURE ANALYSIS".center(80))
    print("="*80)
    
    from mt5_integration import MT5Connection
    
    mt5 = MT5Connection()
    
    if mt5.connected:
        print("\nAnalyzing market structure on different timeframes:\n")
        
        for tf in ['H1', 'H4', 'D1']:
            structure = mt5.get_market_structure(tf, bars=100)
            
            print(f"\n{tf} Timeframe:")
            print(f"  Trend: {structure['trend']}")
            print(f"  Current Price: {structure['current_price']:.2f}")
            print(f"  Recent High: {structure['recent_high']:.2f}")
            print(f"  Recent Low: {structure['recent_low']:.2f}")
        
        mt5.disconnect()

def run_all_examples():
    """
    Run all examples
    """
    print("\n" + "#"*80)
    print("# GOLD LIQUIDITY ANALYZER - EXAMPLES".center(80))
    print("#"*80)
    
    try:
        # Example 1: Basic Analysis
        example_basic_analysis()
        
        # Example 2: Liquidity Detection
        example_liquidity_detection()
        
        # Example 3: FVG Detection
        example_fvg_detection()
        
        # Example 4: Trading Sessions
        example_trading_sessions()
        
        # Example 5: Configuration
        example_configuration()
        
        # Example 6: Alert Callbacks
        example_alert_callback()
        
        # Example 7: Market Structure
        example_market_structure()
        
        print("\n" + "#"*80)
        print("# ALL EXAMPLES COMPLETED".center(80))
        print("#"*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        example_name = sys.argv[1]
        
        examples = {
            '1': example_basic_analysis,
            '2': example_liquidity_detection,
            '3': example_fvg_detection,
            '4': example_trading_sessions,
            '5': example_configuration,
            '6': example_alert_callback,
            '7': example_market_structure,
            'all': run_all_examples
        }
        
        if example_name in examples:
            examples[example_name]()
        else:
            print(f"Unknown example: {example_name}")
            print(f"Available: {', '.join(examples.keys())}")
    else:
        print("\nUsage: python example.py [example_number|all]")
        print("\nExamples:")
        print("  1 - Basic market analysis")
        print("  2 - Liquidity zone detection")
        print("  3 - Fair Value Gap detection")
        print("  4 - Trading sessions monitoring")
        print("  5 - Configuration customization")
        print("  6 - Custom alert callbacks")
        print("  7 - Market structure analysis")
        print("  all - Run all examples")
