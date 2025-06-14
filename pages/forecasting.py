import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

st.title("🔮 Energy Price Forecasting")
st.markdown("AI-powered price prediction using machine learning models")

# Import required modules
from utils.api_clients import EnergyDataAPI
from utils.forecasting import EnergyForecasting
from utils.data_processor import DataProcessor

api_client = EnergyDataAPI()
forecasting = EnergyForecasting()
data_processor = DataProcessor()

# Forecasting parameters
st.subheader("Forecasting Parameters")

col1, col2, col3, col4 = st.columns(4)

with col1:
    commodity = st.selectbox(
        "Select Commodity",
        ["WTI Crude", "Brent Crude", "Natural Gas"]
    )

with col2:
    forecast_days = st.slider(
        "Forecast Period (days)",
        min_value=7,
        max_value=90,
        value=30
    )

with col3:
    model_type = st.selectbox(
        "Model Type",
        ["Random Forest", "Linear Regression"]
    )

with col4:
    training_period = st.selectbox(
        "Training Data Period",
        ["3 Months", "6 Months", "1 Year"],
        index=1
    )

# Load data for forecasting
@st.cache_data(ttl=1800)
def load_forecasting_data(period):
    period_map = {"3 Months": 90, "6 Months": 180, "1 Year": 365}
    days = period_map[period]
    
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

# Generate forecast button
if st.button("🔮 Generate Forecast", type="primary"):
    with st.spinner("Training model and generating forecast..."):
        # Load data
        oil_data, gas_data = load_forecasting_data(training_period)
        
        # Debug information
        st.write("**Debug Information:**")
        if oil_data is not None:
            st.write(f"Oil data shape: {oil_data.shape}")
            st.write(f"Oil data columns: {list(oil_data.columns)}")
            st.write(f"Oil data date range: {oil_data.index.min()} to {oil_data.index.max()}")
        else:
            st.write("Oil data: None")
            
        if gas_data is not None:
            st.write(f"Gas data shape: {gas_data.shape}")
            st.write(f"Gas data date range: {gas_data.index.min()} to {gas_data.index.max()}")
        else:
            st.write("Gas data: None")
        
        # Select appropriate price series
        if commodity == "WTI Crude" and oil_data is not None and 'WTI' in oil_data.columns:
            price_series = oil_data['WTI'].dropna()
            st.write(f"WTI price series length: {len(price_series)}")
        elif commodity == "Brent Crude" and oil_data is not None and 'Brent' in oil_data.columns:
            price_series = oil_data['Brent'].dropna()
            st.write(f"Brent price series length: {len(price_series)}")
        elif commodity == "Natural Gas" and gas_data is not None and 'Price' in gas_data.columns:
            price_series = gas_data['Price'].dropna()
            st.write(f"Natural Gas price series length: {len(price_series)}")
        else:
            price_series = None
            st.error(f"No data available for {commodity}")
        
        if price_series is not None:
            st.write(f"Selected price series has {len(price_series)} data points")
            if len(price_series) >= 30:
                # Train model
                model_type_map = {"Random Forest": "random_forest", "Linear Regression": "linear_regression"}
                model_info = forecasting.train_model(price_series, model_type_map[model_type])
                
                if model_info is not None:
                    # Generate forecasts
                    forecast_df = forecasting.forecast_prices(price_series, model_info, forecast_days)
                    
                    if forecast_df is not None:
                        # Add prediction intervals
                        forecast_df = forecasting.calculate_prediction_intervals(forecast_df)
                        
                        # Store results in session state
                        st.session_state.forecast_results = {
                            'commodity': commodity,
                            'price_series': price_series,
                            'forecast_df': forecast_df,
                            'model_info': model_info,
                            'model_type': model_type
                        }
                        
                        st.success("Forecast generated successfully!")
                    else:
                        st.error("Failed to generate forecast")
                else:
                    st.error("Failed to train forecasting model")
            else:
                st.error(f"Insufficient data for forecasting. Need at least 30 data points, but only have {len(price_series)}")
        else:
            st.error("No price series data available")

