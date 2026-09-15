"""
Main Application
Integrates all modules: MT5, Liquidity Analysis, Trading Sessions, Real-time Alerts
Entry point for the Gold Liquidity Analyzer system
"""

import sys
import time
from datetime import datetime
from mt5_integration import MT5Connection
from liquidity_analysis import LiquidityDetector
from trading_sessions import TradingSessionsClock
from real_time_alerts import RealTimeAlertsSystem, Alert
import argparse

class GoldLiquidityAnalyzer:
    """
    Main application class
    Orchestrates all components
    """
    
    def __init__(self, mt5_path: str = None):
        """Initialize the analyzer"""
        self.mt5 = MT5Connection(mt5_path)
        self.liquidity_detector = LiquidityDetector()
        self.sessions_clock = TradingSessionsClock()
        self.alerts_system = RealTimeAlertsSystem()
        self.is_running = False
        
        # Configuration
        self.monitoring_interval = 5  # seconds
        self.timeframes = ['M15', 'H1', 'H4', 'D1']
        
    def initialize(self) -> bool:
        """Initialize all components"""
        print("🚀 Initializing Gold Liquidity Analyzer...")
        
        if not self.mt5.connected:
            print("❌ Failed to connect to MetaTrader 5")
            return False
        
        print("✅ MT5 Connection established")
        print("✅ Liquidity Detector initialized")
        print("✅ Trading Sessions Clock initialized")
        print("✅ Real-time Alerts System initialized")
        
        return True
    
    def display_header(self):
        """Display application header"""
        print("\n" + "="*80)
        print("🌍 GOLD LIQUIDITY-DRIVEN TECHNICAL ANALYSIS SYSTEM".center(80))
        print("💎 XAU/USD Multi-Timeframe Analysis".center(80))
        print("="*80 + "\n")
    
    def display_current_status(self):
        """Display current market status"""
        print("\n" + "-"*80)
        print("📊 CURRENT MARKET STATUS".center(80))
        print("-"*80)
        
        # Current price
        price_data = self.mt5.get_current_price()
        if 'error' not in price_data:
            print(f"\n💰 XAU/USD Price: {price_data['bid']:.2f}")
            print(f"   Bid: {price_data['bid']:.2f} | Ask: {price_data['ask']:.2f}")
            print(f"   Spread: {price_data['spread']:.1f} pips")
        
        # Trading sessions status
        print("\n🌍 Trading Sessions:")
        for status in self.sessions_clock.get_all_sessions_status():
            status_emoji = status['status'].split()[0]
            print(f"   {status_emoji} {status['session_name']:20} {status['local_time']}")
    
    def analyze_multi_timeframe(self, display: bool = True) -> Dict:
        """
        Perform multi-timeframe liquidity analysis
        
        Args:
            display: Whether to print results
            
        Returns:
            dict: Analysis results for all timeframes
        """
        print("\n" + "-"*80)
        print("📈 MULTI-TIMEFRAME LIQUIDITY ANALYSIS".center(80))
        print("-"*80)
        
        current_price = self.mt5.get_current_price()['bid']
        analysis_results = {}
        
        for tf in self.timeframes:
            print(f"\n▶️  {tf} Timeframe Analysis")
            print("-" * 40)
            
            # Get OHLC data
            ohlc_data = self.mt5.get_ohlc_data(tf, bars=100)
            
            if 'error' in ohlc_data.columns:
                print(f"   ❌ Error retrieving data")
                continue
            
            # Liquidity confluence
            liquidity_analysis = self.liquidity_detector.analyze_liquidity_confluence(
                ohlc_data, tf, current_price
            )
            
            # Market structure
            market_structure = self.mt5.get_market_structure(tf, bars=100)
            
            # Swing points
            swing_points = self.mt5.get_swing_highs_lows(tf, bars=50)
            
            # Fair Value Gaps
            fvgs = self.liquidity_detector.detect_fair_value_gaps(ohlc_data, tf)
            
            # Order blocks
            order_blocks = self.liquidity_detector.detect_order_blocks(ohlc_data, tf)
            
            results = {
                'liquidity': liquidity_analysis,
                'market_structure': market_structure,
                'swing_points': swing_points,
                'fvgs': fvgs[:3] if fvgs else [],
                'order_blocks': order_blocks[:3] if order_blocks else []
            }
            
            analysis_results[tf] = results
            
            # Display results
            if display:
                self._display_timeframe_analysis(tf, results, current_price)
        
        return analysis_results
    
    def _display_timeframe_analysis(self, timeframe: str, results: Dict, current_price: float):
        """Display analysis for a single timeframe"""
        # Market structure
        ms = results['market_structure']
        print(f"   Trend: {ms.get('trend', 'N/A')}")
        print(f"   Current: {current_price:.2f}")
        
        # Liquidity zones
        liquidity = results['liquidity']
        buy_zone = liquidity.get('nearest_buy_zone')
        sell_zone = liquidity.get('nearest_sell_zone')
        
        if buy_zone:
            print(f"   🟢 Nearest Buy Zone: {buy_zone.get('center_price', 'N/A'):.2f}")
        if sell_zone:
            print(f"   🔴 Nearest Sell Zone: {sell_zone.get('center_price', 'N/A'):.2f}")
        
        # Order blocks
        obs = results.get('order_blocks', [])
        if obs:
            print(f"   📍 Order Blocks: {len(obs)} identified")
        
        # FVGs
        fvgs = results.get('fvgs', [])
        if fvgs:
            print(f"   🔓 FVGs: {len(fvgs)} identified")
    
    def start_live_monitoring(self):
        """Start live monitoring with real-time alerts"""
        print("\n" + "="*80)
        print("🚨 STARTING LIVE MONITORING".center(80))
        print("="*80)
        
        # Register alert callback
        self.alerts_system.register_alert_callback(self._on_alert)
        
        # Start monitoring
        self.alerts_system.start_monitoring(
            self.mt5,
            self.liquidity_detector,
            check_interval=self.monitoring_interval
        )
        
        self.is_running = True
        
        try:
            while self.is_running:
                time.sleep(10)
                
                # Display periodic updates
                self._display_periodic_update()
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Monitoring stopped by user")
            self.stop()
    
    def _on_alert(self, alert: Alert):
        """Callback function for new alerts"""
        print(self.alerts_system.format_alert_for_display(alert))
    
    def _display_periodic_update(self):
        """Display periodic status update"""
        print("\n" + "-"*80)
        print(f"⏰ Update: {datetime.now().strftime('%H:%M:%S')}")
        print("-"*80)
        
        price_data = self.mt5.get_current_price()
        if 'error' not in price_data:
            print(f"💰 Current Price: {price_data['bid']:.2f}")
        
        # Show latest alerts
        latest_alerts = self.alerts_system.get_latest_alerts(3)
        if latest_alerts:
            print(f"📬 Latest Alerts: {len(latest_alerts)}")
            for alert in latest_alerts:
                print(f"   • {alert.title}")
    
    def generate_report(self, output_file: str = None) -> str:
        """Generate detailed analysis report"""
        print("\n📄 Generating Report...")
        
        report = []
        report.append("=" * 80)
        report.append("GOLD LIQUIDITY ANALYSIS REPORT".center(80))
        report.append("=" * 80)
        report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Current price
        price_data = self.mt5.get_current_price()
        if 'error' not in price_data:
            report.append(f"Current Price: {price_data['bid']:.2f}")
            report.append(f"Spread: {price_data['spread']:.1f} pips\n")
        
        # Multi-timeframe analysis
        analysis = self.analyze_multi_timeframe(display=False)
        
        for tf in self.timeframes:
            if tf in analysis:
                report.append(f"\n{'='*40}")
                report.append(f"{tf} TIMEFRAME")
                report.append(f"{'='*40}\n")
                
                results = analysis[tf]
                
                # Market structure
                ms = results.get('market_structure', {})
                report.append(f"Trend: {ms.get('trend', 'N/A')}")
                
                # Liquidity zones
                liquidity = results.get('liquidity', {})
                buy_zone = liquidity.get('nearest_buy_zone')
                sell_zone = liquidity.get('nearest_sell_zone')
                
                if buy_zone:
                    report.append(f"Nearest Buy Zone: {buy_zone.get('center_price', 'N/A'):.2f}")
                if sell_zone:
                    report.append(f"Nearest Sell Zone: {sell_zone.get('center_price', 'N/A'):.2f}")
                
                # FVGs
                fvgs = results.get('fvgs', [])
                if fvgs:
                    report.append(f"\nFair Value Gaps: {len(fvgs)}")
                
                # Order blocks
                obs = results.get('order_blocks', [])
                if obs:
                    report.append(f"Order Blocks: {len(obs)}")
        
        report.append(f"\n{'='*80}\n")
        
        report_text = "\n".join(report)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_text)
            print(f"✅ Report saved to {output_file}")
        
        return report_text
    
    def stop(self):
        """Stop all monitoring and disconnect"""
        print("\n🛑 Stopping Gold Liquidity Analyzer...")
        
        self.is_running = False
        self.alerts_system.stop_monitoring()
        self.mt5.disconnect()
        
        print("✅ All systems stopped")
    
    def run_interactive_menu(self):
        """Run interactive command menu"""
        self.display_header()
        
        if not self.initialize():
            return
        
        menu_options = {
            '1': ('Analyze Current Market', self._menu_analyze),
            '2': ('Start Live Monitoring', self._menu_live_monitoring),
            '3': ('View Alert History', self._menu_alert_history),
            '4': ('Generate Report', self._menu_generate_report),
            '5': ('Display Sessions Clock', self._menu_sessions_clock),
            '0': ('Exit', None)
        }
        
        while True:
            print("\n" + "="*80)
            print("MENU".center(80))
            print("="*80)
            
            for key, (label, _) in menu_options.items():
                print(f"  {key}. {label}")
            
            choice = input("\nSelect option: ").strip()
            
            if choice == '0':
                self.stop()
                break
            
            if choice in menu_options:
                _, func = menu_options[choice]
                if func:
                    func()
            else:
                print("❌ Invalid option")
    
    def _menu_analyze(self):
        """Menu option: Analyze current market"""
        self.display_current_status()
        self.analyze_multi_timeframe()
    
    def _menu_live_monitoring(self):
        """Menu option: Start live monitoring"""
        self.start_live_monitoring()
    
    def _menu_alert_history(self):
        """Menu option: View alert history"""
        alerts = self.alerts_system.get_alert_history(limit=20)
        
        print("\n" + "-"*80)
        print(f"ALERT HISTORY ({len(alerts)} alerts)".center(80))
        print("-"*80)
        
        for alert in alerts:
            print(f"\n{alert.title}")
            print(f"  {alert.description}")
            print(f"  Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def _menu_generate_report(self):
        """Menu option: Generate report"""
        report = self.generate_report()
        print("\n" + report)
    
    def _menu_sessions_clock(self):
        """Menu option: Display sessions clock"""
        self.sessions_clock.display_live_clock(duration_seconds=10)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Gold Liquidity Analyzer')
    parser.add_argument('--mt5-path', type=str, help='Path to MetaTrader 5 terminal')
    parser.add_argument('--mode', choices=['interactive', 'monitor', 'analyze'], 
                       default='interactive', help='Operation mode')
    
    args = parser.parse_args()
    
    analyzer = GoldLiquidityAnalyzer(mt5_path=args.mt5_path)
    
    if args.mode == 'interactive':
        analyzer.run_interactive_menu()
    elif args.mode == 'monitor':
        if analyzer.initialize():
            analyzer.start_live_monitoring()
    elif args.mode == 'analyze':
        if analyzer.initialize():
            analyzer.display_header()
            analyzer.display_current_status()
            analyzer.analyze_multi_timeframe()
            analyzer.generate_report('gold_analysis_report.txt')
            analyzer.stop()

if __name__ == "__main__":
    main()
