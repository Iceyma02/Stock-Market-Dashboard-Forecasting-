import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime, timedelta
import numpy as np

st.set_page_config(page_title="Stock Dashboard", layout="wide")

st.title("📈 Stock Market Dashboard & Forecast")
st.write("Analyzing AAPL, MSFT, GOOGL, AMZN, TSLA (Last 2 Years)")

# Sidebar for stock selection
ticker = st.sidebar.selectbox("Select Stock", ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'])

# Forecasting settings in sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("Forecast Settings")
forecast_days = st.sidebar.slider("Days to Forecast", 7, 90, 30)
confidence_interval = st.sidebar.slider("Confidence Interval", 80, 95, 80)

# Simple function to get stock data
def get_stock_data_simple(ticker):
    try:
        import yfinance as yf
        # Download data
        data = yf.download(ticker, period="2y", progress=False)
        
        # If we get data, return it directly
        if not data.empty:
            return data
        return None
    except Exception as e:
        st.error(f"Error downloading data: {e}")
        return None

# Simple sample data
def generate_simple_sample_data(ticker):
    dates = pd.date_range(start=datetime.now() - timedelta(days=730), end=datetime.now(), freq='D')
    
    # Realistic price ranges for each stock
    price_ranges = {
        'AAPL': (140, 200),
        'MSFT': (240, 400),
        'GOOGL': (80, 160),
        'AMZN': (100, 180),
        'TSLA': (150, 300)
    }
    
    low, high = price_ranges.get(ticker, (100, 200))
    
    # Generate realistic prices
    np.random.seed(42)  # For consistent results
    prices = np.random.uniform(low, high, len(dates))
    
    # Add some trend
    trend = np.linspace(0, (high - low) * 0.3, len(dates))
    prices = prices + trend
    
    data = pd.DataFrame({
        'Open': prices * 0.99,
        'High': prices * 1.02,
        'Low': prices * 0.98,
        'Close': prices,
        'Volume': np.random.randint(10000000, 50000000, len(dates))
    }, index=dates)
    
    return data

# Get data
data = get_stock_data_simple(ticker)

# If no real data, use sample
if data is None or data.empty:
    st.warning("⚠️ Using sample data (real data unavailable)")
    data = generate_simple_sample_data(ticker)
else:
    st.success("✅ Real market data loaded successfully!")

# SIMPLE DATA PROCESSING - No complex cleaning
try:
    # If data has MultiIndex columns, simplify it
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    
    # Ensure we have the basic columns
    if 'Close' not in data.columns:
        st.error("No Close price data available")
        st.stop()
    
    # Convert to simple numeric values
    close_prices = pd.Series(data['Close'].values, index=data.index)
    close_prices = close_prices.apply(lambda x: float(x) if pd.notna(x) else np.nan)
    
except Exception as e:
    st.error(f"Data processing error: {e}")
    st.stop()

# Display basic info
st.subheader(f"Data Overview for {ticker}")
col1, col2, col3 = st.columns(3)

with col1:
    current_price = close_prices.iloc[-1] if not close_prices.isna().all() else np.nan
    if not np.isnan(current_price):
        st.metric("Current Price", f"${current_price:.2f}")
    else:
        st.metric("Current Price", "N/A")

with col2:
    if len(close_prices) > 1:
        current_price = close_prices.iloc[-1]
        previous_price = close_prices.iloc[-2]
        if not (np.isnan(current_price) or np.isnan(previous_price)):
            change = current_price - previous_price
            change_pct = (change / previous_price) * 100
            st.metric("Daily Change", f"${change:.2f}", f"{change_pct:.2f}%")
        else:
            st.metric("Daily Change", "N/A")
    else:
        st.metric("Daily Change", "N/A")

with col3:
    st.metric("Data Points", len(close_prices))

# Plot historical prices
st.subheader(f"Historical Close Price for {ticker}")

# Filter out NaN values for plotting
valid_data = close_prices.dropna()

if len(valid_data) > 0:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=valid_data.index, 
        y=valid_data.values, 
        mode='lines', 
        name='Close Price',
        line=dict(color='#00FF00', width=2),
        hovertemplate='<b>Date</b>: %{x}<br><b>Price</b>: $%{y:.2f}<extra></extra>'
    ))

    fig.update_layout(
        title=f"{ticker} Stock Price (Last 2 Years)",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        template="plotly_dark",
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("No valid price data available for plotting")

# Show recent data
st.subheader("Recent Data (Last 5 Trading Days)")

try:
    recent_dates = data.index[-5:]
    recent_closes = close_prices[-5:]
    
    display_data = pd.DataFrame({
        'Date': recent_dates,
        'Close': [f"${x:.2f}" for x in recent_closes]
    })
    
    st.dataframe(display_data, use_container_width=True)
    
except Exception as e:
    st.error(f"Error displaying recent data: {e}")

# Simple moving averages
st.subheader("Price Analysis with Moving Averages")

if len(valid_data) > 20:
    # Calculate moving averages
    ma_20 = valid_data.rolling(window=20).mean()
    ma_50 = valid_data.rolling(window=50).mean()
    
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=valid_data.index, 
        y=valid_data.values, 
        mode='lines', 
        name='Close Price',
        line=dict(color='#00FF00', width=2)
    ))
    fig2.add_trace(go.Scatter(
        x=ma_20.index, 
        y=ma_20.values, 
        mode='lines', 
        name='20-Day MA',
        line=dict(color='#FFAA00', width=1.5)
    ))
    fig2.add_trace(go.Scatter(
        x=ma_50.index, 
        y=ma_50.values, 
        mode='lines', 
        name='50-Day MA',
        line=dict(color='#FF0000', width=1.5)
    ))

    fig2.update_layout(
        title=f"{ticker} Price with Moving Averages",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        template="plotly_dark",
        height=500
    )

    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("Need more data points for moving average analysis")

