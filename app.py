import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from utils.api_clients import EnergyDataAPI
from utils.data_processor import DataProcessor
from utils.alerts import AlertSystem

# Configure page settings
st.set_page_config(
    page_title="Houston Energy Market Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'data_cache' not in st.session_state:
    st.session_state.data_cache = {}
if 'last_update' not in st.session_state:
    st.session_state.last_update = None
if 'alerts' not in st.session_state:
    st.session_state.alerts = []

# Initialize API clients and processors
@st.cache_resource
def init_services():
    api_client = EnergyDataAPI()
    data_processor = DataProcessor()
    alert_system = AlertSystem()
    return api_client, data_processor, alert_system

api_client, data_processor, alert_system = init_services()

# Main navigation
st.sidebar.title("🛢️ Houston Energy Analytics")
st.sidebar.markdown("---")

page = st.sidebar.selectbox(
    "Navigate to:",
    ["Real-Time Dashboard", "Historical Analysis", "Price Forecasting", "Alert Management"]
)

# Auto-refresh toggle
auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=False)
if auto_refresh:
    time.sleep(30)
    st.rerun()

# Manual refresh button
if st.sidebar.button("🔄 Refresh Data"):
    st.session_state.data_cache.clear()
    st.rerun()

# Data freshness indicator
if st.session_state.last_update:
    minutes_ago = (datetime.now() - st.session_state.last_update).seconds // 60
    if minutes_ago < 5:
        st.sidebar.success(f"Data fresh ({minutes_ago}m ago)")
    elif minutes_ago < 30:
        st.sidebar.warning(f"Data aging ({minutes_ago}m ago)")
    else:
        st.sidebar.error(f"Data stale ({minutes_ago}m ago)")

# Page routing
if page == "Real-Time Dashboard":
    # Main dashboard content
    st.title("⚡ Houston Energy Market Dashboard")
    st.markdown("Real-time energy commodity prices and market insights")
    
    # Test if this content shows up
    st.success("Dashboard is loading successfully!")
    
    # Initialize variables
    wti_price = brent_price = gas_price = None
    oil_data = gas_data = renewable_data = None
    
    # Get real-time data with better error handling
    try:
        st.info("Attempting to load market data...")
        
        # Oil prices
        oil_data = api_client.get_oil_prices()
        if oil_data is not None and not oil_data.empty:
            st.success(f"Oil data loaded successfully! Shape: {oil_data.shape}")
            if 'WTI' in oil_data.columns:
                wti_price = oil_data['WTI'].iloc[-1]
            if 'Brent' in oil_data.columns:
                brent_price = oil_data['Brent'].iloc[-1]
        else:
            st.warning("No oil price data available from Yahoo Finance")
        
        # Natural gas prices
        gas_data = api_client.get_natural_gas_prices()
        if gas_data is not None and not gas_data.empty and 'Price' in gas_data.columns:
            gas_price = gas_data['Price'].iloc[-1]
            st.success("Natural gas data loaded successfully!")
        else:
            st.warning("No natural gas data available")
        
        # Renewable energy data
        renewable_data = api_client.get_renewable_energy_data()
        if renewable_data is not None:
            st.success("Renewable energy data loaded")
        
        st.session_state.last_update = datetime.now()
        
    except Exception as e:
        st.error(f"Error loading energy market data: {str(e)}")
        st.info("Would you like to provide API keys for premium data sources like EIA, Alpha Vantage, or FRED for more reliable data access?")
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if wti_price is not None:
            st.metric(
                label="WTI Crude Oil",
                value=f"${wti_price:.2f}/bbl",
                delta=None  # Could calculate delta if historical data available
            )
        else:
            st.metric("WTI Crude Oil", "No Data", "")
    
    with col2:
        if brent_price is not None:
            st.metric(
                label="Brent Crude Oil",
                value=f"${brent_price:.2f}/bbl",
                delta=None
            )
        else:
            st.metric("Brent Crude Oil", "No Data", "")
    
    with col3:
        if gas_price is not None:
            st.metric(
                label="Natural Gas",
                value=f"${gas_price:.2f}/MMBtu",
                delta=None
            )
        else:
            st.metric("Natural Gas", "No Data", "")
    
    with col4:
        if renewable_data is not None and not renewable_data.empty:
            renewable_capacity = renewable_data['Capacity'].sum() if 'Capacity' in renewable_data.columns else 0
            st.metric(
                label="Renewable Capacity",
                value=f"{renewable_capacity:.1f} GW",
                delta=None
            )
        else:
            st.metric("Renewable Capacity", "No Data", "")
    
    # Price charts
    st.subheader("📈 Price Trends")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        if oil_data is not None and not oil_data.empty:
            fig_oil = go.Figure()
            if 'WTI' in oil_data.columns:
                fig_oil.add_trace(go.Scatter(
                    x=oil_data.index,
                    y=oil_data['WTI'],
                    mode='lines',
                    name='WTI Crude',
                    line=dict(color='#FF6B35')
                ))
            if 'Brent' in oil_data.columns:
                fig_oil.add_trace(go.Scatter(
                    x=oil_data.index,
                    y=oil_data['Brent'],
                    mode='lines',
                    name='Brent Crude',
                    line=dict(color='#4ECDC4')
                ))
            fig_oil.update_layout(
                title="Oil Prices ($/barrel)",
                xaxis_title="Date",
                yaxis_title="Price (USD)",
                height=300
            )
            st.plotly_chart(fig_oil, use_container_width=True)
        else:
            st.info("Oil price data not available")
    
    with chart_col2:
        if gas_data is not None and not gas_data.empty:
            fig_gas = go.Figure()
            fig_gas.add_trace(go.Scatter(
                x=gas_data.index,
                y=gas_data['Price'],
                mode='lines',
                name='Natural Gas',
                line=dict(color='#45B7D1')
            ))
            fig_gas.update_layout(
                title="Natural Gas Prices ($/MMBtu)",
                xaxis_title="Date",
                yaxis_title="Price (USD)",
                height=300
            )
            st.plotly_chart(fig_gas, use_container_width=True)
        else:
            st.info("Natural gas price data not available")
    
    # Market status and alerts
    st.subheader("🚨 Market Alerts")
    if st.session_state.alerts:
        for alert in st.session_state.alerts[-5:]:  # Show last 5 alerts
            st.warning(f"**{alert['timestamp']}**: {alert['message']}")
    else:
        st.info("No active alerts")
    
    # Houston-specific information
    st.subheader("🏙️ Houston Energy Market Focus")
    
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.info("""
        **Houston Energy Hub**
        - Major oil refining center
        - Key pipeline infrastructure
        - Energy trading hub
        - Renewable energy investments
        """)
    
    with info_col2:
        st.info("""
        **Market Benchmarks**
        - WTI Cushing delivery point
        - Houston Ship Channel pricing
        - Gulf Coast refinery margins
        - Texas renewable capacity
        """)

elif page == "Historical Analysis":
    exec(open('pages/historical_analysis.py').read())

elif page == "Price Forecasting":
    exec(open('pages/forecasting.py').read())

elif page == "Alert Management":
    exec(open('pages/alerts.py').read())
