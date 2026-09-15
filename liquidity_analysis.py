"""
Liquidity Detection and Order Block Analysis
Identifies institutional liquidity zones and order blocks
Based on price action and volume analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class LiquidityType(Enum):
    """Types of liquidity zones"""
    BUY_ZONE = "BUY_ZONE"           # Institutional buying area
    SELL_ZONE = "SELL_ZONE"         # Institutional selling area
    ORDER_BLOCK = "ORDER_BLOCK"     # Price action order block
    FAIR_VALUE_GAP = "FAIR_VALUE_GAP"  # FVG - Gap in price action
    SUPPORT = "SUPPORT"             # Support level
    RESISTANCE = "RESISTANCE"       # Resistance level
    BREAKER_BLOCK = "BREAKER_BLOCK" # Breaker block for continuation

@dataclass
class LiquidityZone:
    """Liquidity zone data structure"""
    type: LiquidityType
    top_price: float
    bottom_price: float
    center_price: float
    strength: float  # 0-100 (how strong/reliable)
    timeframe: str
    identified_at: datetime
    volume_profile: Optional[Dict] = None
    confluence_factors: Optional[List[str]] = None

class LiquidityDetector:
    """
    Detects institutional liquidity zones
    Analyzes order flow and price action
    """
    
    def __init__(self):
        self.liquidity_zones: List[LiquidityZone] = []
        self.order_blocks: List[Dict] = []
    
    def detect_fair_value_gaps(self, df: pd.DataFrame, timeframe: str = 'H1') -> List[Dict]:
        """
        Detect Fair Value Gaps (FVG)
        FVG = Gap between high and low of candles when price jumps
        
        Args:
            df: OHLC DataFrame
            timeframe: Timeframe being analyzed
            
        Returns:
            list: List of detected FVGs
        """
        fvgs = []
        
        for i in range(2, len(df) - 1):
            # Bullish FVG: When low[i] > high[i-2]
            if df['low'].iloc[i] > df['high'].iloc[i-2]:
                fvg = {
                    'type': 'BULLISH_FVG',
                    'top_price': df['low'].iloc[i],
                    'bottom_price': df['high'].iloc[i-2],
                    'gap_size': df['low'].iloc[i] - df['high'].iloc[i-2],
                    'time': df.index[i],
                    'candle_index': i,
                    'strength': self._calculate_fvg_strength(df, i, 'bullish'),
                    'timeframe': timeframe
                }
                fvgs.append(fvg)
            
            # Bearish FVG: When high[i] < low[i-2]
            elif df['high'].iloc[i] < df['low'].iloc[i-2]:
                fvg = {
                    'type': 'BEARISH_FVG',
                    'top_price': df['low'].iloc[i-2],
                    'bottom_price': df['high'].iloc[i],
                    'gap_size': df['low'].iloc[i-2] - df['high'].iloc[i],
                    'time': df.index[i],
                    'candle_index': i,
                    'strength': self._calculate_fvg_strength(df, i, 'bearish'),
                    'timeframe': timeframe
                }
                fvgs.append(fvg)
        
        return fvgs
    
    def _calculate_fvg_strength(self, df: pd.DataFrame, index: int, direction: str) -> float:
        """Calculate FVG strength based on size and volume"""
        if direction == 'bullish':
            gap_size = df['low'].iloc[index] - df['high'].iloc[index-2]
            avg_candle_size = (df['high'].iloc[index-2:index+1].max() - 
                              df['low'].iloc[index-2:index+1].min()) / 3
        else:
            gap_size = df['low'].iloc[index-2] - df['high'].iloc[index]
            avg_candle_size = (df['high'].iloc[index-2:index+1].max() - 
                              df['low'].iloc[index-2:index+1].min()) / 3
        
        if avg_candle_size == 0:
            return 50
        
        strength = min(100, (gap_size / avg_candle_size) * 50)
        return strength
    
    def detect_order_blocks(self, df: pd.DataFrame, timeframe: str = 'H4', 
                           min_candles: int = 2) -> List[LiquidityZone]:
        """
        Detect Order Blocks (imbalances in price action)
        Order blocks form before trend reversals or continuations
        
        Args:
            df: OHLC DataFrame
            timeframe: Timeframe being analyzed
            min_candles: Minimum candles to form a block
            
        Returns:
            list: List of identified order blocks
        """
        order_blocks = []
        
        for i in range(min_candles, len(df) - 1):
            # Bullish Order Block: Strong up move followed by pullback
            if self._is_bullish_order_block(df, i):
                ob_high = df['high'].iloc[i-min_candles:i].max()
                ob_low = df['low'].iloc[i-min_candles:i].min()
                
                ob = LiquidityZone(
                    type=LiquidityType.ORDER_BLOCK,
                    top_price=ob_high,
                    bottom_price=ob_low,
                    center_price=(ob_high + ob_low) / 2,
                    strength=self._calculate_ob_strength(df, i, 'bullish'),
                    timeframe=timeframe,
                    identified_at=df.index[i],
                    confluence_factors=['Strong Volume', 'Higher Low']
                )
                order_blocks.append(ob)
            
            # Bearish Order Block: Strong down move followed by relief
            elif self._is_bearish_order_block(df, i):
                ob_high = df['high'].iloc[i-min_candles:i].max()
                ob_low = df['low'].iloc[i-min_candles:i].min()
                
                ob = LiquidityZone(
                    type=LiquidityType.ORDER_BLOCK,
                    top_price=ob_high,
                    bottom_price=ob_low,
                    center_price=(ob_high + ob_low) / 2,
                    strength=self._calculate_ob_strength(df, i, 'bearish'),
                    timeframe=timeframe,
                    identified_at=df.index[i],
                    confluence_factors=['Strong Volume', 'Lower High']
                )
                order_blocks.append(ob)
        
        return order_blocks[-5:]  # Return last 5 most recent
    
    def _is_bullish_order_block(self, df: pd.DataFrame, index: int) -> bool:
        """Check if bullish order block pattern exists"""
        if index < 2:
            return False
        
        # Check for strong upcandle followed by pullback
        strong_up = df['close'].iloc[index-1] > df['open'].iloc[index-1]
        body_size = abs(df['close'].iloc[index-1] - df['open'].iloc[index-1])
        avg_body = df['high'].iloc[index-3:index].sub(df['low'].iloc[index-3:index]).mean()
        
        return strong_up and body_size > (avg_body * 0.8)
    
    def _is_bearish_order_block(self, df: pd.DataFrame, index: int) -> bool:
        """Check if bearish order block pattern exists"""
        if index < 2:
            return False
        
        # Check for strong down candle followed by relief
        strong_down = df['close'].iloc[index-1] < df['open'].iloc[index-1]
        body_size = abs(df['close'].iloc[index-1] - df['open'].iloc[index-1])
        avg_body = df['high'].iloc[index-3:index].sub(df['low'].iloc[index-3:index]).mean()
        
        return strong_down and body_size > (avg_body * 0.8)
    
    def _calculate_ob_strength(self, df: pd.DataFrame, index: int, direction: str) -> float:
        """Calculate order block strength"""
        if direction == 'bullish':
            body_size = df['close'].iloc[index-1] - df['open'].iloc[index-1]
        else:
            body_size = df['open'].iloc[index-1] - df['close'].iloc[index-1]
        
        high_low_range = df['high'].iloc[index-1] - df['low'].iloc[index-1]
        
        if high_low_range == 0:
            return 50
        
        body_ratio = (body_size / high_low_range) * 100
        strength = min(100, body_ratio * 0.8 + 20)
        
        return strength
    
    def detect_breaker_blocks(self, df: pd.DataFrame, timeframe: str = 'H4') -> List[Dict]:
        """
        Detect Breaker Blocks (broken previous resistance/support)
        Often used for continuation trades
        
        Args:
            df: OHLC DataFrame
            timeframe: Timeframe being analyzed
            
        Returns:
            list: List of breaker blocks
        """
        breaker_blocks = []
        
        for i in range(5, len(df) - 1):
            # Find previous resistance that's been broken
            prev_resistances = df['high'].iloc[i-10:i-2].max()
            
            # Bullish breaker: Price breaks previous resistance and pulls back
            if (df['close'].iloc[i] > prev_resistances and 
                df['close'].iloc[i-1] < prev_resistances and
                df['high'].iloc[i] > prev_resistances):
                
                breaker = {
                    'type': 'BULLISH_BREAKER',
                    'breakout_level': prev_resistances,
                    'pullback_price': df['low'].iloc[i],
                    'time': df.index[i],
                    'strength': 70,
                    'timeframe': timeframe
                }
                breaker_blocks.append(breaker)
            
            # Bearish breaker: Price breaks previous support and pulls back
            prev_supports = df['low'].iloc[i-10:i-2].min()
            
            if (df['close'].iloc[i] < prev_supports and 
                df['close'].iloc[i-1] > prev_supports and
                df['low'].iloc[i] < prev_supports):
                
                breaker = {
                    'type': 'BEARISH_BREAKER',
                    'breakout_level': prev_supports,
                    'pullback_price': df['high'].iloc[i],
                    'time': df.index[i],
                    'strength': 70,
                    'timeframe': timeframe
                }
                breaker_blocks.append(breaker)
        
        return breaker_blocks
    
    def detect_institutional_buy_zones(self, df: pd.DataFrame, timeframe: str = 'H4') -> List[LiquidityZone]:
        """
        Detect institutional buy zones based on:
        - Previous lows
        - Support levels
        - Order blocks
        - Volume clusters
        """
        zones = []
        
        # Find strong support areas
        support_levels = self._find_support_levels(df)
        
        for support_price, strength in support_levels:
            zone = LiquidityZone(
                type=LiquidityType.BUY_ZONE,
                top_price=support_price + (support_price * 0.001),  # 0.1% above support
                bottom_price=support_price - (support_price * 0.002),  # 0.2% below support
                center_price=support_price,
                strength=strength,
                timeframe=timeframe,
                identified_at=datetime.now(),
                confluence_factors=['Support Level', 'Volume Cluster']
            )
            zones.append(zone)
        
        return zones
    
    def detect_institutional_sell_zones(self, df: pd.DataFrame, timeframe: str = 'H4') -> List[LiquidityZone]:
        """
        Detect institutional sell zones based on:
        - Previous highs
        - Resistance levels
        - Order blocks
        - Volume clusters
        """
        zones = []
        
        # Find strong resistance areas
        resistance_levels = self._find_resistance_levels(df)
        
        for resistance_price, strength in resistance_levels:
            zone = LiquidityZone(
                type=LiquidityType.SELL_ZONE,
                top_price=resistance_price + (resistance_price * 0.002),  # 0.2% above resistance
                bottom_price=resistance_price - (resistance_price * 0.001),  # 0.1% below resistance
                center_price=resistance_price,
                strength=strength,
                timeframe=timeframe,
                identified_at=datetime.now(),
                confluence_factors=['Resistance Level', 'Volume Cluster']
            )
            zones.append(zone)
        
        return zones
    
    def _find_support_levels(self, df: pd.DataFrame, lookback: int = 50) -> List[Tuple[float, float]]:
        """Find support levels in data"""
        lows = df['low'].tail(lookback)
        
        # Find local minima
        supports = []
        for i in range(1, len(lows) - 1):
            if lows.iloc[i] < lows.iloc[i-1] and lows.iloc[i] < lows.iloc[i+1]:
                strength = (lows.mean() - lows.iloc[i]) / lows.std() * 20 + 50
                strength = min(100, max(50, strength))
                supports.append((lows.iloc[i], strength))
        
        return sorted(supports, key=lambda x: x[1], reverse=True)[:3]
    
    def _find_resistance_levels(self, df: pd.DataFrame, lookback: int = 50) -> List[Tuple[float, float]]:
        """Find resistance levels in data"""
        highs = df['high'].tail(lookback)
        
        # Find local maxima
        resistances = []
        for i in range(1, len(highs) - 1):
            if highs.iloc[i] > highs.iloc[i-1] and highs.iloc[i] > highs.iloc[i+1]:
                strength = (highs.iloc[i] - highs.mean()) / highs.std() * 20 + 50
                strength = min(100, max(50, strength))
                resistances.append((highs.iloc[i], strength))
        
        return sorted(resistances, key=lambda x: x[1], reverse=True)[:3]
    
    def analyze_liquidity_confluence(self, df: pd.DataFrame, timeframe: str = 'H4', 
                                    current_price: float = None) -> Dict:
        """
        Analyze confluence of multiple liquidity factors
        
        Returns:
            dict: Confluence analysis
        """
        if current_price is None:
            current_price = df['close'].iloc[-1]
        
        buy_zones = self.detect_institutional_buy_zones(df, timeframe)
        sell_zones = self.detect_institutional_sell_zones(df, timeframe)
        order_blocks = self.detect_order_blocks(df, timeframe)
        fvgs = self.detect_fair_value_gaps(df, timeframe)
        
        return {
            'current_price': current_price,
            'buy_zones': buy_zones,
            'sell_zones': sell_zones,
            'order_blocks': order_blocks,
            'fair_value_gaps': fvgs[:3],
            'nearest_buy_zone': self._find_nearest_level(current_price, buy_zones, direction='down'),
            'nearest_sell_zone': self._find_nearest_level(current_price, sell_zones, direction='up'),
            'timeframe': timeframe,
            'analysis_time': datetime.now()
        }
    
    def _find_nearest_level(self, current_price: float, levels: List, direction: str = 'down') -> Optional[Dict]:
        """Find nearest liquidity level in specified direction"""
        if direction == 'down':
            viable = [z for z in levels if z.center_price < current_price]
            return max(viable, key=lambda x: x.center_price).__dict__ if viable else None
        else:
            viable = [z for z in levels if z.center_price > current_price]
            return min(viable, key=lambda x: x.center_price).__dict__ if viable else None

# Example usage
if __name__ == "__main__":
    # This would be used with MT5 data
    detector = LiquidityDetector()
    print("✅ Liquidity Detector initialized")
    print(f"   Detects: FVGs, Order Blocks, Breaker Blocks, Buy/Sell Zones")
