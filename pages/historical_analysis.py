import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np

st.title("📊 Historical Energy Market Analysis")
st.markdown("Comprehensive analysis of historical energy price trends and patterns")

# Get data from the main app's API client
from utils.api_clients import EnergyDataAPI
from utils.data_processor import DataProcessor

api_client = EnergyDataAPI()
data_processor = DataProcessor()

# Time period selection
st.subheader("Analysis Parameters")
col1, col2, col3 = st.columns(3)

with col1:
    analysis_period = st.selectbox(
        "Analysis Period",
        ["30 Days", "90 Days", "1 Year", "2 Years"],
        index=2
    )

with col2:
    commodities = st.multiselect(
        "Select Commodities",
        ["WTI Crude", "Brent Crude", "Natural Gas"],
        default=["WTI Crude", "Natural Gas"]
    )

with col3:
    analysis_type = st.selectbox(
        "Analysis Type",
        ["Price Trends", "Volatility Analysis", "Correlation Analysis", "Technical Analysis"]
    )

# Convert period to days
period_map = {"30 Days": 30, "90 Days": 90, "1 Year": 365, "2 Years": 730}
days = period_map[analysis_period]

# Load historical data
@st.cache_data(ttl=1800)  # Cache for 30 minutes
def load_historical_data(days):
    oil_data = api_client.get_oil_prices()
    gas_data = api_client.get_natural_gas_prices()
    
    # Trim to requested period
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    if oil_data is not None:
        oil_data = oil_data[oil_data.index >= start_date]
    if gas_data is not None:
        gas_data = gas_data[gas_data.index >= start_date]
    
    return oil_data, gas_data

with st.spinner("Loading historical data..."):
    oil_data, gas_data = load_historical_data(days)

