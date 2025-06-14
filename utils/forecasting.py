import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
from datetime import datetime, timedelta
import streamlit as st

class EnergyForecasting:
    """Time series forecasting for energy prices"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.features_cache = {}
    
    def create_time_features(self, dates):
        """Create time-based features for modeling"""
        df = pd.DataFrame(index=dates)
        df['day_of_week'] = dates.dayofweek
        df['day_of_month'] = dates.day
        df['month'] = dates.month
        df['quarter'] = dates.quarter
        df['year'] = dates.year
        df['day_of_year'] = dates.dayofyear
        
        # Cyclical encoding
        df['day_of_week_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_of_week_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        return df
    
    def create_lag_features(self, price_series, lags=[1, 2, 3, 5, 7, 14]):
        """Create lagged features for price prediction"""
        df = pd.DataFrame()
        
        for lag in lags:
            df[f'lag_{lag}'] = price_series.shift(lag)
        
        return df
    
    def create_technical_features(self, price_series):
        """Create technical analysis features"""
        df = pd.DataFrame(index=price_series.index)
        
        # Moving averages
        for window in [5, 10, 20]:
            df[f'ma_{window}'] = price_series.rolling(window=window).mean()
            df[f'ma_ratio_{window}'] = price_series / df[f'ma_{window}']
        
        # Volatility
        df['volatility_5'] = price_series.rolling(window=5).std()
        df['volatility_20'] = price_series.rolling(window=20).std()
        
        # Price changes
        df['pct_change_1'] = price_series.pct_change(1, fill_method=None)
        df['pct_change_5'] = price_series.pct_change(5, fill_method=None)
        
        # RSI
        delta = price_series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        return df
    
    def prepare_features(self, price_series):
        """Prepare all features for modeling"""
        # Create base features
        time_features = self.create_time_features(price_series.index)
        lag_features = self.create_lag_features(price_series)
        technical_features = self.create_technical_features(price_series)
        
        # Combine features
        features = pd.concat([time_features, lag_features, technical_features], axis=1)
        
        # Add target variable
        features['target'] = price_series
        
        # Drop rows with NaN values
        features = features.dropna()
        
        return features
    
    def train_model(self, price_series, model_type='random_forest', test_size=0.2):
        """Train forecasting model"""
        if price_series is None or price_series.empty or len(price_series) < 30:
            st.error("Insufficient data for model training (minimum 30 points required)")
            return None
        
        try:
            # Prepare features
            features_df = self.prepare_features(price_series)
            
            if features_df.empty:
                st.error("No valid features could be created from the data")
                return None
            
            # Split features and target
            X = features_df.drop('target', axis=1)
            y = features_df['target']
            
            # Train-test split
            split_idx = int(len(features_df) * (1 - test_size))
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train model
            if model_type == 'random_forest':
                model = RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42,
                    n_jobs=-1
                )
            else:  # linear_regression
                model = LinearRegression()
            
            model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            train_pred = model.predict(X_train_scaled)
            test_pred = model.predict(X_test_scaled)
            
            train_mae = mean_absolute_error(y_train, train_pred)
            test_mae = mean_absolute_error(y_test, test_pred)
            train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
            test_rmse = np.sqrt(mean_squared_error(y_test, test_pred))
            
            model_info = {
                'model': model,
                'scaler': scaler,
                'feature_columns': X.columns.tolist(),
                'train_mae': train_mae,
                'test_mae': test_mae,
                'train_rmse': train_rmse,
                'test_rmse': test_rmse,
                'train_score': model.score(X_train_scaled, y_train),
                'test_score': model.score(X_test_scaled, y_test)
            }
            
            return model_info
            
        except Exception as e:
            st.error(f"Error training model: {str(e)}")
            return None
    
    def forecast_prices(self, price_series, model_info, forecast_days=30):
        """Generate price forecasts"""
        if model_info is None or price_series is None or price_series.empty:
            return None
        
        try:
            model = model_info['model']
            scaler = model_info['scaler']
            feature_columns = model_info['feature_columns']
            
            # Prepare recent data for forecasting
            recent_data = price_series.tail(60)  # Use last 60 days for context
            
            forecasts = []
            forecast_dates = []
            
            # Generate forecasts day by day
            current_series = recent_data.copy()
            
            for i in range(forecast_days):
                # Create next date
                next_date = current_series.index[-1] + timedelta(days=1)
                forecast_dates.append(next_date)
                
                # Prepare features for next prediction
                extended_series = current_series.copy()
                extended_series.loc[next_date] = np.nan  # Placeholder
                
                features_df = self.prepare_features(extended_series)
                
                if features_df.empty:
                    break
                
                # Get features for the last (prediction) row
                last_features = features_df.iloc[-1:].drop('target', axis=1, errors='ignore')
                
                # Ensure we have all required features
                missing_features = set(feature_columns) - set(last_features.columns)
                for feature in missing_features:
                    last_features[feature] = 0  # Fill missing features with 0
                
                # Reorder columns to match training
                last_features = last_features[feature_columns]
                
                # Scale features and predict
                last_features_scaled = scaler.transform(last_features)
                prediction = model.predict(last_features_scaled)[0]
                
                forecasts.append(prediction)
                
                # Add prediction to series for next iteration
                current_series.loc[next_date] = prediction
                
                # Keep only recent data to avoid memory issues
                if len(current_series) > 100:
                    current_series = current_series.tail(80)
            
            # Create forecast dataframe
            forecast_df = pd.DataFrame({
                'date': forecast_dates,
                'forecast': forecasts
            }).set_index('date')
            
            return forecast_df
            
        except Exception as e:
            st.error(f"Error generating forecasts: {str(e)}")
            return None
    
    def calculate_prediction_intervals(self, forecasts, confidence_level=0.95):
        """Calculate prediction intervals for forecasts"""
        if forecasts is None or forecasts.empty:
            return None
        
        try:
            # Simple method: use historical volatility to estimate intervals
            forecast_values = forecasts['forecast']
            volatility = forecast_values.std()
            
            # Calculate z-score for confidence level
            from scipy import stats
            z_score = stats.norm.ppf((1 + confidence_level) / 2)
            
            margin = z_score * volatility
            
            forecasts['lower_bound'] = forecast_values - margin
            forecasts['upper_bound'] = forecast_values + margin
            
            return forecasts
            
        except Exception as e:
            st.error(f"Error calculating prediction intervals: {str(e)}")
            return forecasts
    
    def evaluate_forecast_accuracy(self, actual_prices, forecasted_prices):
        """Evaluate forecast accuracy using multiple metrics"""
        if actual_prices is None or forecasted_prices is None:
            return None
        
        try:
            # Align the data
            aligned_data = pd.concat([actual_prices, forecasted_prices], axis=1, join='inner')
            if aligned_data.shape[0] < 2:
                return None
            
            actual = aligned_data.iloc[:, 0]
            forecast = aligned_data.iloc[:, 1]
            
            # Calculate metrics
            mae = mean_absolute_error(actual, forecast)
            rmse = np.sqrt(mean_squared_error(actual, forecast))
            mape = np.mean(np.abs((actual - forecast) / actual)) * 100
            
            # Direction accuracy
            actual_direction = np.sign(actual.diff().dropna())
            forecast_direction = np.sign(forecast.diff().dropna())
            direction_accuracy = np.mean(actual_direction == forecast_direction) * 100
            
            return {
                'mae': mae,
                'rmse': rmse,
                'mape': mape,
                'direction_accuracy': direction_accuracy
            }
            
        except Exception as e:
            st.error(f"Error evaluating forecast accuracy: {str(e)}")
            return None
    
    def generate_forecast_summary(self, model_info, forecast_df):
        """Generate summary of forecast results"""
        if model_info is None or forecast_df is None:
            return None
        
        summary = {
            'forecast_period': f"{forecast_df.index[0].strftime('%Y-%m-%d')} to {forecast_df.index[-1].strftime('%Y-%m-%d')}",
            'forecast_days': len(forecast_df),
            'model_performance': {
                'train_mae': model_info.get('train_mae', 'N/A'),
                'test_mae': model_info.get('test_mae', 'N/A'),
                'train_score': model_info.get('train_score', 'N/A'),
                'test_score': model_info.get('test_score', 'N/A')
            },
            'forecast_statistics': {
                'mean_forecast': forecast_df['forecast'].mean(),
                'min_forecast': forecast_df['forecast'].min(),
                'max_forecast': forecast_df['forecast'].max(),
                'std_forecast': forecast_df['forecast'].std()
            }
        }
        
        return summary
