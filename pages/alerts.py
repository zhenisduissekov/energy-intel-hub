import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

st.title("🚨 Energy Market Alert System")
st.markdown("Configure and monitor energy market alerts for price movements and market conditions")

# Import required modules
from utils.api_clients import EnergyDataAPI
from utils.alerts import AlertSystem
from utils.data_processor import DataProcessor

api_client = EnergyDataAPI()
alert_system = AlertSystem()
data_processor = DataProcessor()

# Initialize session state for alerts
if 'active_alerts' not in st.session_state:
    st.session_state.active_alerts = []

# Alert Configuration Section
st.subheader("⚙️ Alert Configuration")

with st.expander("Configure Alert Rules", expanded=False):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Price Movement Alerts**")
        price_threshold = st.slider(
            "Price Change Threshold (%)",
            min_value=1.0,
            max_value=20.0,
            value=5.0,
            step=0.5,
            help="Alert when price changes exceed this percentage"
        )
        
        volatility_threshold = st.slider(
            "Volatility Threshold",
            min_value=0.1,
            max_value=1.0,
            value=0.3,
            step=0.05,
            help="Alert when volatility exceeds this level"
        )
    
    with col2:
        st.markdown("**Technical Analysis Alerts**")
        rsi_overbought = st.slider(
            "RSI Overbought Level",
            min_value=60,
            max_value=90,
            value=70,
            help="Alert when RSI exceeds this level"
        )
        
        rsi_oversold = st.slider(
            "RSI Oversold Level",
            min_value=10,
            max_value=40,
            value=30,
            help="Alert when RSI falls below this level"
        )
    
    # Advanced alert options
    st.markdown("**Advanced Alert Options**")
    enable_correlation_alerts = st.checkbox("Enable Correlation Alerts", value=True)
    enable_technical_alerts = st.checkbox("Enable Technical Analysis Alerts", value=True)
    enable_ma_cross_alerts = st.checkbox("Enable Moving Average Crossover Alerts", value=True)
    
    # Update alert rules
    if st.button("Update Alert Rules"):
        new_rules = {
            'price_change_threshold': price_threshold,
            'volatility_threshold': volatility_threshold,
            'rsi_overbought': rsi_overbought,
            'rsi_oversold': rsi_oversold,
            'bollinger_band_breach': enable_technical_alerts,
            'moving_average_cross': enable_ma_cross_alerts
        }
        alert_system.update_alert_rules(new_rules)
        st.success("Alert rules updated successfully!")

# Real-time Alert Generation
st.subheader("🔴 Live Alert Monitor")

# Manual alert check
if st.button("🔍 Check for New Alerts", type="primary"):
    with st.spinner("Checking market conditions for alerts..."):
        # Load current market data
        oil_data = api_client.get_oil_prices()
        gas_data = api_client.get_natural_gas_prices()
        
        # Generate alerts
        new_alerts = alert_system.generate_all_alerts(oil_data, gas_data)
        
        # Add to session state
        st.session_state.active_alerts.extend(new_alerts)
        
        # Keep only recent alerts (last 100)
        if len(st.session_state.active_alerts) > 100:
            st.session_state.active_alerts = st.session_state.active_alerts[-100:]
        
        if new_alerts:
            st.success(f"Generated {len(new_alerts)} new alerts!")
        else:
            st.info("No new alerts generated")

# Alert Summary Dashboard
alert_summary = alert_system.get_alert_summary(hours=24)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Alerts (24h)",
        alert_summary['total_alerts']
    )

with col2:
    st.metric(
        "High Severity",
        alert_summary['high_severity'],
        delta=None
    )

with col3:
    st.metric(
        "Medium Severity",
        alert_summary['medium_severity'],
        delta=None
    )

with col4:
    st.metric(
        "Low Severity",
        alert_summary['low_severity'],
        delta=None
    )

# Recent Alerts Display
st.subheader("📋 Recent Alerts")