if analysis_type == "Price Trends":
    st.subheader("📈 Price Trend Analysis")
    
    # Create comprehensive price chart
    fig = go.Figure()
    
    if oil_data is not None and not oil_data.empty:
        if "WTI Crude" in commodities and 'WTI' in oil_data.columns:
            fig.add_trace(go.Scatter(
                x=oil_data.index,
                y=oil_data['WTI'],
                mode='lines',
                name='WTI Crude',
                line=dict(color='#FF6B35', width=2)
            ))
        
        if "Brent Crude" in commodities and 'Brent' in oil_data.columns:
            fig.add_trace(go.Scatter(
                x=oil_data.index,
                y=oil_data['Brent'],
                mode='lines',
                name='Brent Crude',
                line=dict(color='#4ECDC4', width=2)
            ))
    
    if gas_data is not None and not gas_data.empty and "Natural Gas" in commodities:
        # Scale natural gas prices to be comparable with oil
        gas_scaled = gas_data['Price'] * 15  # Rough scaling factor
        fig.add_trace(go.Scatter(
            x=gas_data.index,
            y=gas_scaled,
            mode='lines',
            name='Natural Gas (Scaled)',
            line=dict(color='#45B7D1', width=2),
            yaxis='y2'
        ))
    
    fig.update_layout(
        title=f"Energy Price Trends - {analysis_period}",
        xaxis_title="Date",
        yaxis_title="Oil Price (USD/barrel)",
        yaxis2=dict(
            title="Natural Gas Price (USD/MMBtu × 15)",
            overlaying='y',
            side='right'
        ),
        height=500,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Price statistics
    st.subheader("📊 Price Statistics")
    
    stats_data = {}
    
    if oil_data is not None and not oil_data.empty:
        for column in ['WTI', 'Brent']:
            if column in oil_data.columns and f"{column} Crude" in commodities:
                price_series = oil_data[column].dropna()
                if not price_series.empty:
                    stats_data[f"{column} Crude"] = {
                        'Current': price_series.iloc[-1],
                        'Average': price_series.mean(),
                        'Min': price_series.min(),
                        'Max': price_series.max(),
                        'Std Dev': price_series.std(),
                        'Total Return': ((price_series.iloc[-1] / price_series.iloc[0]) - 1) * 100
                    }
    
    if gas_data is not None and not gas_data.empty and "Natural Gas" in commodities:
        price_series = gas_data['Price'].dropna()
        if not price_series.empty:
            stats_data["Natural Gas"] = {
                'Current': price_series.iloc[-1],
                'Average': price_series.mean(),
                'Min': price_series.min(),
                'Max': price_series.max(),
                'Std Dev': price_series.std(),
                'Total Return': ((price_series.iloc[-1] / price_series.iloc[0]) - 1) * 100
            }
    
    if stats_data:
        stats_df = pd.DataFrame(stats_data).round(2)
        st.dataframe(stats_df, use_container_width=True)

elif analysis_type == "Volatility Analysis":
    st.subheader("📊 Volatility Analysis")
    
    # Calculate volatility for each commodity
    volatility_data = {}
    
    if oil_data is not None and not oil_data.empty:
        for column in ['WTI', 'Brent']:
            if column in oil_data.columns and f"{column} Crude" in commodities:
                price_series = oil_data[column].dropna()
                if len(price_series) > 20:
                    returns = price_series.pct_change().dropna()
                    volatility = returns.rolling(window=20).std() * np.sqrt(252) * 100
                    volatility_data[f"{column} Crude"] = volatility
    
    if gas_data is not None and not gas_data.empty and "Natural Gas" in commodities:
        price_series = gas_data['Price'].dropna()
        if len(price_series) > 20:
            returns = price_series.pct_change().dropna()
            volatility = returns.rolling(window=20).std() * np.sqrt(252) * 100
            volatility_data["Natural Gas"] = volatility
    
    if volatility_data:
        # Plot volatility
        fig_vol = go.Figure()
        
        for commodity, vol_series in volatility_data.items():
            fig_vol.add_trace(go.Scatter(
                x=vol_series.index,
                y=vol_series,
                mode='lines',
                name=commodity,
                line=dict(width=2)
            ))
        
        fig_vol.update_layout(
            title="Rolling 20-Day Annualized Volatility",
            xaxis_title="Date",
            yaxis_title="Volatility (%)",
            height=400
        )
        
        st.plotly_chart(fig_vol, use_container_width=True)
        
        # Volatility statistics
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Current Volatility Levels")
            for commodity, vol_series in volatility_data.items():
                if not vol_series.empty:
                    current_vol = vol_series.iloc[-1]
                    avg_vol = vol_series.mean()
                    st.metric(
                        commodity,
                        f"{current_vol:.1f}%",
                        f"{current_vol - avg_vol:+.1f}% vs avg"
                    )
        
        with col2:
            st.subheader("Volatility Rankings")
            vol_ranking = {}
            for commodity, vol_series in volatility_data.items():
                if not vol_series.empty:
                    vol_ranking[commodity] = vol_series.iloc[-1]
            
            sorted_vol = sorted(vol_ranking.items(), key=lambda x: x[1], reverse=True)
            for i, (commodity, vol) in enumerate(sorted_vol, 1):
                st.write(f"{i}. {commodity}: {vol:.1f}%")

elif analysis_type == "Correlation Analysis":
    st.subheader("🔗 Correlation Analysis")
    
    # Prepare data for correlation analysis
    correlation_data = {}
    
    if oil_data is not None and not oil_data.empty:
        for column in ['WTI', 'Brent']:
            if column in oil_data.columns:
                correlation_data[f"{column} Crude"] = oil_data[column]
    
    if gas_data is not None and not gas_data.empty:
        correlation_data["Natural Gas"] = gas_data['Price']
    
    if len(correlation_data) >= 2:
        # Create correlation matrix
        corr_df = pd.DataFrame(correlation_data).corr()
        
        # Plot correlation heatmap
        fig_corr = px.imshow(
            corr_df,
            text_auto=True,
            aspect="auto",
            title="Commodity Price Correlations",
            color_continuous_scale="RdBu_r"
        )
        
        st.plotly_chart(fig_corr, use_container_width=True)
        
        # Rolling correlation analysis
        if len(correlation_data) == 2:
            commodities_list = list(correlation_data.keys())
            
            # Calculate rolling correlation
            aligned_data = pd.DataFrame(correlation_data).dropna()
            if len(aligned_data) > 30:
                rolling_corr = aligned_data.iloc[:, 0].rolling(window=30).corr(aligned_data.iloc[:, 1])
                
                fig_rolling = go.Figure()
                fig_rolling.add_trace(go.Scatter(
                    x=rolling_corr.index,
                    y=rolling_corr,
                    mode='lines',
                    name=f"{commodities_list[0]} vs {commodities_list[1]}",
                    line=dict(width=2)
                ))
                
                fig_rolling.update_layout(
                    title="30-Day Rolling Correlation",
                    xaxis_title="Date",
                    yaxis_title="Correlation",
                    yaxis=dict(range=[-1, 1]),
                    height=400
                )
                
                st.plotly_chart(fig_rolling, use_container_width=True)

elif analysis_type == "Technical Analysis":
    st.subheader("📈 Technical Analysis")
    
    # Select commodity for detailed technical analysis
    tech_commodity = st.selectbox(
        "Select commodity for technical analysis:",
        ["WTI Crude", "Brent Crude", "Natural Gas"]
    )
    
    # Get appropriate data
    if tech_commodity == "WTI Crude" and oil_data is not None and 'WTI' in oil_data.columns:
        price_data = oil_data['WTI'].dropna()
    elif tech_commodity == "Brent Crude" and oil_data is not None and 'Brent' in oil_data.columns:
        price_data = oil_data['Brent'].dropna()
    elif tech_commodity == "Natural Gas" and gas_data is not None:
        price_data = gas_data['Price'].dropna()
    else:
        price_data = None
    
    if price_data is not None and len(price_data) >= 50:
        # Calculate technical indicators
        ma_data = data_processor.calculate_moving_averages(price_data)
        bollinger_bands = data_processor.calculate_bollinger_bands(price_data)
        rsi = data_processor.calculate_rsi(price_data)
        
        # Plot price with technical indicators
        fig_tech = go.Figure()
        
        # Price
        fig_tech.add_trace(go.Scatter(
            x=price_data.index,
            y=price_data,
            mode='lines',
            name='Price',
            line=dict(color='black', width=2)
        ))
        
        # Moving averages
        if ma_data is not None:
            for col in ma_data.columns:
                if col.startswith('MA_'):
                    fig_tech.add_trace(go.Scatter(
                        x=ma_data.index,
                        y=ma_data[col],
                        mode='lines',
                        name=col,
                        line=dict(width=1),
                        opacity=0.7
                    ))
        
        # Bollinger bands
        if bollinger_bands is not None:
            fig_tech.add_trace(go.Scatter(
                x=bollinger_bands['upper'].index,
                y=bollinger_bands['upper'],
                mode='lines',
                name='BB Upper',
                line=dict(color='red', dash='dash'),
                opacity=0.5
            ))
            
            fig_tech.add_trace(go.Scatter(
                x=bollinger_bands['lower'].index,
                y=bollinger_bands['lower'],
                mode='lines',
                name='BB Lower',
                line=dict(color='red', dash='dash'),
                opacity=0.5,
                fill='tonexty',
                fillcolor='rgba(255,0,0,0.1)'
            ))
        
        fig_tech.update_layout(
            title=f"{tech_commodity} - Technical Analysis",
            xaxis_title="Date",
            yaxis_title="Price",
            height=500
        )
        
        st.plotly_chart(fig_tech, use_container_width=True)
        
        # Technical indicators summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if rsi is not None:
                rsi_signal = "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral"
                st.metric("RSI", f"{rsi:.1f}", rsi_signal)
        
        with col2:
            volatility = data_processor.calculate_volatility(price_data)
            if volatility is not None:
                st.metric("Volatility", f"{volatility:.1%}")
        
        with col3:
            trend = data_processor.detect_trend(price_data)
            st.metric("Trend", trend)
        
        # Support and resistance levels
        support, resistance = data_processor.calculate_support_resistance(price_data)
        if support is not None and resistance is not None:
            st.subheader("Support & Resistance Levels")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Support Level", f"${support:.2f}")
            with col2:
                st.metric("Resistance Level", f"${resistance:.2f}")

# Export functionality
st.subheader("📥 Export Data")

export_col1, export_col2 = st.columns(2)

with export_col1:
    if st.button("Export Oil Data"):
        if oil_data is not None and not oil_data.empty:
            csv_data, filename = data_processor.export_data_csv(oil_data, "oil_prices.csv")
            if csv_data:
                st.download_button(
                    label="Download Oil Prices CSV",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv"
                )

with export_col2:
    if st.button("Export Gas Data"):
        if gas_data is not None and not gas_data.empty:
            csv_data, filename = data_processor.export_data_csv(gas_data, "gas_prices.csv")
            if csv_data:
                st.download_button(
                    label="Download Gas Prices CSV",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv"
                )
