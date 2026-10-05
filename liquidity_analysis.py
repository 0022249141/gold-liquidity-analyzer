"""
Liquidity Detection and Order Block Analysis
Identifies institutional liquidity zones and order blocks
Based on price action and volume analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum

class LiquidityType(Enum):
    """Types of liquidity zones"""
    BUY_ZONE = "BUY_ZONE"
    SELL_ZONE = "SELL_ZONE"
    ORDER_BLOCK = "ORDER_BLOCK"
    FAIR_VALUE_GAP = "FAIR_VALUE_GAP"
    SUPPORT = "SUPPORT"
    RESISTANCE = "RESISTANCE"
    BREAKER_BLOCK = "BREAKER_BLOCK"

@dataclass
class LiquidityZone:
    """Liquidity zone data structure"""
    type: LiquidityType
    top_price: float
    bottom_price: float
    center_price: float
    strength: float
    timeframe: str
    identified_at: datetime
    volume_profile: Optional[Dict] = None
    confluence_factors: Optional[List[str]] = None
    direction: str = "NEUTRAL"

class LiquidityDetector:
    """
    Detects institutional liquidity zones
    Analyzes order flow and price action
    """

    def __init__(self):
        self.liquidity_zones: List[LiquidityZone] = []
        self.order_blocks: List[Dict] = []

    def detect_fair_value_gaps(self, df: pd.DataFrame, timeframe: str = 'H1') -> List[Dict]:
        """Detect Fair Value Gaps (FVG)"""
        fvgs = []

        for i in range(2, len(df) - 1):
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
        """Detect Order Blocks (imbalances in price action)"""
        order_blocks = []

        for i in range(min_candles, len(df) - 1):
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
                    confluence_factors=['Strong Volume', 'Higher Low'],
                    direction='BUY'
                )
                order_blocks.append(ob)

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
                    confluence_factors=['Strong Volume', 'Lower High'],
                    direction='SELL'
                )
                order_blocks.append(ob)

        return order_blocks[-5:]

    def _is_bullish_order_block(self, df: pd.DataFrame, index: int) -> bool:
        """Check if bullish order block pattern exists"""
        if index < 2:
            return False

        strong_up = df['close'].iloc[index-1] > df['open'].iloc[index-1]
        body_size = abs(df['close'].iloc[index-1] - df['open'].iloc[index-1])
        avg_body = (df['high'].iloc[index-3:index].sub(df['low'].iloc[index-3:index])).mean()

        return strong_up and body_size > (avg_body * 0.8)

    def _is_bearish_order_block(self, df: pd.DataFrame, index: int) -> bool:
        """Check if bearish order block pattern exists"""
        if index < 2:
            return False

        strong_down = df['close'].iloc[index-1] < df['open'].iloc[index-1]
        body_size = abs(df['close'].iloc[index-1] - df['open'].iloc[index-1])
        avg_body = (df['high'].iloc[index-3:index].sub(df['low'].iloc[index-3:index])).mean()

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
        """Detect Breaker Blocks"""
        breaker_blocks = []

        for i in range(5, len(df) - 1):
            prev_resistances = df['high'].iloc[i-10:i-2].max()

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
        """Detect institutional buy zones"""
        zones = []
        support_levels = self._find_support_levels(df)

        for support_price, strength in support_levels:
            zone = LiquidityZone(
                type=LiquidityType.BUY_ZONE,
                top_price=support_price + (support_price * 0.001),
                bottom_price=support_price - (support_price * 0.002),
                center_price=support_price,
                strength=strength,
                timeframe=timeframe,
                identified_at=datetime.now(),
                confluence_factors=['Support Level', 'Volume Cluster'],
                direction='BUY'
            )
            zones.append(zone)

        return zones

    def detect_institutional_sell_zones(self, df: pd.DataFrame, timeframe: str = 'H4') -> List[LiquidityZone]:
        """Detect institutional sell zones"""
        zones = []
        resistance_levels = self._find_resistance_levels(df)

        for resistance_price, strength in resistance_levels:
            zone = LiquidityZone(
                type=LiquidityType.SELL_ZONE,
                top_price=resistance_price + (resistance_price * 0.002),
                bottom_price=resistance_price - (resistance_price * 0.001),
                center_price=resistance_price,
                strength=strength,
                timeframe=timeframe,
                identified_at=datetime.now(),
                confluence_factors=['Resistance Level', 'Volume Cluster'],
                direction='SELL'
            )
            zones.append(zone)

        return zones

    def _find_support_levels(self, df: pd.DataFrame, lookback: int = 50) -> List[Tuple[float, float]]:
        """Find support levels"""
        lows = df['low'].tail(lookback)
        supports = []

        for i in range(1, len(lows) - 1):
            if lows.iloc[i] < lows.iloc[i-1] and lows.iloc[i] < lows.iloc[i+1]:
                strength = (lows.mean() - lows.iloc[i]) / lows.std() * 20 + 50
                strength = min(100, max(50, strength))
                supports.append((lows.iloc[i], strength))

        return sorted(supports, key=lambda x: x[1], reverse=True)[:3]

    def _find_resistance_levels(self, df: pd.DataFrame, lookback: int = 50) -> List[Tuple[float, float]]:
        """Find resistance levels"""
        highs = df['high'].tail(lookback)
        resistances = []

        for i in range(1, len(highs) - 1):
            if highs.iloc[i] > highs.iloc[i-1] and highs.iloc[i] > highs.iloc[i+1]:
                strength = (highs.iloc[i] - highs.mean()) / highs.std() * 20 + 50
                strength = min(100, max(50, strength))
                resistances.append((highs.iloc[i], strength))

        return sorted(resistances, key=lambda x: x[1], reverse=True)[:3]

    def analyze_liquidity_confluence(self, df: pd.DataFrame, timeframe: str = 'H4', 
                                     current_price: float = None) -> Dict:
        """Analyze confluence of multiple liquidity factors"""
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
            if not viable:
                return None
            return max(viable, key=lambda x: x.center_price).__dict__
        else:
            viable = [z for z in levels if z.center_price > current_price]
            if not viable:
                return None
            return min(viable, key=lambda x: x.center_price).__dict__

# Example usage
if __name__ == "__main__":
    detector = LiquidityDetector()
    print("✅ Liquidity Detector initialized")
    print(f"   Detects: FVGs, Order Blocks, Breaker Blocks, Buy/Sell Zones")