# Price statistics
st.subheader("Price Statistics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if len(valid_data) > 0:
        high_price = valid_data.max()
        st.metric("All-Time High", f"${high_price:.2f}")
    else:
        st.metric("All-Time High", "N/A")

with col2:
    if len(valid_data) > 0:
        low_price = valid_data.min()
        st.metric("All-Time Low", f"${low_price:.2f}")
    else:
        st.metric("All-Time Low", "N/A")

with col3:
    if len(valid_data) > 0:
        avg_price = valid_data.mean()
        st.metric("Average Price", f"${avg_price:.2f}")
    else:
        st.metric("Average Price", "N/A")

with col4:
    if len(valid_data) > 1:
        volatility = valid_data.pct_change().std() * 100
        st.metric("Volatility", f"{volatility:.2f}%")
    else:
        st.metric("Volatility", "N/A")

# FORECASTING SECTION
st.markdown("---")
st.subheader("🔮 Stock Price Forecasting")

# Forecasting method selection
forecast_method = st.selectbox(
    "Select Forecasting Method",
    ["Linear Regression", "Moving Average Trend", "Simple Projection"]
)

if st.button(f"Generate {forecast_days}-Day Forecast", type="primary"):
    with st.spinner('Generating forecast...'):
        try:
            # Prepare data for forecasting
            forecast_data = valid_data.reset_index()
            forecast_data.columns = ['ds', 'y']
            forecast_data = forecast_data.dropna()
            
            if forecast_method == "Linear Regression":
                # Simple linear regression forecast
                from sklearn.linear_model import LinearRegression
                
                # Create features (days as numbers)
                days = np.arange(len(forecast_data)).reshape(-1, 1)
                prices = forecast_data['y'].values
                
                # Train model
                model = LinearRegression()
                model.fit(days, prices)
                
                # Predict future
                future_days = np.arange(len(forecast_data), len(forecast_data) + forecast_days).reshape(-1, 1)
                future_prices = model.predict(future_days)
                
                # Create future dates
                last_date = forecast_data['ds'].iloc[-1]
                future_dates = [last_date + timedelta(days=i+1) for i in range(forecast_days)]
                
                forecast_df = pd.DataFrame({
                    'ds': future_dates,
                    'yhat': future_prices
                })
                
            elif forecast_method == "Moving Average Trend":
                # Moving average based forecast
                last_prices = forecast_data['y'].tail(30).values
                trend = np.mean(np.diff(last_prices[-10:]))  # Recent trend
                
                future_prices = []
                current_price = forecast_data['y'].iloc[-1]
                
                for i in range(forecast_days):
                    # Add trend with some randomness
                    change = trend + np.random.normal(0, abs(trend) * 0.5)
                    current_price = max(0.1, current_price + change)
                    future_prices.append(current_price)
                
                # Create future dates
                last_date = forecast_data['ds'].iloc[-1]
                future_dates = [last_date + timedelta(days=i+1) for i in range(forecast_days)]
                
                forecast_df = pd.DataFrame({
                    'ds': future_dates,
                    'yhat': future_prices
                })
                
            else:  # Simple Projection
                # Simple projection based on recent volatility
                recent_returns = forecast_data['y'].pct_change().dropna().tail(30)
                avg_return = recent_returns.mean()
                std_return = recent_returns.std()
                
                future_prices = []
                current_price = forecast_data['y'].iloc[-1]
                
                for i in range(forecast_days):
                    # Random walk based on historical volatility
                    change = current_price * np.random.normal(avg_return, std_return)
                    current_price = max(0.1, current_price + change)
                    future_prices.append(current_price)
                
                # Create future dates
                last_date = forecast_data['ds'].iloc[-1]
                future_dates = [last_date + timedelta(days=i+1) for i in range(forecast_days)]
                
                forecast_df = pd.DataFrame({
                    'ds': future_dates,
                    'yhat': future_prices
                })
            
            # Display forecast results
            st.success(f"Forecast generated for next {forecast_days} days!")
            
            # Create forecast plot
            fig_forecast = go.Figure()
            
            # Historical data
            fig_forecast.add_trace(go.Scatter(
                x=forecast_data['ds'],
                y=forecast_data['y'],
                mode='lines',
                name='Historical Price',
                line=dict(color='#00FF00', width=2)
            ))
            
            # Forecast data
            fig_forecast.add_trace(go.Scatter(
                x=forecast_df['ds'],
                y=forecast_df['yhat'],
                mode='lines',
                name='Forecast',
                line=dict(color='#FF6B00', width=2, dash='dash')
            ))
            
            fig_forecast.update_layout(
                title=f"{ticker} {forecast_days}-Day Price Forecast ({forecast_method})",
                xaxis_title="Date",
                yaxis_title="Price (USD)",
                template="plotly_dark",
                height=500
            )
            
            st.plotly_chart(fig_forecast, use_container_width=True)
            
            # Forecast statistics
            st.subheader("Forecast Summary")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                forecast_high = forecast_df['yhat'].max()
                st.metric("Forecast High", f"${forecast_high:.2f}")
            
            with col2:
                forecast_low = forecast_df['yhat'].min()
                st.metric("Forecast Low", f"${forecast_low:.2f}")
            
            with col3:
                forecast_end = forecast_df['yhat'].iloc[-1]
                current_price = forecast_data['y'].iloc[-1]
                change_pct = ((forecast_end - current_price) / current_price) * 100
                st.metric("End Price", f"${forecast_end:.2f}", f"{change_pct:.1f}%")
            
            with col4:
                forecast_trend = "📈 Bullish" if forecast_end > current_price else "📉 Bearish"
                st.metric("Trend", forecast_trend)
            
            # Detailed forecast table
            st.subheader("Detailed Forecast")
            forecast_display = forecast_df.copy()
            forecast_display['Date'] = forecast_display['ds'].dt.strftime('%Y-%m-%d')
            forecast_display['Predicted Price'] = forecast_display['yhat'].apply(lambda x: f"${x:.2f}")
            forecast_display = forecast_display[['Date', 'Predicted Price']]
            
            st.dataframe(forecast_display, use_container_width=True)
            
        except Exception as e:
            st.error(f"Forecasting error: {str(e)}")
            st.info("Try selecting a different forecasting method or check your data.")

# Risk Disclaimer
st.markdown("---")
st.info("""
**⚠️ Risk Disclaimer:** Stock price forecasts are based on historical data and statistical models. 
They are for educational purposes only and should not be considered financial advice. 
Past performance does not guarantee future results. Always do your own research and consult with a financial advisor before making investment decisions.
""")

# Additional info
st.sidebar.markdown("---")
st.sidebar.subheader("About")
st.sidebar.info(
    "Stock dashboard with price history, analysis, and forecasting. "
    "Data from Yahoo Finance with sample data fallback."
)

# Debug info
with st.sidebar.expander("Data Info"):
    st.write(f"Data points: {len(data)}")
    st.write(f"Valid prices: {len(valid_data)}")
    st.write(f"Date range: {data.index.min()} to {data.index.max()}")
    if len(valid_data) > 0:
        st.write(f"Price range: ${valid_data.min():.2f} - ${valid_data.max():.2f}")