# Filter options
alert_filter_col1, alert_filter_col2, alert_filter_col3 = st.columns(3)

with alert_filter_col1:
    severity_filter = st.selectbox(
        "Filter by Severity",
        ["All", "High", "Medium", "Low"]
    )

with alert_filter_col2:
    commodity_filter = st.selectbox(
        "Filter by Commodity",
        ["All", "WTI", "Brent", "Natural Gas", "Oil-Gas"]
    )

with alert_filter_col3:
    alert_type_filter = st.selectbox(
        "Filter by Type",
        ["All", "price_change", "volatility", "technical_rsi", "technical_ma_cross", "correlation"]
    )

# Display alerts
if st.session_state.active_alerts or alert_system.alert_history:
    # Combine session alerts with system history
    all_alerts = st.session_state.active_alerts + alert_system.alert_history
    
    # Remove duplicates based on timestamp and message
    seen = set()
    unique_alerts = []
    for alert in all_alerts:
        alert_key = (alert['timestamp'].isoformat(), alert['message'])
        if alert_key not in seen:
            seen.add(alert_key)
            unique_alerts.append(alert)
    
    # Sort by timestamp (most recent first)
    unique_alerts.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Apply filters
    filtered_alerts = unique_alerts
    
    if severity_filter != "All":
        filtered_alerts = [a for a in filtered_alerts if a['severity'].lower() == severity_filter.lower()]
    
    if commodity_filter != "All":
        filtered_alerts = [a for a in filtered_alerts if commodity_filter.lower() in a['commodity'].lower()]
    
    if alert_type_filter != "All":
        filtered_alerts = [a for a in filtered_alerts if a['type'] == alert_type_filter]
    
    # Show only recent alerts (last 24 hours)
    cutoff_time = datetime.now() - timedelta(hours=24)
    filtered_alerts = [a for a in filtered_alerts if a['timestamp'] > cutoff_time]
    
    if filtered_alerts:
        for alert in filtered_alerts[:20]:  # Show only last 20 alerts
            severity_color = {
                'high': '🔴',
                'medium': '🟡', 
                'low': '🟢'
            }.get(alert['severity'], '⚪')
            
            timestamp_str = alert['timestamp'].strftime('%H:%M:%S')
            
            # Create alert container
            alert_container = st.container()
            with alert_container:
                col1, col2 = st.columns([1, 8])
                with col1:
                    st.write(severity_color)
                with col2:
                    st.write(f"**{timestamp_str}** - {alert['message']}")
                    st.caption(f"Type: {alert['type']} | Commodity: {alert['commodity']}")
                
                st.divider()
    else:
        st.info("No alerts match the current filters")
else:
    st.info("No alerts generated yet. Click 'Check for New Alerts' to start monitoring.")

# Alert Statistics and Trends
st.subheader("📊 Alert Analytics")

if alert_system.alert_history:
    # Prepare data for visualization
    alert_df = pd.DataFrame(alert_system.alert_history)
    alert_df['date'] = pd.to_datetime(alert_df['timestamp']).dt.date
    alert_df['hour'] = pd.to_datetime(alert_df['timestamp']).dt.hour
    
    # Filter to last 7 days
    recent_date = datetime.now().date() - timedelta(days=7)
    recent_alerts = alert_df[alert_df['date'] >= recent_date]
    
    if not recent_alerts.empty:
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            # Alerts by type
            type_counts = recent_alerts['type'].value_counts()
            fig_type = px.pie(
                values=type_counts.values,
                names=type_counts.index,
                title="Alerts by Type (Last 7 Days)"
            )
            st.plotly_chart(fig_type, use_container_width=True)
        
        with chart_col2:
            # Alerts by severity
            severity_counts = recent_alerts['severity'].value_counts()
            colors = {'high': 'red', 'medium': 'orange', 'low': 'green'}
            fig_severity = px.bar(
                x=severity_counts.index,
                y=severity_counts.values,
                title="Alerts by Severity (Last 7 Days)",
                color=severity_counts.index,
                color_discrete_map=colors
            )
            st.plotly_chart(fig_severity, use_container_width=True)
        
        # Daily alert trend
        daily_alerts = recent_alerts.groupby('date').size().reset_index(name='count')
        fig_daily = px.line(
            daily_alerts,
            x='date',
            y='count',
            title="Daily Alert Frequency (Last 7 Days)",
            markers=True
        )
        st.plotly_chart(fig_daily, use_container_width=True)

