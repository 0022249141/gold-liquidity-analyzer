"""
Backtesting Engine for Gold Liquidity Analyzer
Test trading strategies on historical data
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import json

class TradeDirection(Enum):
    """Trade direction"""
    BUY = "BUY"
    SELL = "SELL"

class TradeStatus(Enum):
    """Trade status"""
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"

@dataclass
class BacktestTrade:
    """Backtest trade record"""
    entry_time: datetime
    entry_price: float
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    direction: TradeDirection = TradeDirection.BUY
    quantity: float = 1.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    status: TradeStatus = TradeStatus.OPEN
    profit_loss: Optional[float] = None
    profit_loss_pips: Optional[float] = None
    profit_loss_percent: Optional[float] = None
    duration_hours: Optional[float] = None
    notes: str = ""
    
    def close(self, exit_price: float, exit_time: datetime):
        """Close the trade"""
        self.exit_price = exit_price
        self.exit_time = exit_time
        self.status = TradeStatus.CLOSED
        
        # Calculate P&L
        if self.direction == TradeDirection.BUY:
            pips = (exit_price - self.entry_price) * 100
            pl = (exit_price - self.entry_price) * self.quantity
        else:
            pips = (self.entry_price - exit_price) * 100
            pl = (self.entry_price - exit_price) * self.quantity
        
        self.profit_loss_pips = pips
        self.profit_loss = pl
        self.profit_loss_percent = (pips / self.entry_price) * 100
        
        # Duration
        duration = exit_time - self.entry_time
        self.duration_hours = duration.total_seconds() / 3600

@dataclass
class BacktestResult:
    """Backtest result summary"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    cancelled_trades: int = 0
    
    win_rate: float = 0.0
    profit_factor: float = 0.0
    
    total_profit_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    average_win: float = 0.0
    average_loss: float = 0.0
    
    total_pips: float = 0.0
    average_pips_per_trade: float = 0.0
    
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    
    max_drawdown: float = 0.0
    max_drawdown_percent: float = 0.0
    
    sharpe_ratio: float = 0.0
    recovery_factor: float = 0.0
    
    average_trade_duration_hours: float = 0.0
    
    trades: List[BacktestTrade] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': round(self.win_rate, 2),
            'profit_factor': round(self.profit_factor, 2),
            'total_profit_loss': round(self.total_profit_loss, 2),
            'largest_win': round(self.largest_win, 2),
            'largest_loss': round(self.largest_loss, 2),
            'average_win': round(self.average_win, 2),
            'average_loss': round(self.average_loss, 2),
            'total_pips': round(self.total_pips, 2),
            'average_pips_per_trade': round(self.average_pips_per_trade, 2),
            'max_consecutive_wins': self.max_consecutive_wins,
            'max_consecutive_losses': self.max_consecutive_losses,
            'max_drawdown': round(self.max_drawdown, 2),
            'max_drawdown_percent': round(self.max_drawdown_percent, 2),
            'sharpe_ratio': round(self.sharpe_ratio, 2),
            'recovery_factor': round(self.recovery_factor, 2),
            'average_trade_duration_hours': round(self.average_trade_duration_hours, 2)
        }

