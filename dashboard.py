"""
Web Dashboard using Streamlit
Real-time visualization of Gold Liquidity Analysis
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from mt5_integration import MT5Connection
from liquidity_analysis import LiquidityDetector
from real_time_alerts import RealTimeAlertsSystem
from config import get_config
import time

# Page configuration
st.set_page_config(
    page_title="Gold Liquidity Analyzer Dashboard",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 0rem 0rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .alert-box {
        background: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .critical-alert {
        background: #f8d7da;
        border-left: 5px solid #dc3545;
    }
    </style>
""", unsafe_allow_html=True)

class DashboardState:
    """Manage dashboard state"""
    def __init__(self):
        if 'mt5' not in st.session_state:
            st.session_state.mt5 = MT5Connection()
        if 'detector' not in st.session_state:
            st.session_state.detector = LiquidityDetector()
        if 'alerts_system' not in st.session_state:
            st.session_state.alerts_system = RealTimeAlertsSystem()
        if 'config' not in st.session_state:
            st.session_state.config = get_config()
        if 'last_update' not in st.session_state:
            st.session_state.last_update = datetime.now()

def display_header():
    """Display dashboard header"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        st.markdown("### 💎 GOLD LIQUIDITY ANALYZER")
    
    with col2:
        price_data = st.session_state.mt5.get_current_price()
        if 'error' not in price_data:
            price = price_data['bid']
            st.markdown(f"### XAU/USD: **{price:.2f}**")
        else:
            st.error("⚠️ MT5 Connection Error")
    
    with col3:
        last_update = st.session_state.last_update.strftime("%H:%M:%S")
        st.markdown(f"**Updated:** {last_update}")

def display_price_chart():
    """Display price chart with liquidity zones"""
    st.subheader("📊 Price Chart with Liquidity Zones")
    
    timeframe = st.selectbox("Select Timeframe:", ["M15", "H1", "H4", "D1"], key="tf_chart")
    
    try:
        # Get OHLC data
        ohlc_data = st.session_state.mt5.get_ohlc_data(timeframe, bars=100)
        
        if 'error' not in ohlc_data.columns:
            current_price = st.session_state.mt5.get_current_price()['bid']
            
            # Analyze liquidity
            liquidity = st.session_state.detector.analyze_liquidity_confluence(
                ohlc_data, timeframe, current_price
            )
            
            # Create candlestick chart
            fig = go.Figure(data=[go.Candlestick(
                x=ohlc_data.index,
                open=ohlc_data['open'],
                high=ohlc_data['high'],
                low=ohlc_data['low'],
                close=ohlc_data['close'],
                name='XAU/USD'
            )])
            
            # Add buy zones
            for zone in liquidity.get('buy_zones', [])[:3]:
                fig.add_hline(
                    y=zone.center_price,
                    line_dash="dash",
                    line_color="green",
                    annotation_text=f"BUY {zone.center_price:.2f}",
                    annotation_position="right"
                )
            
            # Add sell zones
            for zone in liquidity.get('sell_zones', [])[:3]:
                fig.add_hline(
                    y=zone.center_price,
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"SELL {zone.center_price:.2f}",
                    annotation_position="right"
                )
            
            # Add current price
            fig.add_hline(
                y=current_price,
                line_color="blue",
                line_width=2,
                annotation_text=f"Current: {current_price:.2f}"
            )
            
            fig.update_layout(
                title=f"XAU/USD {timeframe}",
                yaxis_title="Price (USD)",
                xaxis_title="Time",
                template="plotly_dark",
                height=500,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.error("Failed to retrieve chart data")
            
    except Exception as e:
        st.error(f"Chart Error: {e}")

def display_liquidity_analysis():
    """Display liquidity zones analysis"""
    st.subheader("🎯 Liquidity Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🟢 BUY ZONES")
        
        try:
            ohlc = st.session_state.mt5.get_ohlc_data('H4', bars=100)
            current_price = st.session_state.mt5.get_current_price()['bid']
            
            liquidity = st.session_state.detector.analyze_liquidity_confluence(
                ohlc, 'H4', current_price
            )
            
            buy_zones = liquidity.get('buy_zones', [])
            
            if buy_zones:
                df_buy = pd.DataFrame([{
                    'Level': zone.center_price,
                    'Strength': f"{zone.strength:.0f}%",
                    'Distance': f"{(current_price - zone.center_price):.2f} pips"
                } for zone in buy_zones[:5]])
                
                st.dataframe(df_buy, use_container_width=True)
            else:
                st.info("No buy zones detected")
                
        except Exception as e:
            st.error(f"Error: {e}")
    
    with col2:
        st.markdown("#### 🔴 SELL ZONES")
        
        try:
            sell_zones = liquidity.get('sell_zones', [])
            
            if sell_zones:
                df_sell = pd.DataFrame([{
                    'Level': zone.center_price,
                    'Strength': f"{zone.strength:.0f}%",
                    'Distance': f"{(zone.center_price - current_price):.2f} pips"
                } for zone in sell_zones[:5]])
                
                st.dataframe(df_sell, use_container_width=True)
            else:
                st.info("No sell zones detected")
                
        except Exception as e:
            st.error(f"Error: {e}")

def display_order_blocks():
    """Display order blocks"""
    st.subheader("📍 Order Blocks")
    
    try:
        ohlc = st.session_state.mt5.get_ohlc_data('H4', bars=100)
        order_blocks = st.session_state.detector.detect_order_blocks(ohlc, 'H4')
        
        if order_blocks:
            df_ob = pd.DataFrame([{
                'Type': ob.type.name,
                'Level': f"{ob.center_price:.2f}",
                'Bottom': f"{ob.bottom_price:.2f}",
                'Top': f"{ob.top_price:.2f}",
                'Strength': f"{ob.strength:.0f}%"
            } for ob in order_blocks[:10]])
            
            st.dataframe(df_ob, use_container_width=True)
        else:
            st.info("No order blocks detected")
            
    except Exception as e:
        st.error(f"Error: {e}")

def display_fvg_analysis():
    """Display Fair Value Gaps"""
    st.subheader("🔓 Fair Value Gaps")
    
    try:
        ohlc = st.session_state.mt5.get_ohlc_data('H1', bars=50)
        fvgs = st.session_state.detector.detect_fair_value_gaps(ohlc, 'H1')
        
        if fvgs:
            df_fvg = pd.DataFrame([{
                'Type': fvg['type'],
                'Bottom': f"{fvg['bottom_price']:.2f}",
                'Top': f"{fvg['top_price']:.2f}",
                'Gap Size': f"{fvg['gap_size']:.2f} pips",
                'Strength': f"{fvg['strength']:.0f}%"
            } for fvg in fvgs[:10]])
            
            st.dataframe(df_fvg, use_container_width=True)
        else:
            st.info("No FVGs detected")
            
    except Exception as e:
        st.error(f"Error: {e}")

def display_real_time_alerts():
    """Display real-time alerts"""
    st.subheader("🚨 Real-time Alerts")
    
    # Alert filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        alert_type = st.selectbox("Alert Type:", ["ALL", "PRICE", "LIQUIDITY", "ORDER_BLOCK", "FVG"])
    
    with col2:
        severity = st.selectbox("Severity:", ["ALL", "CRITICAL", "WARNING", "INFO"])
    
    with col3:
        limit = st.number_input("Show last N alerts:", min_value=5, max_value=50, value=10)
    
    try:
        alerts = st.session_state.alerts_system.get_alert_history(limit=limit)
        
        if alerts:
            for alert in alerts:
                # Determine alert color
                if alert.severity.value == "CRITICAL":
                    alert_class = "critical-alert"
                    icon = "🚨"
                elif alert.severity.value == "WARNING":
                    alert_class = "alert-box"
                    icon = "⚠️"
                else:
                    alert_class = ""
                    icon = "ℹ️"
                
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"{icon} **{alert.title}**")
                    st.write(alert.description)
                
                with col2:
                    st.metric("Distance", f"{abs(alert.distance_pips):.1f} pips")
                
                with col3:
                    st.metric("Confidence", f"{alert.confidence:.0f}%")
                
                st.divider()
        else:
            st.info("No alerts yet")
            
    except Exception as e:
        st.error(f"Error: {e}")

def display_metrics():
    """Display key metrics"""
    st.subheader("📈 Key Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        price_data = st.session_state.mt5.get_current_price()
        
        with col1:
            st.metric("Current Price", f"{price_data['bid']:.2f}")
        
        with col2:
            st.metric("Spread", f"{price_data['spread']:.1f} pips")
        
        with col3:
            alert_count = len(st.session_state.alerts_system.get_alert_history(limit=100))
            st.metric("Alerts Today", alert_count)
        
        with col4:
            st.metric("Uptime", "OK")
            
    except Exception as e:
        st.error(f"Error: {e}")

def display_settings_sidebar():
    """Display settings in sidebar"""
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        
        config = st.session_state.config
        
        st.markdown("#### Alert Thresholds (pips)")
        config.alerts.liquidity_zone_threshold = st.slider(
            "Liquidity Zone Alert",
            min_value=20,
            max_value=100,
            value=50,
            step=5
        )
        
        config.alerts.order_block_threshold = st.slider(
            "Order Block Alert",
            min_value=10,
            max_value=50,
            value=30,
            step=5
        )
        
        st.markdown("#### Monitoring")
        config.monitoring.check_interval = st.slider(
            "Check Interval (seconds)",
            min_value=1,
            max_value=30,
            value=5,
            step=1
        )
        
        st.markdown("#### Risk Management")
        config.risk_management.risk_percentage = st.slider(
            "Risk Per Trade (%)",
            min_value=0.1,
            max_value=5.0,
            value=1.0,
            step=0.1
        )
        
        config.risk_management.tp_to_sl_ratio = st.slider(
            "TP/SL Ratio",
            min_value=1.0,
            max_value=5.0,
            value=2.0,
            step=0.5
        )
        
        st.markdown("---")
        if st.button("💾 Save Settings"):
            st.success("✅ Settings saved!")

def main():
    """Main dashboard"""
    # Initialize state
    DashboardState()
    
    # Header
    display_header()
    
    st.markdown("---")
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Chart",
        "🎯 Analysis",
        "🚨 Alerts",
        "📈 Metrics",
        "⚙️ Settings"
    ])
    
    with tab1:
        display_price_chart()
    
    with tab2:
        display_liquidity_analysis()
        st.divider()
        display_order_blocks()
        st.divider()
        display_fvg_analysis()
    
    with tab3:
        display_real_time_alerts()
    
    with tab4:
        display_metrics()
    
    with tab5:
        display_settings_sidebar()
    
    # Sidebar settings
    with st.sidebar:
        st.markdown("---")
        if st.button("🔄 Refresh Now"):
            st.rerun()
        
        # Auto-refresh toggle
        auto_refresh = st.checkbox("Auto-refresh every 5 seconds", value=False)
        
        if auto_refresh:
            time.sleep(5)
            st.rerun()

if __name__ == "__main__":
    main()
