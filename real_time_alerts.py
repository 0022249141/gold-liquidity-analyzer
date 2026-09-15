"""
Real-time Alerts System
Monitors price action and sends alerts when liquidity zones are approached
Multi-timeframe monitoring with customizable alert thresholds
"""

import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import queue
import json

class AlertType(Enum):
    """Types of trading alerts"""
    PRICE_ALERT = "PRICE_ALERT"
    LIQUIDITY_ZONE_ALERT = "LIQUIDITY_ZONE_ALERT"
    ORDER_BLOCK_ALERT = "ORDER_BLOCK_ALERT"
    FVG_ALERT = "FVG_ALERT"
    BREAKOUT_ALERT = "BREAKOUT_ALERT"
    SESSION_ALERT = "SESSION_ALERT"
    CONFLUENCE_ALERT = "CONFLUENCE_ALERT"
    VOLUME_ALERT = "VOLUME_ALERT"

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

@dataclass
class Alert:
    """Alert data structure"""
    type: AlertType
    severity: AlertSeverity
    title: str
    description: str
    price_level: float
    current_price: float
    distance_pips: float
    timeframe: str
    timestamp: datetime
    action_suggested: str  # BUY, SELL, WATCH
    confidence: float  # 0-100

class RealTimeAlertsSystem:
    """
    Real-time alerts monitoring system
    Tracks price action and generates alerts
    """
    
    def __init__(self, symbol: str = "XAUUSD"):
        self.symbol = symbol
        self.alerts_queue = queue.Queue()
        self.alert_history: List[Alert] = []
        self.is_running = False
        self.monitoring_thread = None
        self.alert_callbacks: List[Callable] = []
        
        # Alert thresholds (in pips)
        self.alert_thresholds = {
            'liquidity_zone': 50,      # Alert when 50 pips away
            'order_block': 30,
            'fvg': 40,
            'support_resistance': 60
        }
        
        # Session times (UTC)
        self.sessions = {
            'asian': {'start': 0, 'end': 8},
            'european': {'start': 8, 'end': 16},
            'american': {'start': 13, 'end': 21}
        }
    
    def start_monitoring(self, mt5_connection, liquidity_detector, 
                        check_interval: int = 5):
        """
        Start real-time monitoring
        
        Args:
            mt5_connection: MT5Connection instance
            liquidity_detector: LiquidityDetector instance
            check_interval: Check interval in seconds
        """
        if self.is_running:
            print("⚠️  Monitoring already running")
            return
        
        self.is_running = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(mt5_connection, liquidity_detector, check_interval),
            daemon=True
        )
        self.monitoring_thread.start()
        print("✅ Real-time monitoring started")
    
    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.is_running = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
        print("✅ Monitoring stopped")
    
    def _monitoring_loop(self, mt5_connection, liquidity_detector, check_interval: int):
        """Main monitoring loop"""
        while self.is_running:
            try:
                # Get current price
                current_data = mt5_connection.get_current_price()
                if 'error' in current_data:
                    time.sleep(check_interval)
                    continue
                
                current_price = current_data['bid']
                current_time = datetime.now()
                
                # Check multi-timeframe data
                timeframes = ['M15', 'H1', 'H4', 'D1']
                for tf in timeframes:
                    ohlc_data = mt5_connection.get_ohlc_data(tf, bars=100)
                    
                    if 'error' not in ohlc_data.columns:
                        # Detect liquidity zones
                        liquidity_analysis = liquidity_detector.analyze_liquidity_confluence(
                            ohlc_data, tf, current_price
                        )
                        
                        # Check for alerts
                        self._check_liquidity_alerts(
                            liquidity_analysis, current_price, current_time, tf
                        )
                        
                        # Check for order block alerts
                        self._check_order_block_alerts(
                            ohlc_data, current_price, current_time, tf
                        )
                        
                        # Check for FVG alerts
                        fvgs = liquidity_detector.detect_fair_value_gaps(ohlc_data, tf)
                        self._check_fvg_alerts(fvgs, current_price, current_time, tf)
                
                # Check session-based alerts
                self._check_session_alerts(current_time)
                
                # Check volume alerts
                volume_alert = self._check_volume_alerts(mt5_connection, current_time)
                if volume_alert:
                    self._add_alert(volume_alert)
                
                time.sleep(check_interval)
                
            except Exception as e:
                print(f"❌ Monitoring error: {e}")
                time.sleep(check_interval)
    
    def _check_liquidity_alerts(self, liquidity_analysis: Dict, 
                               current_price: float, timestamp: datetime, 
                               timeframe: str):
        """Check for liquidity zone alerts"""
        buy_zones = liquidity_analysis.get('buy_zones', [])
        sell_zones = liquidity_analysis.get('sell_zones', [])
        
        # Check buy zones
        for zone in buy_zones:
            distance = (current_price - zone.center_price) * 100  # Convert to pips
            
            if abs(distance) < self.alert_thresholds['liquidity_zone']:
                alert = Alert(
                    type=AlertType.LIQUIDITY_ZONE_ALERT,
                    severity=AlertSeverity.WARNING if abs(distance) < 20 else AlertSeverity.INFO,
                    title=f"🟢 BUY ZONE APPROACHING ({timeframe})",
                    description=f"Price approaching institutional buy zone at {zone.center_price:.2f}",
                    price_level=zone.center_price,
                    current_price=current_price,
                    distance_pips=distance,
                    timeframe=timeframe,
                    timestamp=timestamp,
                    action_suggested="WATCH",
                    confidence=zone.strength
                )
                self._add_alert(alert)
        
        # Check sell zones
        for zone in sell_zones:
            distance = (zone.center_price - current_price) * 100  # Convert to pips
            
            if abs(distance) < self.alert_thresholds['liquidity_zone']:
                alert = Alert(
                    type=AlertType.LIQUIDITY_ZONE_ALERT,
                    severity=AlertSeverity.WARNING if abs(distance) < 20 else AlertSeverity.INFO,
                    title=f"🔴 SELL ZONE APPROACHING ({timeframe})",
                    description=f"Price approaching institutional sell zone at {zone.center_price:.2f}",
                    price_level=zone.center_price,
                    current_price=current_price,
                    distance_pips=distance,
                    timeframe=timeframe,
                    timestamp=timestamp,
                    action_suggested="WATCH",
                    confidence=zone.strength
                )
                self._add_alert(alert)
    
    def _check_order_block_alerts(self, df, current_price: float, 
                                 timestamp: datetime, timeframe: str):
        """Check for order block alerts"""
        from liquidity_analysis import LiquidityDetector
        detector = LiquidityDetector()
        order_blocks = detector.detect_order_blocks(df, timeframe)
        
        for ob in order_blocks:
            # Check if price is entering order block zone
            if ob.bottom_price <= current_price <= ob.top_price:
                alert = Alert(
                    type=AlertType.ORDER_BLOCK_ALERT,
                    severity=AlertSeverity.CRITICAL,
                    title=f"⚡ ORDER BLOCK HIT ({timeframe})",
                    description=f"Price has entered order block zone ({ob.bottom_price:.2f} - {ob.top_price:.2f})",
                    price_level=ob.center_price,
                    current_price=current_price,
                    distance_pips=0,
                    timeframe=timeframe,
                    timestamp=timestamp,
                    action_suggested="BUY" if ob.type.name == "BULLISH_OB" else "SELL",
                    confidence=ob.strength
                )
                self._add_alert(alert)
            
            # Alert when approaching
            elif abs(current_price - ob.center_price) * 100 < self.alert_thresholds['order_block']:
                alert = Alert(
                    type=AlertType.ORDER_BLOCK_ALERT,
                    severity=AlertSeverity.WARNING,
                    title=f"📍 ORDER BLOCK NEARBY ({timeframe})",
                    description=f"Price approaching order block at {ob.center_price:.2f}",
                    price_level=ob.center_price,
                    current_price=current_price,
                    distance_pips=(ob.center_price - current_price) * 100,
                    timeframe=timeframe,
                    timestamp=timestamp,
                    action_suggested="WATCH",
                    confidence=ob.strength
                )
                self._add_alert(alert)
    
    def _check_fvg_alerts(self, fvgs: List[Dict], current_price: float, 
                         timestamp: datetime, timeframe: str):
        """Check for Fair Value Gap alerts"""
        for fvg in fvgs:
            # Check if price is in FVG
            if fvg['bottom_price'] <= current_price <= fvg['top_price']:
                alert = Alert(
                    type=AlertType.FVG_ALERT,
                    severity=AlertSeverity.CRITICAL,
                    title=f"🔓 FVG FILLED ({timeframe})",
                    description=f"Fair Value Gap has been filled at {current_price:.2f}",
                    price_level=(fvg['top_price'] + fvg['bottom_price']) / 2,
                    current_price=current_price,
                    distance_pips=0,
                    timeframe=timeframe,
                    timestamp=timestamp,
                    action_suggested="WATCH",
                    confidence=fvg['strength']
                )
                self._add_alert(alert)
    
    def _check_session_alerts(self, current_time: datetime):
        """Check for trading session change alerts"""
        utc_hour = current_time.hour
        
        # Session opening alerts
        session_opens = {
            'asian': 0,
            'european': 8,
            'american': 13
        }
        
        for session_name, open_hour in session_opens.items():
            if utc_hour == open_hour:
                alert = Alert(
                    type=AlertType.SESSION_ALERT,
                    severity=AlertSeverity.INFO,
                    title=f"🌍 {session_name.upper()} SESSION OPENED",
                    description=f"{session_name.capitalize()} trading session has started",
                    price_level=0,
                    current_price=0,
                    distance_pips=0,
                    timeframe="D1",
                    timestamp=current_time,
                    action_suggested="MONITOR",
                    confidence=100
                )
                self._add_alert(alert)
    
    def _check_volume_alerts(self, mt5_connection, timestamp: datetime) -> Optional[Alert]:
        """Check for unusual volume alerts"""
        volume_data = mt5_connection.get_volume_analysis('H1', bars=50)
        
        if 'volume_trend' in volume_data:
            if volume_data['volume_trend'] == 'INCREASING':
                current = volume_data['current_volume']
                avg = volume_data['average_volume']
                
                if current > (avg * 1.5):
                    alert = Alert(
                        type=AlertType.VOLUME_ALERT,
                        severity=AlertSeverity.WARNING,
                        title="📊 UNUSUAL VOLUME DETECTED",
                        description=f"Volume increased {(current/avg):.1f}x above average",
                        price_level=0,
                        current_price=0,
                        distance_pips=0,
                        timeframe="H1",
                        timestamp=timestamp,
                        action_suggested="WATCH",
                        confidence=80
                    )
                    return alert
        
        return None
    
    def _add_alert(self, alert: Alert):
        """Add alert to queue and history"""
        # Avoid duplicate alerts
        for recent_alert in self.alert_history[-10:]:
            if (recent_alert.type == alert.type and 
                recent_alert.price_level == alert.price_level and
                (datetime.now() - recent_alert.timestamp).seconds < 300):
                return  # Don't add duplicate
        
        self.alerts_queue.put(alert)
        self.alert_history.append(alert)
        
        # Trigger callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                print(f"❌ Callback error: {e}")
    
    def register_alert_callback(self, callback: Callable):
        """Register callback function to be called on new alerts"""
        self.alert_callbacks.append(callback)
    
    def get_latest_alerts(self, count: int = 10) -> List[Alert]:
        """Get latest alerts from queue"""
        alerts = []
        for _ in range(min(count, self.alerts_queue.qsize())):
            try:
                alerts.append(self.alerts_queue.get_nowait())
            except queue.Empty:
                break
        return alerts
    
    def get_alert_history(self, limit: int = 50, alert_type: Optional[AlertType] = None) -> List[Alert]:
        """Get alert history"""
        if alert_type:
            return [a for a in self.alert_history if a.type == alert_type][-limit:]
        return self.alert_history[-limit:]
    
    def format_alert_for_display(self, alert: Alert) -> str:
        """Format alert for console or UI display"""
        severity_emoji = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.CRITICAL: "🚨"
        }
        
        formatted = f"""
{severity_emoji.get(alert.severity, '❓')} {alert.title}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 {alert.description}
💰 Price Level: {alert.price_level:.2f}
💹 Current Price: {alert.current_price:.2f}
📏 Distance: {abs(alert.distance_pips):.1f} pips
⏰ TimeFrame: {alert.timeframe}
🎯 Action: {alert.action_suggested}
📈 Confidence: {alert.confidence:.0f}%
🕐 Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
"""
        return formatted
    
    def export_alerts_to_json(self, filepath: str):
        """Export alert history to JSON"""
        alerts_data = []
        for alert in self.alert_history:
            alerts_data.append({
                'type': alert.type.value,
                'severity': alert.severity.value,
                'title': alert.title,
                'description': alert.description,
                'price_level': alert.price_level,
                'current_price': alert.current_price,
                'distance_pips': alert.distance_pips,
                'timeframe': alert.timeframe,
                'timestamp': alert.timestamp.isoformat(),
                'action': alert.action_suggested,
                'confidence': alert.confidence
            })
        
        with open(filepath, 'w') as f:
            json.dump(alerts_data, f, indent=2)
        
        print(f"✅ Alerts exported to {filepath}")

# Example usage
if __name__ == "__main__":
    alerts_system = RealTimeAlertsSystem()
    
    # Define custom callback
    def on_alert(alert: Alert):
        print(alerts_system.format_alert_for_display(alert))
    
    alerts_system.register_alert_callback(on_alert)
    print("✅ Real-time Alerts System initialized")