class BacktestEngine:
    """Backtesting engine for trading strategies"""
    
    def __init__(self, initial_balance: float = 10000.0):
        """Initialize backtester"""
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.trades: List[BacktestTrade] = []
        self.equity_curve = [initial_balance]
        self.ohlc_data: Optional[pd.DataFrame] = None
    
    def load_data(self, ohlc_data: pd.DataFrame):
        """Load OHLC data for backtesting"""
        self.ohlc_data = ohlc_data.sort_index()
    
    def enter_trade(self, entry_time: datetime, entry_price: float, 
                   direction: TradeDirection, quantity: float = 1.0,
                   stop_loss: float = 0.0, take_profit: float = 0.0,
                   notes: str = "") -> BacktestTrade:
        """Enter a new trade"""
        trade = BacktestTrade(
            entry_time=entry_time,
            entry_price=entry_price,
            direction=direction,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit,
            notes=notes
        )
        
        self.trades.append(trade)
        return trade
    
    def close_trade(self, trade_index: int, exit_price: float, exit_time: datetime):
        """Close a trade"""
        if 0 <= trade_index < len(self.trades):
            trade = self.trades[trade_index]
            trade.close(exit_price, exit_time)
            
            # Update balance
            self.current_balance += trade.profit_loss
            self.equity_curve.append(self.current_balance)
    
    def test_liquidity_strategy(self, ohlc_data: pd.DataFrame,
                               buy_zones: List[Dict], sell_zones: List[Dict],
                               risk_percentage: float = 1.0,
                               tp_to_sl_ratio: float = 2.0) -> BacktestResult:
        """Test liquidity-based trading strategy"""
        
        self.load_data(ohlc_data)
        self.trades = []
        self.equity_curve = [self.initial_balance]
        self.current_balance = self.initial_balance
        
        result = BacktestResult()
        open_trades = []
        
        for i in range(1, len(ohlc_data)):
            current_row = ohlc_data.iloc[i]
            current_price = current_row['close']
            current_time = current_row.name if isinstance(current_row.name, datetime) else datetime.now()
            
            # Check open trades for exits
            trades_to_remove = []
            
            for trade_idx in open_trades[:]:
                trade = self.trades[trade_idx]
                
                # Check take profit
                if trade.direction == TradeDirection.BUY:
                    if current_price >= trade.take_profit or current_price <= trade.stop_loss:
                        self.close_trade(trade_idx, current_price, current_time)
                        open_trades.remove(trade_idx)
                else:
                    if current_price <= trade.take_profit or current_price >= trade.stop_loss:
                        self.close_trade(trade_idx, current_price, current_time)
                        open_trades.remove(trade_idx)
            
            # Check for new entry signals
            for buy_zone in buy_zones:
                zone_level = buy_zone.get('center_price', 0)
                zone_range = buy_zone.get('range', 50)
                
                if abs(current_price - zone_level) < zone_range:
                    # Calculate position size
                    risk_amount = self.current_balance * (risk_percentage / 100)
                    sl_pips = zone_range * 1.5
                    quantity = risk_amount / (sl_pips / 100)
                    
                    stop_loss = current_price - (sl_pips / 100)
                    take_profit = current_price + (sl_pips / 100 * tp_to_sl_ratio)
                    
                    trade = self.enter_trade(
                        current_time, current_price,
                        TradeDirection.BUY, quantity,
                        stop_loss, take_profit,
                        f"Buy zone at {zone_level:.2f}"
                    )
                    
                    open_trades.append(len(self.trades) - 1)
                    break
            
            for sell_zone in sell_zones:
                zone_level = sell_zone.get('center_price', 0)
                zone_range = sell_zone.get('range', 50)
                
                if abs(current_price - zone_level) < zone_range:
                    # Calculate position size
                    risk_amount = self.current_balance * (risk_percentage / 100)
                    sl_pips = zone_range * 1.5
                    quantity = risk_amount / (sl_pips / 100)
                    
                    stop_loss = current_price + (sl_pips / 100)
                    take_profit = current_price - (sl_pips / 100 * tp_to_sl_ratio)
                    
                    trade = self.enter_trade(
                        current_time, current_price,
                        TradeDirection.SELL, quantity,
                        stop_loss, take_profit,
                        f"Sell zone at {zone_level:.2f}"
                    )
                    
                    open_trades.append(len(self.trades) - 1)
                    break
        
        # Close any remaining open trades
        last_row = ohlc_data.iloc[-1]
        last_price = last_row['close']
        last_time = last_row.name if isinstance(last_row.name, datetime) else datetime.now()
        
        for trade_idx in open_trades:
            self.close_trade(trade_idx, last_price, last_time)
        
        # Calculate result statistics
        result.trades = self.trades
        result.equity_curve = self.equity_curve
        result = self._calculate_statistics(result)
        
        return result
    
    def _calculate_statistics(self, result: BacktestResult) -> BacktestResult:
        """Calculate backtest statistics"""
        
        closed_trades = [t for t in result.trades if t.status == TradeStatus.CLOSED]
        
        result.total_trades = len(result.trades)
        result.winning_trades = len([t for t in closed_trades if t.profit_loss > 0])
        result.losing_trades = len([t for t in closed_trades if t.profit_loss < 0])
        result.cancelled_trades = len([t for t in result.trades if t.status == TradeStatus.CANCELLED])
        
        # Win rate
        if result.total_trades > 0:
            result.win_rate = (result.winning_trades / result.total_trades) * 100
        
        # Profit/Loss statistics
        if closed_trades:
            wins = [t.profit_loss for t in closed_trades if t.profit_loss > 0]
            losses = [t.profit_loss for t in closed_trades if t.profit_loss < 0]
            
            result.total_profit_loss = sum([t.profit_loss for t in closed_trades])
            result.total_pips = sum([t.profit_loss_pips for t in closed_trades if t.profit_loss_pips])
            
            if wins:
                result.largest_win = max(wins)
                result.average_win = sum(wins) / len(wins)
            
            if losses:
                result.largest_loss = min(losses)
                result.average_loss = sum(losses) / len(losses)
            
            if result.average_loss != 0:
                result.profit_factor = result.average_win / abs(result.average_loss)
            
            if result.total_trades > 0:
                result.average_pips_per_trade = result.total_pips / result.total_trades
        
        # Consecutive wins/losses
        result.max_consecutive_wins = self._max_consecutive(closed_trades, True)
        result.max_consecutive_losses = self._max_consecutive(closed_trades, False)
        
        # Drawdown analysis
        result.max_drawdown, result.max_drawdown_percent = self._calculate_drawdown(result.equity_curve)
        
        # Sharpe Ratio
        if len(result.equity_curve) > 1:
            returns = np.diff(result.equity_curve) / result.equity_curve[:-1]
            if len(returns) > 0 and np.std(returns) > 0:
                result.sharpe_ratio = (np.mean(returns) / np.std(returns)) * np.sqrt(252)
        
        # Recovery Factor
        if result.max_drawdown != 0:
            result.recovery_factor = result.total_profit_loss / abs(result.max_drawdown)
        
        # Average trade duration
        durations = [t.duration_hours for t in closed_trades if t.duration_hours]
        if durations:
            result.average_trade_duration_hours = sum(durations) / len(durations)
        
        return result
    
    @staticmethod
    def _max_consecutive(trades: List[BacktestTrade], winning: bool) -> int:
        """Calculate max consecutive wins or losses"""
        max_consecutive = 0
        current_consecutive = 0
        
        for trade in trades:
            is_win = trade.profit_loss > 0 if trade.profit_loss else False
            
            if (is_win and winning) or (not is_win and not winning):
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive
    
    @staticmethod
    def _calculate_drawdown(equity_curve: List[float]) -> Tuple[float, float]:
        """Calculate maximum drawdown"""
        if len(equity_curve) < 2:
            return 0.0, 0.0
        
        peak = equity_curve[0]
        max_drawdown_amount = 0.0
        max_drawdown_percent = 0.0
        
        for value in equity_curve[1:]:
            if value > peak:
                peak = value
            
            drawdown_amount = peak - value
            drawdown_percent = (drawdown_amount / peak) * 100 if peak > 0 else 0
            
            if drawdown_amount > max_drawdown_amount:
                max_drawdown_amount = drawdown_amount
                max_drawdown_percent = drawdown_percent
        
        return max_drawdown_amount, max_drawdown_percent
    
    def optimize_parameters(self, ohlc_data: pd.DataFrame,
                           buy_zones: List[Dict], sell_zones: List[Dict],
                           risk_range: Tuple[float, float] = (0.5, 3.0),
                           tp_sl_range: Tuple[float, float] = (1.0, 3.0)) -> Dict:
        """Optimize strategy parameters"""
        
        best_result = None
        best_params = {}
        best_profit = float('-inf')
        
        risk_values = np.arange(risk_range[0], risk_range[1], 0.5)
        tp_sl_values = np.arange(tp_sl_range[0], tp_sl_range[1], 0.5)
        
        results_log = []
        
        for risk in risk_values:
            for tp_sl in tp_sl_values:
                result = self.test_liquidity_strategy(
                    ohlc_data, buy_zones, sell_zones,
                    risk_percentage=risk,
                    tp_to_sl_ratio=tp_sl
                )
                
                results_log.append({
                    'risk': risk,
                    'tp_sl_ratio': tp_sl,
                    'profit': result.total_profit_loss,
                    'win_rate': result.win_rate,
                    'profit_factor': result.profit_factor
                })
                
                if result.total_profit_loss > best_profit:
                    best_profit = result.total_profit_loss
                    best_result = result
                    best_params = {
                        'risk_percentage': risk,
                        'tp_to_sl_ratio': tp_sl
                    }
        
        return {
            'best_parameters': best_params,
            'best_result': best_result.to_dict() if best_result else None,
            'optimization_log': results_log
        }
    
    def generate_report(self, result: BacktestResult, filepath: str = "backtest_report.json"):
        """Generate backtest report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': result.to_dict(),
            'equity_curve': result.equity_curve,
            'trades': [
                {
                    'entry_time': t.entry_time.isoformat(),
                    'entry_price': t.entry_price,
                    'exit_time': t.exit_time.isoformat() if t.exit_time else None,
                    'exit_price': t.exit_price,
                    'direction': t.direction.value,
                    'profit_loss': t.profit_loss,
                    'profit_loss_pips': t.profit_loss_pips,
                    'duration_hours': t.duration_hours,
                    'notes': t.notes
                }
                for t in result.trades
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)

# Example usage
if __name__ == "__main__":
    # Create sample OHLC data
    dates = pd.date_range(start='2024-01-01', periods=100, freq='H')
    ohlc_data = pd.DataFrame({
        'open': 2040 + np.random.randn(100).cumsum(),
        'high': 2042 + np.random.randn(100).cumsum(),
        'low': 2038 + np.random.randn(100).cumsum(),
        'close': 2041 + np.random.randn(100).cumsum()
    }, index=dates)
    
    # Sample zones
    buy_zones = [{'center_price': 2040, 'range': 50}]
    sell_zones = [{'center_price': 2050, 'range': 50}]
    
    # Run backtest
    engine = BacktestEngine(initial_balance=10000)
    result = engine.test_liquidity_strategy(ohlc_data, buy_zones, sell_zones)
    
    print("Backtest Summary:")
    print(json.dumps(result.to_dict(), indent=2))
    
    # Optimize parameters
    optimization = engine.optimize_parameters(ohlc_data, buy_zones, sell_zones)
    print("\nOptimization Results:")
    print(json.dumps(optimization['best_parameters'], indent=2))
