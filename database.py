"""
Database Layer for Gold Liquidity Analyzer
SQLite database for storing alerts, analysis, and trading history
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import pandas as pd
from pathlib import Path

class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"

class AlertType(Enum):
    """Alert types"""
    PRICE = "PRICE"
    LIQUIDITY = "LIQUIDITY"
    ORDER_BLOCK = "ORDER_BLOCK"
    FVG = "FVG"
    SESSION = "SESSION"

@dataclass
class AlertRecord:
    """Alert database record"""
    id: Optional[int] = None
    timestamp: Optional[str] = None
    title: str = ""
    description: str = ""
    alert_type: str = "INFO"
    severity: str = "INFO"
    current_price: float = 0.0
    target_price: float = 0.0
    distance_pips: float = 0.0
    confidence: float = 0.0
    timeframe: str = ""
    action_suggested: str = ""
    is_active: bool = True
    is_closed: bool = False

@dataclass
class AnalysisRecord:
    """Analysis database record"""
    id: Optional[int] = None
    timestamp: Optional[str] = None
    timeframe: str = ""
    current_price: float = 0.0
    trend: str = ""
    buy_zones_count: int = 0
    sell_zones_count: int = 0
    order_blocks_count: int = 0
    fvgs_count: int = 0
    nearest_buy_zone: float = 0.0
    nearest_sell_zone: float = 0.0
    analysis_data: str = ""  # JSON string

@dataclass
class TradeRecord:
    """Trade database record"""
    id: Optional[int] = None
    timestamp: Optional[str] = None
    entry_price: float = 0.0
    entry_time: Optional[str] = None
    exit_price: Optional[float] = None
    exit_time: Optional[str] = None
    direction: str = "BUY"  # BUY or SELL
    quantity: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    profit_loss: Optional[float] = None
    profit_loss_pips: Optional[float] = None
    status: str = "OPEN"  # OPEN, CLOSED, CANCELLED
    notes: str = ""

class DatabaseManager:
    """Manage SQLite database for Gold Liquidity Analyzer"""
    
    def __init__(self, db_path: str = "gold_analyzer.db"):
        """Initialize database manager"""
        self.db_path = Path(db_path)
        self.connection = None
        self._init_db()
    
    def _init_db(self):
        """Initialize database and create tables"""
        self.connection = sqlite3.connect(str(self.db_path))
        self.connection.row_factory = sqlite3.Row
        
        cursor = self.connection.cursor()
        
        # Alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                alert_type TEXT,
                severity TEXT,
                current_price REAL,
                target_price REAL,
                distance_pips REAL,
                confidence REAL,
                timeframe TEXT,
                action_suggested TEXT,
                is_active BOOLEAN DEFAULT 1,
                is_closed BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Analysis table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                timeframe TEXT,
                current_price REAL,
                trend TEXT,
                buy_zones_count INTEGER,
                sell_zones_count INTEGER,
                order_blocks_count INTEGER,
                fvgs_count INTEGER,
                nearest_buy_zone REAL,
                nearest_sell_zone REAL,
                analysis_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Trades table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                entry_price REAL NOT NULL,
                entry_time TEXT,
                exit_price REAL,
                exit_time TEXT,
                direction TEXT,
                quantity REAL,
                stop_loss REAL,
                take_profit REAL,
                profit_loss REAL,
                profit_loss_pips REAL,
                status TEXT DEFAULT 'OPEN',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Performance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                total_trades INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                losing_trades INTEGER DEFAULT 0,
                win_rate REAL DEFAULT 0.0,
                total_profit_loss REAL DEFAULT 0.0,
                largest_win REAL DEFAULT 0.0,
                largest_loss REAL DEFAULT 0.0,
                average_win REAL DEFAULT 0.0,
                average_loss REAL DEFAULT 0.0,
                profit_factor REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_alerts_timestamp 
            ON alerts(timestamp DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_analysis_timestamp 
            ON analysis(timestamp DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_timestamp 
            ON trades(timestamp DESC)
        """)
        
        self.connection.commit()
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
    
    # ==================== ALERTS ====================
    
    def add_alert(self, alert: AlertRecord) -> int:
        """Add new alert to database"""
        alert.timestamp = alert.timestamp or datetime.now().isoformat()
        
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO alerts (
                timestamp, title, description, alert_type, severity,
                current_price, target_price, distance_pips, confidence,
                timeframe, action_suggested, is_active, is_closed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert.timestamp, alert.title, alert.description, alert.alert_type,
            alert.severity, alert.current_price, alert.target_price,
            alert.distance_pips, alert.confidence, alert.timeframe,
            alert.action_suggested, alert.is_active, alert.is_closed
        ))
        
        self.connection.commit()
        return cursor.lastrowid
    
    def get_alerts(self, limit: int = 100, severity: Optional[str] = None,
                   alert_type: Optional[str] = None, 
                   hours_back: int = 24) -> List[AlertRecord]:
        """Get alerts from database"""
        cursor = self.connection.cursor()
        
        time_filter = datetime.now() - timedelta(hours=hours_back)
        query = "SELECT * FROM alerts WHERE timestamp > ? AND is_closed = 0"
        params = [time_filter.isoformat()]
        
        if severity:
            query += " AND severity = ?"
            params.append(severity)
        
        if alert_type:
            query += " AND alert_type = ?"
            params.append(alert_type)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        alerts = []
        for row in rows:
            alert = AlertRecord(
                id=row['id'],
                timestamp=row['timestamp'],
                title=row['title'],
                description=row['description'],
                alert_type=row['alert_type'],
                severity=row['severity'],
                current_price=row['current_price'],
                target_price=row['target_price'],
                distance_pips=row['distance_pips'],
                confidence=row['confidence'],
                timeframe=row['timeframe'],
                action_suggested=row['action_suggested'],
                is_active=row['is_active'],
                is_closed=row['is_closed']
            )
            alerts.append(alert)
        
        return alerts
    
    def close_alert(self, alert_id: int):
        """Close an alert"""
        cursor = self.connection.cursor()
        cursor.execute("""
            UPDATE alerts SET is_closed = 1, is_active = 0
            WHERE id = ?
        """, (alert_id,))
        self.connection.commit()
    
    def get_alerts_statistics(self, hours_back: int = 24) -> Dict:
        """Get alert statistics"""
        cursor = self.connection.cursor()
        
        time_filter = datetime.now() - timedelta(hours=hours_back)
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_alerts,
                SUM(CASE WHEN severity = 'CRITICAL' THEN 1 ELSE 0 END) as critical_count,
                SUM(CASE WHEN severity = 'WARNING' THEN 1 ELSE 0 END) as warning_count,
                SUM(CASE WHEN severity = 'INFO' THEN 1 ELSE 0 END) as info_count,
                AVG(confidence) as avg_confidence,
                MAX(confidence) as max_confidence
            FROM alerts
            WHERE timestamp > ? AND is_closed = 0
        """, (time_filter.isoformat(),))
        
        row = cursor.fetchone()
        return {
            'total_alerts': row['total_alerts'] or 0,
            'critical': row['critical_count'] or 0,
            'warning': row['warning_count'] or 0,
            'info': row['info_count'] or 0,
            'avg_confidence': row['avg_confidence'] or 0.0,
            'max_confidence': row['max_confidence'] or 0.0
        }
    
    # ==================== ANALYSIS ====================
    
    def add_analysis(self, analysis: AnalysisRecord) -> int:
        """Add analysis record"""
        analysis.timestamp = analysis.timestamp or datetime.now().isoformat()
        
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO analysis (
                timestamp, timeframe, current_price, trend,
                buy_zones_count, sell_zones_count, order_blocks_count,
                fvgs_count, nearest_buy_zone, nearest_sell_zone,
                analysis_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            analysis.timestamp, analysis.timeframe, analysis.current_price,
            analysis.trend, analysis.buy_zones_count, analysis.sell_zones_count,
            analysis.order_blocks_count, analysis.fvgs_count,
            analysis.nearest_buy_zone, analysis.nearest_sell_zone,
            analysis.analysis_data
        ))
        
        self.connection.commit()
        return cursor.lastrowid
    
    def get_analysis_history(self, timeframe: str = "H4", 
                            limit: int = 100, hours_back: int = 24) -> List[AnalysisRecord]:
        """Get analysis history"""
        cursor = self.connection.cursor()
        
        time_filter = datetime.now() - timedelta(hours=hours_back)
        
        cursor.execute("""
            SELECT * FROM analysis
            WHERE timeframe = ? AND timestamp > ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (timeframe, time_filter.isoformat(), limit))
        
        rows = cursor.fetchall()
        
        analyses = []
        for row in rows:
            analysis = AnalysisRecord(
                id=row['id'],
                timestamp=row['timestamp'],
                timeframe=row['timeframe'],
                current_price=row['current_price'],
                trend=row['trend'],
                buy_zones_count=row['buy_zones_count'],
                sell_zones_count=row['sell_zones_count'],
                order_blocks_count=row['order_blocks_count'],
                fvgs_count=row['fvgs_count'],
                nearest_buy_zone=row['nearest_buy_zone'],
                nearest_sell_zone=row['nearest_sell_zone'],
                analysis_data=row['analysis_data']
            )
            analyses.append(analysis)
        
        return analyses
    
    # ==================== TRADES ====================
    
    def add_trade(self, trade: TradeRecord) -> int:
        """Add trade record"""
        trade.timestamp = trade.timestamp or datetime.now().isoformat()
        
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO trades (
                timestamp, entry_price, entry_time, exit_price, exit_time,
                direction, quantity, stop_loss, take_profit, profit_loss,
                profit_loss_pips, status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade.timestamp, trade.entry_price, trade.entry_time,
            trade.exit_price, trade.exit_time, trade.direction,
            trade.quantity, trade.stop_loss, trade.take_profit,
            trade.profit_loss, trade.profit_loss_pips, trade.status,
            trade.notes
        ))
        
        self.connection.commit()
        return cursor.lastrowid
    
    def close_trade(self, trade_id: int, exit_price: float, 
                   profit_loss: float, profit_loss_pips: float):
        """Close a trade"""
        cursor = self.connection.cursor()
        cursor.execute("""
            UPDATE trades
            SET status = 'CLOSED', exit_price = ?, exit_time = ?,
                profit_loss = ?, profit_loss_pips = ?
            WHERE id = ?
        """, (exit_price, datetime.now().isoformat(), 
              profit_loss, profit_loss_pips, trade_id))
        
        self.connection.commit()
    
    def get_trades(self, status: Optional[str] = None, 
                   days_back: int = 30) -> List[TradeRecord]:
        """Get trades"""
        cursor = self.connection.cursor()
        
        time_filter = datetime.now() - timedelta(days=days_back)
        
        query = "SELECT * FROM trades WHERE timestamp > ?"
        params = [time_filter.isoformat()]
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY timestamp DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        trades = []
        for row in rows:
            trade = TradeRecord(
                id=row['id'],
                timestamp=row['timestamp'],
                entry_price=row['entry_price'],
                entry_time=row['entry_time'],
                exit_price=row['exit_price'],
                exit_time=row['exit_time'],
                direction=row['direction'],
                quantity=row['quantity'],
                stop_loss=row['stop_loss'],
                take_profit=row['take_profit'],
                profit_loss=row['profit_loss'],
                profit_loss_pips=row['profit_loss_pips'],
                status=row['status'],
                notes=row['notes']
            )
            trades.append(trade)
        
        return trades
    
    def get_trade_statistics(self, days_back: int = 30) -> Dict:
        """Get trade statistics"""
        cursor = self.connection.cursor()
        
        time_filter = datetime.now() - timedelta(days=days_back)
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN status = 'CLOSED' AND profit_loss > 0 THEN 1 ELSE 0 END) as winning_trades,
                SUM(CASE WHEN status = 'CLOSED' AND profit_loss < 0 THEN 1 ELSE 0 END) as losing_trades,
                SUM(CASE WHEN status = 'CLOSED' THEN profit_loss ELSE 0 END) as total_profit_loss,
                MAX(CASE WHEN status = 'CLOSED' AND profit_loss > 0 THEN profit_loss ELSE 0 END) as largest_win,
                MIN(CASE WHEN status = 'CLOSED' AND profit_loss < 0 THEN profit_loss ELSE 0 END) as largest_loss,
                AVG(CASE WHEN status = 'CLOSED' AND profit_loss > 0 THEN profit_loss END) as avg_win,
                AVG(CASE WHEN status = 'CLOSED' AND profit_loss < 0 THEN ABS(profit_loss) END) as avg_loss
            FROM trades
            WHERE timestamp > ?
        """, (time_filter.isoformat(),))
        
        row = cursor.fetchone()
        
        total = row['total_trades'] or 0
        winning = row['winning_trades'] or 0
        losing = row['losing_trades'] or 0
        
        win_rate = (winning / total * 100) if total > 0 else 0.0
        
        avg_win = row['avg_win'] or 0.0
        avg_loss = row['avg_loss'] or 0.0
        profit_factor = (avg_win / avg_loss) if avg_loss > 0 else 0.0
        
        return {
            'total_trades': total,
            'winning_trades': winning,
            'losing_trades': losing,
            'win_rate': win_rate,
            'total_profit_loss': row['total_profit_loss'] or 0.0,
            'largest_win': row['largest_win'] or 0.0,
            'largest_loss': row['largest_loss'] or 0.0,
            'average_win': avg_win,
            'average_loss': avg_loss,
            'profit_factor': profit_factor
        }
    
    # ==================== PERFORMANCE ====================
    
    def update_daily_performance(self, date: str = None):
        """Update daily performance statistics"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        stats = self.get_trade_statistics(days_back=1)
        
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO performance (
                date, total_trades, winning_trades, losing_trades,
                win_rate, total_profit_loss, largest_win, largest_loss,
                average_win, average_loss, profit_factor
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            date,
            stats['total_trades'],
            stats['winning_trades'],
            stats['losing_trades'],
            stats['win_rate'],
            stats['total_profit_loss'],
            stats['largest_win'],
            stats['largest_loss'],
            stats['average_win'],
            stats['average_loss'],
            stats['profit_factor']
        ))
        
        self.connection.commit()
    
    def get_performance_history(self, days_back: int = 30) -> pd.DataFrame:
        """Get performance history as DataFrame"""
        cursor = self.connection.cursor()
        
        time_filter = datetime.now() - timedelta(days=days_back)
        
        cursor.execute("""
            SELECT * FROM performance
            WHERE date > ?
            ORDER BY date DESC
        """, (time_filter.strftime("%Y-%m-%d"),))
        
        rows = cursor.fetchall()
        
        data = [dict(row) for row in rows]
        
        return pd.DataFrame(data)
    
    # ==================== EXPORT ====================
    
    def export_to_csv(self, table: str, filepath: str):
        """Export table to CSV"""
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT * FROM {table}")
        
        rows = cursor.fetchall()
        
        df = pd.DataFrame([dict(row) for row in rows])
        df.to_csv(filepath, index=False)
    
    def export_alerts_to_json(self, filepath: str, hours_back: int = 24):
        """Export alerts to JSON"""
        alerts = self.get_alerts(hours_back=hours_back)
        
        data = [asdict(alert) for alert in alerts]
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    # ==================== CLEANUP ====================
    
    def cleanup_old_data(self, days_old: int = 90):
        """Delete old data from database"""
        cursor = self.connection.cursor()
        
        time_filter = datetime.now() - timedelta(days=days_old)
        
        cursor.execute("DELETE FROM alerts WHERE timestamp < ?", 
                      (time_filter.isoformat(),))
        cursor.execute("DELETE FROM analysis WHERE timestamp < ?", 
                      (time_filter.isoformat(),))
        cursor.execute("DELETE FROM trades WHERE timestamp < ?", 
                      (time_filter.isoformat(),))
        
        self.connection.commit()

# Example usage
if __name__ == "__main__":
    db = DatabaseManager()
    
    # Add sample alert
    alert = AlertRecord(
        title="Order Block Hit",
        description="Price entered order block zone",
        alert_type=AlertType.ORDER_BLOCK.value,
        severity=AlertSeverity.WARNING.value,
        current_price=2045.50,
        confidence=82.0,
        timeframe="H4"
    )
    alert_id = db.add_alert(alert)
    print(f"Alert added with ID: {alert_id}")
    
    # Get alerts
    alerts = db.get_alerts(limit=10)
    print(f"Recent alerts: {len(alerts)}")
    
    # Get statistics
    stats = db.get_alerts_statistics()
    print(f"Alert statistics: {stats}")
    
    db.close()
