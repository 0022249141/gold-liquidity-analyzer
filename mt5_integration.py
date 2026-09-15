"""
MetaTrader 5 Integration Module
Connects to MT5 and retrieves real-time XAU/USD data
Supports multi-timeframe analysis
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import time

class MT5Connection:
    """
    MetaTrader 5 Connection and Data Retrieval
    """
    
    def __init__(self, path: Optional[str] = None):
        """
        Initialize MT5 connection
        
        Args:
            path: Optional path to MT5 terminal
        """
        self.connected = False
        self.symbol = "XAUUSD"
        self.timeframes = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1,
            'W1': mt5.TIMEFRAME_W1,
            'MN1': mt5.TIMEFRAME_MN1
        }
        self.connect(path)
    
    def connect(self, path: Optional[str] = None) -> bool:
        """
        Connect to MetaTrader 5
        
        Returns:
            bool: Connection status
        """
        try:
            if not mt5.initialize(path=path):
                print(f"❌ MT5 initialization failed: {mt5.last_error()}")
                return False
            
            self.connected = True
            print("✅ Connected to MetaTrader 5")
            print(f"   Terminal: {mt5.terminal_info()}")
            return True
            
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MetaTrader 5"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            print("✅ Disconnected from MetaTrader 5")
    
    def get_current_price(self) -> Dict:
        """
        Get current XAU/USD price and tick data
        
        Returns:
            dict: Current price information
        """
        try:
            tick = mt5.symbol_info_tick(self.symbol)
            if tick is None:
                return {'error': f"Failed to get tick for {self.symbol}"}
            
            return {
                'symbol': self.symbol,
                'bid': tick.bid,
                'ask': tick.ask,
                'last': tick.last,
                'volume': tick.volume,
                'time': datetime.fromtimestamp(tick.time),
                'spread': round((tick.ask - tick.bid) * 100, 2)  # in pips
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_ohlc_data(self, timeframe: str = 'H1', bars: int = 100) -> pd.DataFrame:
        """
        Retrieve OHLC data for specified timeframe
        
        Args:
            timeframe: Timeframe string (M1, M5, M15, H1, H4, D1, W1, MN1)
            bars: Number of bars to retrieve
            
        Returns:
            pd.DataFrame: OHLC data with columns [open, high, low, close, volume, time]
        """
        try:
            if timeframe not in self.timeframes:
                return pd.DataFrame({'error': f"Timeframe {timeframe} not supported"})
            
            tf = self.timeframes[timeframe]
            rates = mt5.copy_rates_from_pos(self.symbol, tf, 0, bars)
            
            if rates is None:
                return pd.DataFrame({'error': f"Failed to get rates: {mt5.last_error()}"})
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            return df[['open', 'high', 'low', 'close', 'tick_volume', 'spread']].copy()
            
        except Exception as e:
            return pd.DataFrame({'error': str(e)})
    
    def get_multi_timeframe_data(self, timeframes: List[str] = None, bars: int = 100) -> Dict[str, pd.DataFrame]:
        """
        Get OHLC data for multiple timeframes simultaneously
        
        Args:
            timeframes: List of timeframes
            bars: Number of bars per timeframe
            
        Returns:
            dict: Dictionary with timeframe as key and DataFrame as value
        """
        if timeframes is None:
            timeframes = ['M15', 'H1', 'H4', 'D1']
        
        multi_tf_data = {}
        for tf in timeframes:
            multi_tf_data[tf] = self.get_ohlc_data(tf, bars)
        
        return multi_tf_data
    
    def get_swing_highs_lows(self, timeframe: str = 'D1', bars: int = 50) -> Dict:
        """
        Identify swing highs and lows (Previous Highs/Lows)
        
        Args:
            timeframe: Timeframe for analysis
            bars: Number of bars to analyze
            
        Returns:
            dict: Dictionary with swing points
        """
        df = self.get_ohlc_data(timeframe, bars)
        
        if 'error' in df.columns:
            return {'error': df['error'].iloc[0]}
        
        # Find swing highs and lows
        swing_highs = []
        swing_lows = []
        
        for i in range(2, len(df) - 2):
            # Swing High: high[i] > high[i-1] and high[i] > high[i+1] and high[i-2] < high[i] and high[i] > high[i+2]
            if (df['high'].iloc[i] > df['high'].iloc[i-1] and 
                df['high'].iloc[i] > df['high'].iloc[i+1] and
                df['high'].iloc[i-2] < df['high'].iloc[i] and 
                df['high'].iloc[i] > df['high'].iloc[i+2]):
                swing_highs.append({
                    'time': df.index[i],
                    'price': df['high'].iloc[i],
                    'bar': i
                })
            
            # Swing Low: low[i] < low[i-1] and low[i] < low[i+1] and low[i-2] > low[i] and low[i] < low[i+2]
            if (df['low'].iloc[i] < df['low'].iloc[i-1] and 
                df['low'].iloc[i] < df['low'].iloc[i+1] and
                df['low'].iloc[i-2] > df['low'].iloc[i] and 
                df['low'].iloc[i] < df['low'].iloc[i+2]):
                swing_lows.append({
                    'time': df.index[i],
                    'price': df['low'].iloc[i],
                    'bar': i
                })
        
        return {
            'swing_highs': swing_highs[-5:],  # Last 5 swing highs
            'swing_lows': swing_lows[-5:],    # Last 5 swing lows
            'timeframe': timeframe
        }
    
    def get_market_structure(self, timeframe: str = 'H4', bars: int = 100) -> Dict:
        """
        Analyze market structure (Higher Highs, Higher Lows, etc.)
        
        Args:
            timeframe: Timeframe for analysis
            bars: Number of bars to analyze
            
        Returns:
            dict: Market structure analysis
        """
        df = self.get_ohlc_data(timeframe, bars)
        
        if 'error' in df.columns:
            return {'error': df['error'].iloc[0]}
        
        # Determine trend direction
        recent_highs = df['high'].tail(20).max()
        previous_highs = df['high'].iloc[-40:-20].max()
        recent_lows = df['low'].tail(20).min()
        previous_lows = df['low'].iloc[-40:-20].min()
        
        trend = 'UPTREND' if (recent_highs > previous_highs and recent_lows > previous_lows) else \
                'DOWNTREND' if (recent_highs < previous_highs and recent_lows < previous_lows) else \
                'RANGING'
        
        return {
            'trend': trend,
            'recent_high': recent_highs,
            'previous_high': previous_highs,
            'recent_low': recent_lows,
            'previous_low': previous_lows,
            'current_price': df['close'].iloc[-1],
            'timeframe': timeframe,
            'analysis_time': datetime.now()
        }
    
    def calculate_pivot_points(self, timeframe: str = 'D1') -> Dict:
        """
        Calculate pivot points and support/resistance levels
        
        Returns:
            dict: Pivot point levels
        """
        df = self.get_ohlc_data(timeframe, 10)
        
        if 'error' in df.columns:
            return {'error': df['error'].iloc[0]}
        
        # Use last day's data
        prev_close = df['close'].iloc[-2]
        prev_high = df['high'].iloc[-2]
        prev_low = df['low'].iloc[-2]
        
        # Calculate pivot levels
        pivot = (prev_high + prev_low + prev_close) / 3
        r1 = (2 * pivot) - prev_low
        r2 = pivot + (prev_high - prev_low)
        s1 = (2 * pivot) - prev_high
        s2 = pivot - (prev_high - prev_low)
        
        return {
            'resistance_2': r2,
            'resistance_1': r1,
            'pivot': pivot,
            'support_1': s1,
            'support_2': s2,
            'timeframe': timeframe
        }
    
    def get_volume_analysis(self, timeframe: str = 'H1', bars: int = 50) -> Dict:
        """
        Analyze volume and identify high volume areas (liquidity zones)
        
        Args:
            timeframe: Timeframe for analysis
            bars: Number of bars to analyze
            
        Returns:
            dict: Volume analysis results
        """
        df = self.get_ohlc_data(timeframe, bars)
        
        if 'error' in df.columns:
            return {'error': df['error'].iloc[0]}
        
        avg_volume = df['tick_volume'].mean()
        volume_std = df['tick_volume'].std()
        
        high_volume_bars = df[df['tick_volume'] > (avg_volume + volume_std)]
        
        return {
            'average_volume': avg_volume,
            'current_volume': df['tick_volume'].iloc[-1],
            'volume_std': volume_std,
            'high_volume_count': len(high_volume_bars),
            'volume_trend': 'INCREASING' if df['tick_volume'].iloc[-1] > avg_volume else 'DECREASING',
            'high_volume_levels': high_volume_bars[['close', 'tick_volume']].tail(5).to_dict()
        }

# Example usage
if __name__ == "__main__":
    # Connect to MT5
    mt5_conn = MT5Connection()
    
    if mt5_conn.connected:
        # Get current price
        print("\n=== CURRENT PRICE ===")
        print(mt5_conn.get_current_price())
        
        # Get multi-timeframe data
        print("\n=== MULTI-TIMEFRAME DATA ===")
        mtf_data = mt5_conn.get_multi_timeframe_data(['M15', 'H1', 'H4', 'D1'])
        for tf, df in mtf_data.items():
            if 'error' not in df.columns:
                print(f"\n{tf}:")
                print(df.tail(3))
        
        # Market structure
        print("\n=== MARKET STRUCTURE ===")
        print(mt5_conn.get_market_structure('H4'))
        
        # Swing highs/lows
        print("\n=== SWING HIGHS/LOWS ===")
        print(mt5_conn.get_swing_highs_lows('D1'))
        
        # Pivot points
        print("\n=== PIVOT POINTS ===")
        print(mt5_conn.calculate_pivot_points('D1'))
        
        # Volume analysis
        print("\n=== VOLUME ANALYSIS ===")
        print(mt5_conn.get_volume_analysis('H1'))
        
        mt5_conn.disconnect()
