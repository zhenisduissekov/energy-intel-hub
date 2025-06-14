import requests
import pandas as pd
import yfinance as yf
import os
from datetime import datetime, timedelta
import streamlit as st

class EnergyDataAPI:
    """Client for accessing various energy market APIs"""
    
    def __init__(self):
        # API keys from environment variables
        self.eia_api_key = os.getenv("EIA_API_KEY", "")
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
        self.fred_api_key = os.getenv("FRED_API_KEY", "")
        
        # Base URLs
        self.eia_base_url = "https://api.eia.gov/v2"
        self.alpha_vantage_base_url = "https://www.alphavantage.co/query"
        self.fred_base_url = "https://api.stlouisfed.org/fred"
        
        # Cache duration in minutes
        self.cache_duration = 30
    
    def _make_request(self, url, params=None, timeout=10):
        """Make HTTP request with error handling"""
        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API request failed: {str(e)}")
            return None
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            return None
    
    def get_oil_prices(self):
        """Get WTI and Brent crude oil prices"""
        try:
            # Use Yahoo Finance for oil prices as it's more reliable and free
            wti_ticker = "CL=F"  # WTI Crude Oil Futures
            brent_ticker = "BZ=F"  # Brent Crude Oil Futures
            
            # Get more data for forecasting - extend to 1 year to ensure enough data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            wti_data = yf.download(wti_ticker, start=start_date, end=end_date, progress=False)
            brent_data = yf.download(brent_ticker, start=start_date, end=end_date, progress=False)
            
            if (wti_data is None or wti_data.empty) and (brent_data is None or brent_data.empty):
                return None
            
            # Combine data
            oil_df = pd.DataFrame()
            if wti_data is not None and not wti_data.empty:
                oil_df['WTI'] = wti_data['Close']
            if brent_data is not None and not brent_data.empty:
                oil_df['Brent'] = brent_data['Close']
            
            return oil_df
            
        except Exception as e:
            st.error(f"Error fetching oil prices: {str(e)}")
            return None
    
    def get_natural_gas_prices(self):
        """Get natural gas prices"""
        try:
            # Use Yahoo Finance for natural gas futures
            ng_ticker = "NG=F"  # Natural Gas Futures
            
            # Get more data for forecasting - extend to 1 year
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            ng_data = yf.download(ng_ticker, start=start_date, end=end_date, progress=False)
            
            if ng_data is None or ng_data.empty:
                return None
            
            ng_df = pd.DataFrame()
            ng_df['Price'] = ng_data['Close']
            
            return ng_df
            
        except Exception as e:
            st.error(f"Error fetching natural gas prices: {str(e)}")
            return None
    
    def get_energy_stocks(self):
        """Get energy sector stock prices"""
        try:
            # Major energy companies
            energy_tickers = ["XOM", "CVX", "COP", "EOG", "SLB"]  # ExxonMobil, Chevron, ConocoPhillips, EOG Resources, Schlumberger
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            stock_data = {}
            for ticker in energy_tickers:
                try:
                    data = yf.download(ticker, start=start_date, end=end_date, progress=False)
                    if not data.empty:
                        stock_data[ticker] = data['Close']
                except:
                    continue
            
            if not stock_data:
                return None
            
            return pd.DataFrame(stock_data)
            
        except Exception as e:
            st.error(f"Error fetching energy stocks: {str(e)}")
            return None
    
    def get_renewable_energy_data(self):
        """Get renewable energy data using EIA API if available"""
        if not self.eia_api_key or self.eia_api_key == "your_eia_api_key" or self.eia_api_key == "":
            # Return sample structure if no API key or using placeholder
            st.warning("Using sample renewable energy data (no valid API key provided)")
            return pd.DataFrame({
                'Source': ['Solar', 'Wind', 'Hydro'],
                'Capacity': [50.0, 120.0, 80.0],  # GW
                'Generation': [45.0, 95.0, 75.0]  # TWh
            })
        
        try:
            st.info("Fetching renewable energy data from EIA API...")
            
            # EIA renewable energy data endpoint
            url = f"{self.eia_base_url}/electricity/electric-power-operational-data/data"
            params = {
                'api_key': self.eia_api_key,
                'frequency': 'monthly',
                'data[0]': 'generation',
                'facets[fueltypeid][]': ['SUN', 'WND', 'HYC'],  # Solar, Wind, Hydro
                'sort[0][column]': 'period',
                'sort[0][direction]': 'desc',
                'offset': 0,
                'length': 100
            }
            
            response_data = self._make_request(url, params)
            
            if response_data is None:
                st.warning("No data received from EIA API. Using sample data.")
                return self._get_sample_renewable_data()
                
            if 'response' not in response_data or 'data' not in response_data['response']:
                st.warning("Unexpected API response format. Using sample data.")
                return self._get_sample_renewable_data()
            
            data = response_data['response']['data']
            if not data:
                st.warning("No data available from EIA API. Using sample data.")
                return self._get_sample_renewable_data()
                
            df = pd.DataFrame(data)
            
            # Process the data
            required_columns = {'generation', 'fueltypeid'}
            if not required_columns.issubset(df.columns):
                st.warning(f"Required columns not found in response. Available columns: {df.columns.tolist()}")
                return self._get_sample_renewable_data()
            
            # Ensure generation is numeric
            try:
                df['generation'] = pd.to_numeric(df['generation'], errors='coerce')
                df = df.dropna(subset=['generation'])
                
                if df.empty:
                    st.warning("No valid generation data after cleaning. Using sample data.")
                    return self._get_sample_renewable_data()
                
                # Process the data
                df['period'] = pd.to_datetime(df['period'])
                df = df.groupby('fueltypeid')['generation'].sum().reset_index()
                
                # Map fuel type IDs to readable names
                fuel_map = {'SUN': 'Solar', 'WND': 'Wind', 'HYC': 'Hydro'}
                df['Source'] = df['fueltypeid'].map(fuel_map)
                
                # Convert to float explicitly before division
                df['Capacity'] = df['generation'].astype(float) / 1000.0  # Convert to GW equivalent
                df['Generation'] = df['generation'].astype(float) / 1000.0  # Convert to TWh
                
                st.success("Successfully loaded renewable energy data from EIA API")
                return df[['Source', 'Capacity', 'Generation']]
                
            except Exception as e:
                st.warning(f"Error processing data: {str(e)}. Using sample data.")
                return self._get_sample_renewable_data()
            
        except Exception as e:
            st.warning(f"Error fetching renewable energy data: {str(e)}. Using sample data.")
            return self._get_sample_renewable_data()
    
    def _get_sample_renewable_data(self):
        """Helper method to return sample renewable data"""
        return pd.DataFrame({
            'Source': ['Solar', 'Wind', 'Hydro'],
            'Capacity': [50.0, 120.0, 80.0],
            'Generation': [45.0, 95.0, 75.0]
        })
    
    def get_economic_indicators(self):
        """Get relevant economic indicators using FRED API"""
        if not self.fred_api_key:
            return None
        
        try:
            # Key economic indicators affecting energy markets
            indicators = {
                'GDP': 'GDP',
                'Inflation': 'CPIAUCSL',
                'USD_Index': 'DTWEXBGS',
                'Interest_Rate': 'FEDFUNDS'
            }
            
            economic_data = {}
            
            for name, series_id in indicators.items():
                url = f"{self.fred_base_url}/series/observations"
                params = {
                    'series_id': series_id,
                    'api_key': self.fred_api_key,
                    'file_type': 'json',
                    'limit': 12,  # Last 12 observations
                    'sort_order': 'desc'
                }
                
                response_data = self._make_request(url, params)
                
                if response_data and 'observations' in response_data:
                    observations = response_data['observations']
                    if observations:
                        # Get the latest value
                        latest = observations[0]
                        if latest['value'] != '.':
                            economic_data[name] = float(latest['value'])
            
            return economic_data if economic_data else None
            
        except Exception as e:
            st.error(f"Error fetching economic indicators: {str(e)}")
            return None
    
    def get_alpha_vantage_commodities(self):
        """Get commodity data from Alpha Vantage"""
        if not self.alpha_vantage_key:
            return None
        
        try:
            commodities = ['WTI', 'BRENT', 'NATURAL_GAS']
            commodity_data = {}
            
            for commodity in commodities:
                url = self.alpha_vantage_base_url
                params = {
                    'function': 'COMMODITY_PRICES',
                    'symbol': commodity,
                    'interval': 'daily',
                    'apikey': self.alpha_vantage_key
                }
                
                response_data = self._make_request(url, params)
                
                if response_data and 'data' in response_data:
                    data = response_data['data']
                    if data:
                        df = pd.DataFrame(data)
                        df['date'] = pd.to_datetime(df['date'])
                        df.set_index('date', inplace=True)
                        df['value'] = pd.to_numeric(df['value'], errors='coerce')
                        commodity_data[commodity] = df['value']
            
            return pd.DataFrame(commodity_data) if commodity_data else None
            
        except Exception as e:
            st.error(f"Error fetching Alpha Vantage commodity data: {str(e)}")
            return None
