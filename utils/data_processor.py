import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st

class DataProcessor:
    """Processes and analyzes energy market data"""
    
    def __init__(self):
        self.cache = {}
    
    def calculate_price_changes(self, price_data, periods=[1, 7, 30]):
        """Calculate price changes over different periods"""
        if price_data is None or price_data.empty:
            return None
        
        changes = {}
        current_price = price_data.iloc[-1]
        
        for period in periods:
            if len(price_data) > period:
                past_price = price_data.iloc[-(period+1)]
                change = current_price - past_price
                pct_change = (change / past_price) * 100
                changes[f'{period}d_change'] = change
                changes[f'{period}d_pct_change'] = pct_change
        
        return changes
    
    def calculate_volatility(self, price_data, window=20):
        """Calculate price volatility"""
        if price_data is None or price_data.empty or len(price_data) < window:
            return None
        
        returns = price_data.pct_change().dropna()
        volatility = returns.rolling(window=window).std() * np.sqrt(252)  # Annualized
        
        return volatility.iloc[-1] if not volatility.empty else None
    
    def detect_trend(self, price_data, window=10):
        """Detect price trend using moving averages"""
        if price_data is None or price_data.empty or len(price_data) < window:
            return "Insufficient Data"
        
        short_ma = price_data.rolling(window=window//2).mean()
        long_ma = price_data.rolling(window=window).mean()
        
        if short_ma.iloc[-1] > long_ma.iloc[-1]:
            return "Uptrend"
        elif short_ma.iloc[-1] < long_ma.iloc[-1]:
            return "Downtrend"
        else:
            return "Sideways"
    
    def calculate_support_resistance(self, price_data, window=20):
        """Calculate support and resistance levels"""
        if price_data is None or price_data.empty or len(price_data) < window:
            return None, None
        
        # Use rolling min/max as basic support/resistance
        support = price_data.rolling(window=window).min().iloc[-1]
        resistance = price_data.rolling(window=window).max().iloc[-1]
        
        return support, resistance
    
    def analyze_correlation(self, data1, data2):
        """Calculate correlation between two price series"""
        if data1 is None or data2 is None or data1.empty or data2.empty:
            return None
        
        # Align the data by index
        aligned_data = pd.concat([data1, data2], axis=1, join='inner')
        if aligned_data.shape[0] < 2:
            return None
        
        correlation = aligned_data.corr().iloc[0, 1]
        return correlation
    
    def generate_market_summary(self, oil_data, gas_data, stock_data=None):
        """Generate comprehensive market summary"""
        summary = {
            'timestamp': datetime.now(),
            'oil_analysis': {},
            'gas_analysis': {},
            'market_sentiment': 'Neutral'
        }
        
        # Oil analysis
        if oil_data is not None and not oil_data.empty:
            for column in oil_data.columns:
                price_series = oil_data[column].dropna()
                if not price_series.empty:
                    summary['oil_analysis'][column] = {
                        'current_price': price_series.iloc[-1],
                        'changes': self.calculate_price_changes(price_series),
                        'volatility': self.calculate_volatility(price_series),
                        'trend': self.detect_trend(price_series),
                        'support_resistance': self.calculate_support_resistance(price_series)
                    }
        
        # Gas analysis
        if gas_data is not None and not gas_data.empty:
            price_series = gas_data['Price'].dropna()
            if not price_series.empty:
                summary['gas_analysis'] = {
                    'current_price': price_series.iloc[-1],
                    'changes': self.calculate_price_changes(price_series),
                    'volatility': self.calculate_volatility(price_series),
                    'trend': self.detect_trend(price_series),
                    'support_resistance': self.calculate_support_resistance(price_series)
                }
        
        # Market sentiment (simplified)
        sentiment_score = 0
        sentiment_factors = 0
        
        # Check oil trends
        for oil_type, analysis in summary['oil_analysis'].items():
            if analysis['trend'] == 'Uptrend':
                sentiment_score += 1
            elif analysis['trend'] == 'Downtrend':
                sentiment_score -= 1
            sentiment_factors += 1
        
        # Check gas trend
        if summary['gas_analysis'] and summary['gas_analysis']['trend']:
            if summary['gas_analysis']['trend'] == 'Uptrend':
                sentiment_score += 1
            elif summary['gas_analysis']['trend'] == 'Downtrend':
                sentiment_score -= 1
            sentiment_factors += 1
        
        if sentiment_factors > 0:
            avg_sentiment = sentiment_score / sentiment_factors
            if avg_sentiment > 0.3:
                summary['market_sentiment'] = 'Bullish'
            elif avg_sentiment < -0.3:
                summary['market_sentiment'] = 'Bearish'
            else:
                summary['market_sentiment'] = 'Neutral'
        
        return summary
    
    def calculate_price_bands(self, price_data, num_bands=3):
        """Calculate price bands for visualization"""
        if price_data is None or price_data.empty:
            return None
        
        mean_price = price_data.mean()
        std_price = price_data.std()
        
        bands = {}
        for i in range(1, num_bands + 1):
            bands[f'upper_band_{i}'] = mean_price + (i * std_price)
            bands[f'lower_band_{i}'] = mean_price - (i * std_price)
        
        bands['mean'] = mean_price
        return bands
    
    def detect_anomalies(self, price_data, threshold=2):
        """Detect price anomalies using z-score"""
        if price_data is None or price_data.empty:
            return None
        
        z_scores = np.abs((price_data - price_data.mean()) / price_data.std())
        anomalies = price_data[z_scores > threshold]
        
        return anomalies if not anomalies.empty else None
    
    def calculate_moving_averages(self, price_data, windows=[5, 10, 20, 50]):
        """Calculate multiple moving averages"""
        if price_data is None or price_data.empty:
            return None
        
        ma_data = pd.DataFrame(index=price_data.index)
        ma_data['price'] = price_data
        
        for window in windows:
            if len(price_data) >= window:
                ma_data[f'MA_{window}'] = price_data.rolling(window=window).mean()
        
        return ma_data
    
    def export_data_csv(self, data, filename=None):
        """Export data to CSV format"""
        if data is None or (isinstance(data, pd.DataFrame) and data.empty):
            return None
        
        if filename is None:
            filename = f"energy_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        try:
            csv_data = data.to_csv()
            return csv_data, filename
        except Exception as e:
            st.error(f"Error exporting data: {str(e)}")
            return None
    
    def calculate_rsi(self, price_data, window=14):
        """Calculate Relative Strength Index"""
        if price_data is None or price_data.empty or len(price_data) < window + 1:
            return None
        
        delta = price_data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1] if not rsi.empty else None
    
    def calculate_bollinger_bands(self, price_data, window=20, num_std=2):
        """Calculate Bollinger Bands"""
        if price_data is None or price_data.empty or len(price_data) < window:
            return None
        
        ma = price_data.rolling(window=window).mean()
        std = price_data.rolling(window=window).std()
        
        upper_band = ma + (std * num_std)
        lower_band = ma - (std * num_std)
        
        return {
            'middle': ma,
            'upper': upper_band,
            'lower': lower_band
        }