# Alert Test Section
st.subheader("🧪 Test Alert System")

with st.expander("Test Alert Generation"):
    st.markdown("Use this section to test different alert scenarios")
    
    test_col1, test_col2 = st.columns(2)
    
    with test_col1:
        test_commodity = st.selectbox("Test Commodity", ["WTI", "Brent", "Natural Gas"])
        test_scenario = st.selectbox(
            "Test Scenario",
            ["Price Spike", "Price Drop", "High Volatility", "Technical Signal"]
        )
    
    with test_col2:
        test_magnitude = st.slider("Test Magnitude", 1.0, 20.0, 10.0)
        
        if st.button("Generate Test Alert"):
            # Create a test alert
            test_alert = {
                'type': 'test',
                'severity': 'medium',
                'commodity': test_commodity,
                'message': f"TEST: {test_scenario} detected for {test_commodity} with magnitude {test_magnitude}%",
                'timestamp': datetime.now(),
                'value': test_magnitude
            }
            
            st.session_state.active_alerts.append(test_alert)
            st.success("Test alert generated!")

# Alert Export
st.subheader("📥 Export Alerts")

export_col1, export_col2 = st.columns(2)

with export_col1:
    export_period = st.selectbox("Export Period", ["Last 24 Hours", "Last 7 Days", "Last 30 Days"])

with export_col2:
    if st.button("Export Alert History"):
        # Prepare export data
        period_map = {"Last 24 Hours": 1, "Last 7 Days": 7, "Last 30 Days": 30}
        days = period_map[export_period]
        cutoff_date = datetime.now() - timedelta(days=days)
        
        export_alerts = [a for a in alert_system.alert_history if a['timestamp'] > cutoff_date]
        
        if export_alerts:
            export_df = pd.DataFrame(export_alerts)
            csv_data = export_df.to_csv(index=False)
            filename = f"energy_alerts_{export_period.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv"
            
            st.download_button(
                label="Download Alerts CSV",
                data=csv_data,
                file_name=filename,
                mime="text/csv"
            )
        else:
            st.warning("No alerts found for the selected period")

# Alert System Status
st.subheader("⚡ Alert System Status")

status_col1, status_col2, status_col3 = st.columns(3)

with status_col1:
    current_rules = alert_system.get_alert_rules()
    st.metric("Active Rules", len(current_rules))

with status_col2:
    total_history = len(alert_system.alert_history)
    st.metric("Total Alerts", total_history)

with status_col3:
    last_check = datetime.now().strftime("%H:%M:%S")
    st.metric("Last Check", last_check)

# Help and Documentation
with st.expander("📖 Alert System Help"):
    st.markdown("""
    **Alert Types:**
    - **Price Change**: Triggered when price moves beyond the configured threshold
    - **Volatility**: Triggered when market volatility exceeds normal levels
    - **Technical RSI**: Triggered when RSI indicates overbought/oversold conditions
    - **Technical MA Cross**: Triggered when moving averages cross over
    - **Technical BB**: Triggered when price breaks Bollinger Bands
    - **Correlation**: Triggered when unusual correlation patterns are detected
    
    **Severity Levels:**
    - **High**: Significant market events requiring immediate attention
    - **Medium**: Notable market movements worth monitoring
    - **Low**: Minor events for informational purposes
    
    **Best Practices:**
    - Set appropriate thresholds to avoid alert fatigue
    - Monitor correlation alerts for unusual market behavior
    - Use technical alerts for trading signal confirmation
    - Export alert history for pattern analysis
    """)