# Display forecast results
if 'forecast_results' in st.session_state:
    results = st.session_state.forecast_results
    
    st.subheader(f"📊 {results['commodity']} Price Forecast")
    
    # Model performance metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Model Type",
            results['model_type']
        )
    
    with col2:
        train_score = results['model_info'].get('train_score', 0)
        st.metric(
            "Training R²",
            f"{train_score:.3f}"
        )
    
    with col3:
        test_score = results['model_info'].get('test_score', 0)
        st.metric(
            "Test R²",
            f"{test_score:.3f}"
        )
    
    with col4:
        test_mae = results['model_info'].get('test_mae', 0)
        st.metric(
            "Test MAE",
            f"${test_mae:.2f}"
        )
    
    # Forecast visualization
    fig = go.Figure()
    
    # Historical prices
    historical_data = results['price_series'].tail(60)  # Show last 60 days
    fig.add_trace(go.Scatter(
        x=historical_data.index,
        y=historical_data.values,
        mode='lines',
        name='Historical Prices',
        line=dict(color='blue', width=2)
    ))
    
    # Forecast
    forecast_df = results['forecast_df']
    fig.add_trace(go.Scatter(
        x=forecast_df.index,
        y=forecast_df['forecast'],
        mode='lines',
        name='Forecast',
        line=dict(color='red', width=2, dash='dash')
    ))
    
    # Prediction intervals
    if 'upper_bound' in forecast_df.columns and 'lower_bound' in forecast_df.columns:
        fig.add_trace(go.Scatter(
            x=forecast_df.index,
            y=forecast_df['upper_bound'],
            mode='lines',
            name='Upper Bound (95%)',
            line=dict(color='red', width=1),
            opacity=0.3
        ))
        
        fig.add_trace(go.Scatter(
            x=forecast_df.index,
            y=forecast_df['lower_bound'],
            mode='lines',
            name='Lower Bound (95%)',
            line=dict(color='red', width=1),
            opacity=0.3,
            fill='tonexty',
            fillcolor='rgba(255,0,0,0.1)'
        ))
    
    # Add a visual separator between historical and forecast data
    # Use a shape instead of vline to avoid compatibility issues
    last_historical_date = historical_data.index[-1]
    fig.add_shape(
        type="line",
        x0=last_historical_date,
        x1=last_historical_date,
        y0=0,
        y1=1,
        yref="paper",
        line=dict(color="gray", width=2, dash="dot"),
    )
    fig.add_annotation(
        x=last_historical_date,
        y=0.9,
        yref="paper",
        text="Forecast Start",
        showarrow=False,
        font=dict(color="gray")
    )
    
    fig.update_layout(
        title=f"{results['commodity']} Price Forecast ({forecast_days} days)",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        height=500,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Forecast summary
    st.subheader("📈 Forecast Summary")
    
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    
    with summary_col1:
        current_price = results['price_series'].iloc[-1]
        forecast_end_price = forecast_df['forecast'].iloc[-1]
        price_change = forecast_end_price - current_price
        price_change_pct = (price_change / current_price) * 100
        
        st.metric(
            "Expected Price Change",
            f"${price_change:+.2f}",
            f"{price_change_pct:+.1f}%"
        )
    
    with summary_col2:
        forecast_mean = forecast_df['forecast'].mean()
        st.metric(
            "Average Forecast Price",
            f"${forecast_mean:.2f}"
        )
    
    with summary_col3:
        forecast_volatility = forecast_df['forecast'].std()
        st.metric(
            "Forecast Volatility",
            f"${forecast_volatility:.2f}"
        )
    
    # Key forecast dates and values
    st.subheader("🎯 Key Forecast Points")
    
    key_points = []
    
    # Weekly points
    for weeks in [1, 2, 4]:
        if weeks * 7 <= len(forecast_df):
            date_idx = weeks * 7 - 1
            date = forecast_df.index[date_idx]
            price = forecast_df['forecast'].iloc[date_idx]
            key_points.append({
                'Period': f"{weeks} Week{'s' if weeks > 1 else ''}",
                'Date': date.strftime('%Y-%m-%d'),
                'Forecast Price': f"${price:.2f}"
            })
    
    # End of forecast
    end_date = forecast_df.index[-1]
    end_price = forecast_df['forecast'].iloc[-1]
    key_points.append({
        'Period': f"{forecast_days} Days",
        'Date': end_date.strftime('%Y-%m-%d'),
        'Forecast Price': f"${end_price:.2f}"
    })
    
    key_points_df = pd.DataFrame(key_points)
    st.dataframe(key_points_df, use_container_width=True, hide_index=True)
    
    # Model insights
    st.subheader("🧠 Model Insights")
    
    insight_col1, insight_col2 = st.columns(2)
    
    with insight_col1:
        # Price trend analysis
        if len(forecast_df) > 1:
            trend_direction = "upward" if forecast_df['forecast'].iloc[-1] > forecast_df['forecast'].iloc[0] else "downward"
            st.info(f"**Trend Direction**: The model predicts an overall {trend_direction} trend over the forecast period.")
        
        # Volatility insight
        historical_volatility = results['price_series'].tail(30).std()
        forecast_volatility = forecast_df['forecast'].std()
        volatility_change = "increase" if forecast_volatility > historical_volatility else "decrease"
        st.info(f"**Volatility**: The model expects a {volatility_change} in price volatility compared to recent history.")
    
    with insight_col2:
        # Confidence assessment
        test_score = results['model_info'].get('test_score', 0)
        if test_score > 0.7:
            confidence = "High"
        elif test_score > 0.4:
            confidence = "Medium"
        else:
            confidence = "Low"
        
        st.info(f"**Model Confidence**: {confidence} (R² = {test_score:.3f})")
        
        # Risk assessment
        if 'upper_bound' in forecast_df.columns and 'lower_bound' in forecast_df.columns:
            avg_interval_width = (forecast_df['upper_bound'] - forecast_df['lower_bound']).mean()
            risk_level = "High" if avg_interval_width > current_price * 0.2 else "Medium" if avg_interval_width > current_price * 0.1 else "Low"
            st.info(f"**Price Risk**: {risk_level} uncertainty in forecasts")
    
    # Export forecast
    st.subheader("📥 Export Forecast")
    
    if st.button("Export Forecast Data"):
        # Combine historical and forecast data
        export_data = pd.DataFrame({
            'Date': list(historical_data.index) + list(forecast_df.index),
            'Type': ['Historical'] * len(historical_data) + ['Forecast'] * len(forecast_df),
            'Price': list(historical_data.values) + list(forecast_df['forecast'])
        })
        
        if 'upper_bound' in forecast_df.columns:
            export_data.loc[export_data['Type'] == 'Forecast', 'Upper_Bound'] = forecast_df['upper_bound'].values
            export_data.loc[export_data['Type'] == 'Forecast', 'Lower_Bound'] = forecast_df['lower_bound'].values
        
        csv_data = export_data.to_csv(index=False)
        filename = f"{results['commodity'].lower().replace(' ', '_')}_forecast_{datetime.now().strftime('%Y%m%d')}.csv"
        
        st.download_button(
            label="Download Forecast CSV",
            data=csv_data,
            file_name=filename,
            mime="text/csv"
        )

# Model comparison section
st.subheader("🔬 Model Comparison")

if st.checkbox("Show Model Comparison"):
    st.markdown("""
    **Random Forest Model:**
    - Better for capturing non-linear patterns
    - Handles multiple features well
    - More robust to outliers
    - Generally higher accuracy for commodity prices
    
    **Linear Regression Model:**
    - Simpler and faster to train
    - More interpretable results
    - Better for linear trends
    - Lower computational requirements
    
    **Recommendation**: Random Forest is typically better for energy price forecasting due to the complex, non-linear nature of commodity markets.
    """)

# Disclaimer
st.subheader("⚠️ Important Disclaimer")
st.warning("""
**Investment Disclaimer**: These forecasts are for informational purposes only and should not be considered as investment advice. 
Energy commodity prices are influenced by numerous unpredictable factors including geopolitical events, weather, economic conditions, 
and market sentiment. Past performance does not guarantee future results. Always consult with qualified financial professionals 
before making investment decisions.
""")
