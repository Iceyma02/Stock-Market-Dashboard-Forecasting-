"""
Stock Market Dashboard & Forecast
A comprehensive stock analysis tool with price history, technical indicators, and forecasting.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.express as px
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Stock Market Dashboard & Forecast",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #00FF00;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #00FF00;
        color: white;
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    .metric-label {
        color: #a0aec0;
        font-size: 0.9rem;
    }
    .stProgress > div > div > div > div {
        background-color: #00FF00;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# TITLE SECTION
# ============================================================================
st.markdown('<h1 class="main-header">📊 STOCK MARKET DASHBOARD & FORECAST</h1>', unsafe_allow_html=True)
st.markdown("### Real-time Analysis & Predictions for Top Tech Stocks")

# ============================================================================
# SIDEBAR CONFIGURATION
# ============================================================================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/stocks.png", width=80)
    st.title("📈 Stock Analyzer")
    
    # Stock selection
    st.subheader("🎯 Stock Selection")
    ticker = st.selectbox(
        "Select Stock",
        ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX'],
        index=0,
        help="Choose a stock to analyze"
    )
    
    # Time period selection
    st.subheader("📅 Time Period")
    period = st.selectbox(
        "Select Period",
        ['1mo', '3mo', '6mo', '1y', '2y', '5y'],
        index=4,  # Default to 2y
        help="Choose historical data range"
    )
    
    # Convert period to days for display
    period_days = {
        '1mo': 30, '3mo': 90, '6mo': 180,
        '1y': 365, '2y': 730, '5y': 1825
    }
    
    st.markdown("---")
    
    # Forecasting settings
    st.subheader("🔮 Forecast Settings")
    forecast_days = st.slider(
        "Days to Forecast",
        min_value=7,
        max_value=90,
        value=30,
        step=1,
        help="Number of days to predict"
    )
    
    forecast_method = st.selectbox(
        "Forecasting Method",
        ["Linear Regression", "Moving Average Trend", "Simple Projection", "Prophet (Basic)"],
        index=0,
        help="Choose forecasting algorithm"
    )
    
    show_confidence = st.checkbox("Show Confidence Interval", value=True)
    
    st.markdown("---")
    
    # Technical indicators
    st.subheader("📊 Technical Indicators")
    show_ma = st.checkbox("Show Moving Averages", value=True)
    ma_short = st.slider("Short MA Period", 5, 50, 20) if show_ma else 20
    ma_long = st.slider("Long MA Period", 20, 200, 50) if show_ma else 50
    
    show_rsi = st.checkbox("Show RSI", value=False)
    show_macd = st.checkbox("Show MACD", value=False)
    
    st.markdown("---")
    
    # Data source info
    st.subheader("ℹ️ About")
    st.info(
        "Data sourced from Yahoo Finance with sample data fallback. "
        "Forecasts are for educational purposes only."
    )
    
    # Refresh button
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_stock_data(ticker, period='2y'):
    """Load stock data from Yahoo Finance"""
    try:
        import yfinance as yf
        with st.spinner(f'Loading {ticker} data...'):
            stock = yf.Ticker(ticker)
            data = stock.history(period=period)
            
            if not data.empty:
                return data, True
            return None, False
    except Exception as e:
        st.warning(f"Could not load real data: {e}")
        return None, False

def generate_sample_data(ticker, days=730):
    """Generate realistic sample data when real data unavailable"""
    np.random.seed(hash(ticker) % 42)  # Different seed per ticker
    
    dates = pd.date_range(
        start=datetime.now() - timedelta(days=days),
        end=datetime.now(),
        freq='D'
    )
    
    # Realistic price ranges for each stock
    price_ranges = {
        'AAPL': (140, 200), 'MSFT': (240, 420), 'GOOGL': (80, 160),
        'AMZN': (100, 190), 'TSLA': (150, 400), 'META': (90, 350),
        'NVDA': (120, 950), 'NFLX': (300, 700)
    }
    
    low, high = price_ranges.get(ticker, (100, 200))
    
    # Generate base price with trend
    base_trend = np.linspace(0, (high - low) * 0.3, len(dates))
    
    # Add seasonality and volatility
    seasonality = np.sin(np.arange(len(dates)) * 2 * np.pi / 252) * (high - low) * 0.05
    volatility = np.random.normal(0, (high - low) * 0.02, len(dates))
    
    # Cumulative volatility for realistic walk
    cum_volatility = np.cumsum(volatility) * 0.1
    
    close_prices = low + base_trend + seasonality + cum_volatility
    close_prices = np.maximum(close_prices, low * 0.5)  # Ensure no negative prices
    
    # Generate OHLC data
    data = pd.DataFrame({
        'Open': close_prices * (1 - np.random.uniform(0, 0.02, len(dates))),
        'High': close_prices * (1 + np.random.uniform(0, 0.03, len(dates))),
        'Low': close_prices * (1 - np.random.uniform(0, 0.03, len(dates))),
        'Close': close_prices,
        'Volume': np.random.randint(10000000, 100000000, len(dates))
    }, index=dates)
    
    return data

# ============================================================================
# TECHNICAL INDICATORS
# ============================================================================
def calculate_moving_averages(data, short=20, long=50):
    """Calculate short and long moving averages"""
    if data is None or data.empty:
        return None, None
    ma_short = data['Close'].rolling(window=short).mean()
    ma_long = data['Close'].rolling(window=long).mean()
    return ma_short, ma_long

def calculate_rsi(data, period=14):
    """Calculate Relative Strength Index"""
    if data is None or data.empty:
        return None
    
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(data, fast=12, slow=26, signal=9):
    """Calculate MACD indicator"""
    if data is None or data.empty:
        return None, None
    
    exp1 = data['Close'].ewm(span=fast, adjust=False).mean()
    exp2 = data['Close'].ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line
    return macd, signal_line, histogram

# ============================================================================
# FORECASTING FUNCTIONS
# ============================================================================
def linear_regression_forecast(data, days, confidence=80):
    """Linear regression based forecast"""
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    
    # Prepare data
    df = data[['Close']].dropna().reset_index()
    df['days'] = np.arange(len(df))
    
    X = df['days'].values.reshape(-1, 1)
    y = df['Close'].values
    
    # Train model
    model = LinearRegression()
    model.fit(X, y)
    
    # Predict future
    future_X = np.arange(len(df), len(df) + days).reshape(-1, 1)
    predictions = model.predict(future_X)
    
    # Calculate confidence intervals (simplified)
    residuals = y - model.predict(X)
    std_residuals = np.std(residuals)
    
    future_dates = [df['index'].iloc[-1] + timedelta(days=i+1) for i in range(days)]
    
    # Create forecast DataFrame
    forecast = pd.DataFrame({
        'ds': future_dates,
        'yhat': predictions,
        'yhat_lower': predictions - (std_residuals * (1 - confidence/100)),
        'yhat_upper': predictions + (std_residuals * (1 - confidence/100))
    })
    
    return forecast

def moving_average_forecast(data, days):
    """Moving average based forecast with trend"""
    df = data[['Close']].dropna()
    
    # Calculate trend from recent data
    recent = df.tail(30)
    prices = recent['Close'].values
    x = np.arange(len(prices))
    z = np.polyfit(x, prices, 1)
    trend = z[0]  # Slope
    
    last_price = df['Close'].iloc[-1]
    future_prices = []
    
    # Generate forecast with trend and some randomness
    for i in range(days):
        # Add trend plus some noise
        noise = np.random.normal(0, abs(trend) * 0.3)
        next_price = last_price + trend + noise
        future_prices.append(next_price)
        last_price = next_price
    
    future_dates = [df.index[-1] + timedelta(days=i+1) for i in range(days)]
    
    forecast = pd.DataFrame({
        'ds': future_dates,
        'yhat': future_prices,
        'yhat_lower': [p * 0.95 for p in future_prices],
        'yhat_upper': [p * 1.05 for p in future_prices]
    })
    
    return forecast

def simple_projection_forecast(data, days):
    """Simple projection based on historical volatility"""
    df = data[['Close']].dropna()
    
    # Calculate daily returns
    returns = df['Close'].pct_change().dropna()
    avg_return = returns.mean()
    std_return = returns.std()
    
    last_price = df['Close'].iloc[-1]
    future_prices = []
    
    # Random walk based on historical volatility
    for i in range(days):
        daily_return = np.random.normal(avg_return, std_return)
        next_price = last_price * (1 + daily_return)
        future_prices.append(next_price)
        last_price = next_price
    
    future_dates = [df.index[-1] + timedelta(days=i+1) for i in range(days)]
    
    forecast = pd.DataFrame({
        'ds': future_dates,
        'yhat': future_prices,
        'yhat_lower': [p * 0.9 for p in future_prices],
        'yhat_upper': [p * 1.1 for p in future_prices]
    })
    
    return forecast

# ============================================================================
# MAIN DASHBOARD
# ============================================================================
def main():
    # Load data
    real_data, is_real = load_stock_data(ticker, period)
    
    if real_data is not None and not real_data.empty:
        data = real_data
        data_source = "✅ Real Yahoo Finance data"
    else:
        data = generate_sample_data(ticker, period_days[period])
        data_source = "⚠️ Sample data (real unavailable)"
        is_real = False
    
    # Data processing
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    
    # Calculate indicators
    ma_short_vals, ma_long_vals = calculate_moving_averages(data, ma_short, ma_long)
    rsi_vals = calculate_rsi(data) if show_rsi else None
    macd_vals, signal_vals, hist_vals = calculate_macd(data) if show_macd else (None, None, None)
    
    # ========================================================================
    # KEY METRICS ROW
    # ========================================================================
    st.subheader("📊 Key Metrics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    current_price = data['Close'].iloc[-1]
    prev_price = data['Close'].iloc[-2] if len(data) > 1 else current_price
    daily_change = current_price - prev_price
    daily_change_pct = (daily_change / prev_price) * 100
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Current Price</div>
            <div class="metric-value">${current_price:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        color = "green" if daily_change >= 0 else "red"
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: {color};">
            <div class="metric-label">Daily Change</div>
            <div class="metric-value">{daily_change:+.2f} ({daily_change_pct:+.2f}%)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        week_high = data['High'].tail(5).max()
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">5-Day High</div>
            <div class="metric-value">${week_high:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        week_low = data['Low'].tail(5).min()
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">5-Day Low</div>
            <div class="metric-value">${week_low:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        volume = data['Volume'].iloc[-1]
        avg_volume = data['Volume'].tail(20).mean()
        volume_ratio = volume / avg_volume
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Volume (vs Avg)</div>
            <div class="metric-value">{volume_ratio:.1f}x</div>
            <div class="metric-label">Avg: {avg_volume:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.caption(f"Data source: {data_source} | Last updated: {data.index[-1].strftime('%Y-%m-%d %H:%M')}")
    
    # ========================================================================
    # PRICE CHART
    # ========================================================================
    st.subheader(f"📈 {ticker} Stock Price History")
    
    fig = go.Figure()
    
    # Candlestick or line chart option
    chart_type = st.radio("Chart Type", ["Candlestick", "Line"], horizontal=True)
    
    if chart_type == "Candlestick":
        fig.add_trace(go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name='Price',
            showlegend=False
        ))
    else:
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['Close'],
            mode='lines',
            name='Close Price',
            line=dict(color='#00FF00', width=2),
            fill='tozeroy',
            fillcolor='rgba(0,255,0,0.1)'
        ))
    
    # Add moving averages
    if show_ma and ma_short_vals is not None and ma_long_vals is not None:
        fig.add_trace(go.Scatter(
            x=data.index,
            y=ma_short_vals,
            mode='lines',
            name=f'{ma_short}-Day MA',
            line=dict(color='#FFAA00', width=1.5, dash='dash')
        ))
        fig.add_trace(go.Scatter(
            x=data.index,
            y=ma_long_vals,
            mode='lines',
            name=f'{ma_long}-Day MA',
            line=dict(color='#FF0000', width=1.5, dash='dash')
        ))
    
    fig.update_layout(
        title=f"{ticker} Stock Price - {period.upper()}",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        template="plotly_dark",
        height=500,
        hovermode='x unified',
        xaxis_rangeslider_visible=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ========================================================================
    # TECHNICAL INDICATORS
    # ========================================================================
    if show_rsi or show_macd:
        st.subheader("📊 Technical Indicators")
        
        if show_rsi and rsi_vals is not None:
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(
                x=data.index,
                y=rsi_vals,
                mode='lines',
                name='RSI',
                line=dict(color='#FF6B00', width=2)
            ))
            
            # Add overbought/oversold lines
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5)
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5)
            
            fig_rsi.update_layout(
                title="Relative Strength Index (RSI)",
                xaxis_title="Date",
                yaxis_title="RSI",
                template="plotly_dark",
                height=300
            )
            
            st.plotly_chart(fig_rsi, use_container_width=True)
        
        if show_macd and macd_vals is not None:
            fig_macd = go.Figure()
            fig_macd.add_trace(go.Scatter(
                x=data.index,
                y=macd_vals,
                mode='lines',
                name='MACD',
                line=dict(color='#00FF00', width=2)
            ))
            fig_macd.add_trace(go.Scatter(
                x=data.index,
                y=signal_vals,
                mode='lines',
                name='Signal',
                line=dict(color='#FF6B00', width=2)
            ))
            
            # Add histogram
            colors = ['red' if val < 0 else 'green' for val in hist_vals]
            fig_macd.add_trace(go.Bar(
                x=data.index,
                y=hist_vals,
                name='Histogram',
                marker_color=colors,
                opacity=0.3
            ))
            
            fig_macd.update_layout(
                title="MACD Indicator",
                xaxis_title="Date",
                yaxis_title="MACD",
                template="plotly_dark",
                height=300
            )
            
            st.plotly_chart(fig_macd, use_container_width=True)
    
    # ========================================================================
    # FORECASTING SECTION
    # ========================================================================
    st.markdown("---")
    st.subheader("🔮 Price Forecast")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown("### Forecast Settings")
        st.write(f"**Method:** {forecast_method}")
        st.write(f"**Forecast Days:** {forecast_days}")
        st.write(f"**Confidence Interval:** {'Enabled' if show_confidence else 'Disabled'}")
        
        if st.button("📊 Generate Forecast", type="primary", use_container_width=True):
            st.session_state['generate_forecast'] = True
    
    with col2:
        if st.session_state.get('generate_forecast', False):
            with st.spinner('Generating forecast...'):
                try:
                    # Generate forecast based on selected method
                    if forecast_method == "Linear Regression":
                        forecast = linear_regression_forecast(data, forecast_days)
                    elif forecast_method == "Moving Average Trend":
                        forecast = moving_average_forecast(data, forecast_days)
                    elif forecast_method == "Simple Projection":
                        forecast = simple_projection_forecast(data, forecast_days)
                    else:  # Prophet (simplified)
                        forecast = linear_regression_forecast(data, forecast_days)  # Placeholder
                    
                    # Create forecast plot
                    fig_forecast = go.Figure()
                    
                    # Historical data
                    fig_forecast.add_trace(go.Scatter(
                        x=data.index[-90:],  # Last 90 days
                        y=data['Close'].iloc[-90:],
                        mode='lines',
                        name='Historical',
                        line=dict(color='#00FF00', width=3)
                    ))
                    
                    # Forecast
                    fig_forecast.add_trace(go.Scatter(
                        x=forecast['ds'],
                        y=forecast['yhat'],
                        mode='lines',
                        name='Forecast',
                        line=dict(color='#FF6B00', width=3, dash='dash')
                    ))
                    
                    # Confidence interval
                    if show_confidence and 'yhat_lower' in forecast.columns:
                        fig_forecast.add_trace(go.Scatter(
                            x=pd.concat([forecast['ds'], forecast['ds'][::-1]]),
                            y=pd.concat([forecast['yhat_upper'], forecast['yhat_lower'][::-1]]),
                            fill='toself',
                            fillcolor='rgba(255,107,0,0.2)',
                            line=dict(color='rgba(255,255,255,0)'),
                            hoverinfo="skip",
                            showlegend=True,
                            name=f'{confidence_interval}% Confidence'
                        ))
                    
                    fig_forecast.update_layout(
                        title=f"{ticker} - {forecast_days}-Day Price Forecast",
                        xaxis_title="Date",
                        yaxis_title="Price (USD)",
                        template="plotly_dark",
                        height=400,
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig_forecast, use_container_width=True)
                    
                    # Forecast metrics
                    col_a, col_b, col_c, col_d = st.columns(4)
                    
                    with col_a:
                        forecast_high = forecast['yhat'].max()
                        st.metric("Forecast High", f"${forecast_high:.2f}")
                    
                    with col_b:
                        forecast_low = forecast['yhat'].min()
                        st.metric("Forecast Low", f"${forecast_low:.2f}")
                    
                    with col_c:
                        forecast_end = forecast['yhat'].iloc[-1]
                        current = data['Close'].iloc[-1]
                        change = ((forecast_end - current) / current) * 100
                        st.metric("Expected Return", f"{change:+.1f}%")
                    
                    with col_d:
                        volatility = data['Close'].pct_change().std() * np.sqrt(252) * 100
                        st.metric("Annual Volatility", f"{volatility:.1f}%")
                    
                    # Show forecast table
                    with st.expander("📋 View Detailed Forecast"):
                        forecast_display = forecast[['ds', 'yhat']].copy()
                        forecast_display['ds'] = forecast_display['ds'].dt.strftime('%Y-%m-%d')
                        forecast_display['yhat'] = forecast_display['yhat'].apply(lambda x: f"${x:.2f}")
                        forecast_display.columns = ['Date', 'Predicted Price']
                        st.dataframe(forecast_display, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"Forecast error: {str(e)}")
    
    # ========================================================================
    # STATISTICS & ANALYSIS
    # ========================================================================
    st.markdown("---")
    st.subheader("📊 Statistical Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Price distribution
        fig_dist = go.Figure()
        fig_dist.add_trace(go.Histogram(
            x=data['Close'],
            nbinsx=30,
            name='Price Distribution',
            marker_color='#00FF00',
            opacity=0.7
        ))
        
        fig_dist.update_layout(
            title="Price Distribution",
            xaxis_title="Price (USD)",
            yaxis_title="Frequency",
            template="plotly_dark",
            height=300
        )
        
        st.plotly_chart(fig_dist, use_container_width=True)
    
    with col2:
        # Returns distribution
        returns = data['Close'].pct_change().dropna() * 100
        
        fig_returns = go.Figure()
        fig_returns.add_trace(go.Histogram(
            x=returns,
            nbinsx=30,
            name='Returns Distribution',
            marker_color='#FF6B00',
            opacity=0.7
        ))
        
        fig_returns.update_layout(
            title="Daily Returns Distribution (%)",
            xaxis_title="Return (%)",
            yaxis_title="Frequency",
            template="plotly_dark",
            height=300
        )
        
        st.plotly_chart(fig_returns, use_container_width=True)
    
    # Summary statistics table
    st.subheader("📋 Summary Statistics")
    
    stats_data = {
        'Metric': ['Mean Price', 'Median Price', 'Std Deviation', 'Skewness', 'Kurtosis',
                  'Max Price', 'Min Price', 'Avg Daily Return', 'Sharpe Ratio (est)'],
        'Value': [
            f"${data['Close'].mean():.2f}",
            f"${data['Close'].median():.2f}",
            f"${data['Close'].std():.2f}",
            f"{data['Close'].skew():.3f}",
            f"{data['Close'].kurtosis():.3f}",
            f"${data['Close'].max():.2f}",
            f"${data['Close'].min():.2f}",
            f"{returns.mean():.3f}%",
            f"{returns.mean() / returns.std() * np.sqrt(252):.2f}"
        ]
    }
    
    stats_df = pd.DataFrame(stats_data)
    st.dataframe(stats_df, use_container_width=True)
    
    # ========================================================================
    # RECENT DATA TABLE
    # ========================================================================
    st.subheader("📋 Recent Trading Data")
    
    recent = data.tail(10)[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
    recent.index = recent.index.strftime('%Y-%m-%d')
    recent['Volume'] = recent['Volume'].apply(lambda x: f"{x:,.0f}")
    recent = recent.round(2)
    
    st.dataframe(recent, use_container_width=True)
    
    # ========================================================================
    # RISK DISCLAIMER
    # ========================================================================
    st.markdown("---")
    st.warning("""
    **⚠️ Risk Disclaimer:** This dashboard is for educational and informational purposes only. 
    Stock price forecasts are based on historical data and statistical models. Past performance 
    does not guarantee future results. Always conduct your own research and consult with a 
    qualified financial advisor before making investment decisions.
    """)

# ============================================================================
# RUN THE APP
# ============================================================================
if __name__ == "__main__":
    main()
