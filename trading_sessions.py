"""
Trading Sessions Clock System
Displays current time for different trading sessions (Asian, European, American)
Integrated with MetaTrader 5 data for XAU/USD
"""

from datetime import datetime, timedelta
import pytz
import time
from enum import Enum

class TradingSession(Enum):
    """Trading sessions with their characteristics"""
    ASIAN = {
        'name': 'Asian Session',
        'timezone': 'Asia/Tokyo',
        'open_time': (0, 0),      # 00:00 UTC
        'close_time': (8, 0),     # 08:00 UTC
        'liquidity': 'Medium',
        'volatility': 'Medium',
        'key_markets': ['Tokyo', 'Hong Kong', 'Singapore']
    }
    EUROPEAN = {
        'name': 'European Session',
        'timezone': 'Europe/London',
        'open_time': (8, 0),      # 08:00 UTC
        'close_time': (16, 0),    # 16:00 UTC
        'liquidity': 'High',
        'volatility': 'High',
        'key_markets': ['London', 'Frankfurt', 'Paris']
    }
    AMERICAN = {
        'name': 'American Session',
        'timezone': 'America/New_York',
        'open_time': (13, 0),     # 13:00 UTC
        'close_time': (21, 0),    # 21:00 UTC
        'liquidity': 'Very High',
        'volatility': 'Very High',
        'key_markets': ['New York', 'Chicago']
    }
    OVERLAP_EU_US = {
        'name': 'EU-US Overlap',
        'timezone': 'Europe/London',
        'open_time': (13, 0),     # 13:00 UTC
        'close_time': (16, 0),    # 16:00 UTC
        'liquidity': 'Extreme',
        'volatility': 'Extreme',
        'key_markets': ['London-New York Bridge']
    }

class TradingSessionsClock:
    """
    Real-time trading sessions clock
    Tracks multiple timeframes and market conditions
    """
    
    def __init__(self):
        self.sessions = TradingSession
        self.utc = pytz.UTC
        self.update_interval = 1  # Update every 1 second
        
    def get_current_utc_time(self):
        """Get current UTC time"""
        return datetime.now(self.utc)
    
    def get_session_time(self, session: TradingSession):
        """Get current time in specific session timezone"""
        tz = pytz.timezone(session.value['timezone'])
        return datetime.now(tz)
    
    def is_session_active(self, session: TradingSession):
        """Check if session is currently active"""
        utc_now = self.get_current_utc_time()
        utc_hour = utc_now.hour
        utc_minute = utc_now.minute
        
        open_time = session.value['open_time']
        close_time = session.value['close_time']
        
        session_open = open_time[0] + (open_time[1] / 60)
        session_close = close_time[0] + (close_time[1] / 60)
        current_time = utc_hour + (utc_minute / 60)
        
        return session_open <= current_time < session_close
    
    def get_session_status(self, session: TradingSession):
        """Get detailed session status"""
        is_active = self.is_session_active(session)
        local_time = self.get_session_time(session)
        session_data = session.value
        
        return {
            'session_name': session_data['name'],
            'timezone': session_data['timezone'],
            'local_time': local_time.strftime('%H:%M:%S'),
            'is_active': is_active,
            'liquidity': session_data['liquidity'],
            'volatility': session_data['volatility'],
            'key_markets': session_data['key_markets'],
            'status': '🟢 ACTIVE' if is_active else '🔴 CLOSED'
        }
    
    def get_all_sessions_status(self):
        """Get status of all trading sessions"""
        sessions_status = []
        for session in TradingSession:
            sessions_status.append(self.get_session_status(session))
        return sessions_status
    
    def get_next_active_session(self):
        """Find next active session"""
        utc_now = self.get_current_utc_time()
        utc_hour = utc_now.hour
        
        sessions_timeline = [
            (TradingSession.ASIAN, 0),
            (TradingSession.EUROPEAN, 8),
            (TradingSession.AMERICAN, 13),
        ]
        
        for session, open_hour in sessions_timeline:
            if utc_hour < open_hour:
                return session
        
        # If no session found today, return Asian (next day)
        return TradingSession.ASIAN
    
    def time_until_session(self, session: TradingSession):
        """Calculate time until session opens"""
        utc_now = self.get_current_utc_time()
        open_time = session.value['open_time']
        
        session_open = utc_now.replace(hour=open_time[0], minute=open_time[1], second=0, microsecond=0)
        
        if session_open <= utc_now:
            # Session already opened or closed today, calculate for next day
            session_open += timedelta(days=1)
        
        time_diff = session_open - utc_now
        hours = int(time_diff.total_seconds() // 3600)
        minutes = int((time_diff.total_seconds() % 3600) // 60)
        
        return {'hours': hours, 'minutes': minutes}
    
    def display_live_clock(self, duration_seconds=None):
        """Display live updating clock"""
        start_time = time.time()
        
        try:
            while True:
                # Clear screen (works on Unix/Linux/Mac)
                import os
                os.system('clear' if os.name == 'posix' else 'cls')
                
                print("=" * 80)
                print("🌍 GOLD TRADING SESSIONS CLOCK (XAU/USD)".center(80))
                print("=" * 80)
                
                utc_now = self.get_current_utc_time()
                print(f"\n⏰ UTC Time: {utc_now.strftime('%H:%M:%S %Z')}\n")
                
                # Display all sessions
                for status in self.get_all_sessions_status():
                    status_emoji = status['status'].split()[0]
                    print(f"{status_emoji} {status['session_name']}")
                    print(f"   Time: {status['local_time']} ({status['timezone']})")
                    print(f"   Liquidity: {status['liquidity']} | Volatility: {status['volatility']}")
                    print(f"   Markets: {', '.join(status['key_markets'])}")
                    
                    if not status['is_active']:
                        time_info = self.time_until_session(
                            [s for s in TradingSession if s.value['name'] == status['session_name']][0]
                        )
                        print(f"   ⏳ Opens in: {time_info['hours']}h {time_info['minutes']}m")
                    print()
                
                # Check next session
                next_session = self.get_next_active_session()
                print("-" * 80)
                print(f"📍 Next Session: {next_session.value['name']}")
                print("-" * 80)
                
                time.sleep(self.update_interval)
                
                # Check duration limit
                if duration_seconds and (time.time() - start_time) > duration_seconds:
                    break
                    
        except KeyboardInterrupt:
            print("\n\n✋ Clock stopped by user")

# Example usage
if __name__ == "__main__":
    clock = TradingSessionsClock()
    
    # Display single session status
    print("\n=== CURRENT SESSION STATUS ===")
    for status in clock.get_all_sessions_status():
        print(f"{status['session_name']}: {status['status']}")
    
    # Display live clock (30 seconds for demo)
    print("\n\nStarting live clock display...\n")
    clock.display_live_clock(duration_seconds=30)
