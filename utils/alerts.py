import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st

class AlertSystem:
    """System for generating energy market alerts"""
    
    def __init__(self):
        self.alert_history = []
        self.alert_rules = self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default alert rules"""
        return {
            'price_change_threshold': 5.0,  # Percentage change threshold
            'volatility_threshold': 0.3,    # Volatility threshold
            'volume_threshold': 1.5,        # Volume spike threshold (multiplier)
            'rsi_overbought': 70,           # RSI overbought level
            'rsi_oversold': 30,             # RSI oversold level
            'bollinger_band_breach': True,  # Alert on Bollinger Band breaches
            'moving_average_cross': True    # Alert on moving average crossovers
        }
    
    def check_price_alerts(self, price_data, commodity_name):
        """Check for price-based alerts"""
        alerts = []
        
        if price_data is None or price_data.empty or len(price_data) < 2:
            return alerts
        
        try:
            current_price = price_data.iloc[-1]
            previous_price = price_data.iloc[-2]
            
            # Calculate price change
            price_change = ((current_price - previous_price) / previous_price) * 100
            
            # Price change alert
            if abs(price_change) >= self.alert_rules['price_change_threshold']:
                direction = "increased" if price_change > 0 else "decreased"
                alerts.append({
                    'type': 'price_change',
                    'severity': 'high' if abs(price_change) >= 10 else 'medium',
                    'commodity': commodity_name,
                    'message': f"{commodity_name} {direction} by {abs(price_change):.2f}% to ${current_price:.2f}",
                    'timestamp': datetime.now(),
                    'value': price_change
                })
            
            # Check for significant price levels
            recent_high = price_data.tail(30).max()
            recent_low = price_data.tail(30).min()
            
            if current_price >= recent_high * 0.99:  # Within 1% of recent high
                alerts.append({
                    'type': 'price_level',
                    'severity': 'medium',
                    'commodity': commodity_name,
                    'message': f"{commodity_name} approaching 30-day high at ${current_price:.2f}",
                    'timestamp': datetime.now(),
                    'value': current_price
                })
            
            if current_price <= recent_low * 1.01:  # Within 1% of recent low
                alerts.append({
                    'type': 'price_level',
                    'severity': 'medium',
                    'commodity': commodity_name,
                    'message': f"{commodity_name} approaching 30-day low at ${current_price:.2f}",
                    'timestamp': datetime.now(),
                    'value': current_price
                })
            
        except Exception as e:
            st.error(f"Error checking price alerts for {commodity_name}: {str(e)}")
        
        return alerts
    
    def check_volatility_alerts(self, price_data, commodity_name):
        """Check for volatility-based alerts"""
        alerts = []
        
        if price_data is None or price_data.empty or len(price_data) < 20:
            return alerts
        
        try:
            # Calculate rolling volatility
            returns = price_data.pct_change().dropna()
            volatility = returns.rolling(window=20).std() * np.sqrt(252)  # Annualized
            
            if volatility.empty:
                return alerts
            
            current_volatility = volatility.iloc[-1]
            avg_volatility = volatility.mean()
            
            # High volatility alert
            if current_volatility > self.alert_rules['volatility_threshold']:
                alerts.append({
                    'type': 'volatility',
                    'severity': 'high' if current_volatility > 0.5 else 'medium',
                    'commodity': commodity_name,
                    'message': f"{commodity_name} showing high volatility: {current_volatility:.2%} (avg: {avg_volatility:.2%})",
                    'timestamp': datetime.now(),
                    'value': current_volatility
                })
            
        except Exception as e:
            st.error(f"Error checking volatility alerts for {commodity_name}: {str(e)}")
        
        return alerts
    
    def check_technical_alerts(self, price_data, commodity_name):
        """Check for technical analysis alerts"""
        alerts = []
        
        if price_data is None or price_data.empty or len(price_data) < 50:
            return alerts
        
        try:
            # RSI alerts
            rsi = self._calculate_rsi(price_data)
            if rsi is not None:
                if rsi >= self.alert_rules['rsi_overbought']:
                    alerts.append({
                        'type': 'technical_rsi',
                        'severity': 'medium',
                        'commodity': commodity_name,
                        'message': f"{commodity_name} RSI indicates overbought condition: {rsi:.1f}",
                        'timestamp': datetime.now(),
                        'value': rsi
                    })
                elif rsi <= self.alert_rules['rsi_oversold']:
                    alerts.append({
                        'type': 'technical_rsi',
                        'severity': 'medium',
                        'commodity': commodity_name,
                        'message': f"{commodity_name} RSI indicates oversold condition: {rsi:.1f}",
                        'timestamp': datetime.now(),
                        'value': rsi
                    })
            
            # Moving average crossover alerts
            if self.alert_rules['moving_average_cross']:
                ma_alerts = self._check_ma_crossover(price_data, commodity_name)
                alerts.extend(ma_alerts)
            
            # Bollinger Band alerts
            if self.alert_rules['bollinger_band_breach']:
                bb_alerts = self._check_bollinger_bands(price_data, commodity_name)
                alerts.extend(bb_alerts)
            
        except Exception as e:
            st.error(f"Error checking technical alerts for {commodity_name}: {str(e)}")
        
        return alerts
    
    def _calculate_rsi(self, price_data, window=14):
        """Calculate RSI"""
        try:
            delta = price_data.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi.iloc[-1] if not rsi.empty else None
        except:
            return None
    
    def _check_ma_crossover(self, price_data, commodity_name):
        """Check for moving average crossover"""
        alerts = []
        
        try:
            if len(price_data) < 50:
                return alerts
            
            ma_short = price_data.rolling(window=10).mean()
            ma_long = price_data.rolling(window=20).mean()
            
            # Check for recent crossover
            if len(ma_short) >= 2 and len(ma_long) >= 2:
                current_position = ma_short.iloc[-1] > ma_long.iloc[-1]
                previous_position = ma_short.iloc[-2] > ma_long.iloc[-2]
                
                if current_position != previous_position:
                    direction = "bullish" if current_position else "bearish"
                    alerts.append({
                        'type': 'technical_ma_cross',
                        'severity': 'medium',
                        'commodity': commodity_name,
                        'message': f"{commodity_name} moving average crossover signals {direction} trend",
                        'timestamp': datetime.now(),
                        'value': 1 if current_position else -1
                    })
        except:
            pass
        
        return alerts
    
    def _check_bollinger_bands(self, price_data, commodity_name):
        """Check for Bollinger Band breaches"""
        alerts = []
        
        try:
            if len(price_data) < 20:
                return alerts
            
            ma = price_data.rolling(window=20).mean()
            std = price_data.rolling(window=20).std()
            upper_band = ma + (std * 2)
            lower_band = ma - (std * 2)
            
            current_price = price_data.iloc[-1]
            current_upper = upper_band.iloc[-1]
            current_lower = lower_band.iloc[-1]
            
            if current_price > current_upper:
                alerts.append({
                    'type': 'technical_bb',
                    'severity': 'medium',
                    'commodity': commodity_name,
                    'message': f"{commodity_name} broke above upper Bollinger Band: ${current_price:.2f} > ${current_upper:.2f}",
                    'timestamp': datetime.now(),
                    'value': current_price - current_upper
                })
            elif current_price < current_lower:
                alerts.append({
                    'type': 'technical_bb',
                    'severity': 'medium',
                    'commodity': commodity_name,
                    'message': f"{commodity_name} broke below lower Bollinger Band: ${current_price:.2f} < ${current_lower:.2f}",
                    'timestamp': datetime.now(),
                    'value': current_lower - current_price
                })
        except:
            pass
        
        return alerts
    
    def check_market_correlation_alerts(self, oil_data, gas_data):
        """Check for unusual market correlation patterns"""
        alerts = []
        
        try:
            if oil_data is None or gas_data is None or oil_data.empty or gas_data.empty:
                return alerts
            
            # Check correlation between oil and gas
            if 'WTI' in oil_data.columns and 'Price' in gas_data.columns:
                # Align data
                aligned_data = pd.concat([
                    oil_data['WTI'].tail(30), 
                    gas_data['Price'].tail(30)
                ], axis=1, join='inner')
                
                if len(aligned_data) >= 10:
                    correlation = aligned_data.corr().iloc[0, 1]
                    
                    # Normal oil-gas correlation is typically positive but moderate
                    if correlation < -0.5:
                        alerts.append({
                            'type': 'correlation',
                            'severity': 'medium',
                            'commodity': 'Oil-Gas',
                            'message': f"Unusual negative correlation between oil and gas: {correlation:.2f}",
                            'timestamp': datetime.now(),
                            'value': correlation
                        })
                    elif correlation > 0.9:
                        alerts.append({
                            'type': 'correlation',
                            'severity': 'low',
                            'commodity': 'Oil-Gas',
                            'message': f"Very high correlation between oil and gas: {correlation:.2f}",
                            'timestamp': datetime.now(),
                            'value': correlation
                        })
        except Exception as e:
            st.error(f"Error checking correlation alerts: {str(e)}")
        
        return alerts
    
    def generate_all_alerts(self, oil_data, gas_data, stock_data=None):
        """Generate all types of alerts"""
        all_alerts = []
        
        # Oil price alerts
        if oil_data is not None and not oil_data.empty:
            for column in oil_data.columns:
                price_series = oil_data[column].dropna()
                if not price_series.empty:
                    all_alerts.extend(self.check_price_alerts(price_series, column))
                    all_alerts.extend(self.check_volatility_alerts(price_series, column))
                    all_alerts.extend(self.check_technical_alerts(price_series, column))
        
        # Gas price alerts
        if gas_data is not None and not gas_data.empty and 'Price' in gas_data.columns:
            gas_series = gas_data['Price'].dropna()
            if not gas_series.empty:
                all_alerts.extend(self.check_price_alerts(gas_series, "Natural Gas"))
                all_alerts.extend(self.check_volatility_alerts(gas_series, "Natural Gas"))
                all_alerts.extend(self.check_technical_alerts(gas_series, "Natural Gas"))
        
        # Correlation alerts
        correlation_alerts = self.check_market_correlation_alerts(oil_data, gas_data)
        all_alerts.extend(correlation_alerts)
        
        # Sort alerts by severity and timestamp
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        all_alerts.sort(key=lambda x: (severity_order.get(x['severity'], 3), x['timestamp']), reverse=True)
        
        # Store in history
        self.alert_history.extend(all_alerts)
        
        # Keep only recent alerts in history (last 1000)
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]
        
        return all_alerts
    
    def get_alert_summary(self, hours=24):
        """Get summary of alerts in the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_alerts = [
            alert for alert in self.alert_history 
            if alert['timestamp'] > cutoff_time
        ]
        
        summary = {
            'total_alerts': len(recent_alerts),
            'high_severity': len([a for a in recent_alerts if a['severity'] == 'high']),
            'medium_severity': len([a for a in recent_alerts if a['severity'] == 'medium']),
            'low_severity': len([a for a in recent_alerts if a['severity'] == 'low']),
            'by_type': {}
        }
        
        # Count by type
        for alert in recent_alerts:
            alert_type = alert['type']
            if alert_type not in summary['by_type']:
                summary['by_type'][alert_type] = 0
            summary['by_type'][alert_type] += 1
        
        return summary
    
    def update_alert_rules(self, new_rules):
        """Update alert rules"""
        self.alert_rules.update(new_rules)
        return True
    
    def get_alert_rules(self):
        """Get current alert rules"""
        return self.alert_rules.copy()
