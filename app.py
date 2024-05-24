import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from tradingview_ta import TA_Handler, Interval, Exchange

# Helper function to fetch stock data
def get_stock_data(ticker, start, end):
    stock = yf.Ticker(ticker)
    df = stock.history(start=start, end=end)
    return df

# Function to plot candlestick chart
def plot_candlestick(df):
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Candlestick chart'
    )])
    fig.update_layout(title='Candlestick Chart', xaxis_title='Date', yaxis_title='Price')
    st.plotly_chart(fig)

# Function to fetch options chain data
def get_options_chain(ticker, date):
    stock = yf.Ticker(ticker)
    opt = stock.option_chain(date)
    return opt.calls, opt.puts

# Function to predict stock prices
def predict_prices(df, days):
    df['Prediction'] = df['Close'].shift(-days)
    X = np.array(df[['Close']])
    X = X[:-days]
    y = np.array(df['Prediction'])
    y = y[:-days]
    model = LinearRegression().fit(X, y)
    future = np.array(df[['Close']])[-days:]
    pred = model.predict(future)
    return pred

# Function to get technical analysis
def get_technical_analysis(ticker):
    handler = TA_Handler(
        symbol=ticker,
        screener="india",
        exchange="NSE",
        interval=Interval.INTERVAL_1_DAY
    )
    analysis = handler.get_analysis()
    return analysis.summary

# Function to suggest option buying strategy
def suggest_option_strategy(calls, puts, spot_price, max_loss, expected_profit):
    # Example strategy: Buy slightly OTM Call and Put options with specific risk/reward
    call_options = calls[calls['strike'] >= spot_price].iloc[0]
    put_options = puts[puts['strike'] <= spot_price].iloc[-1]

    st.write(f"Suggested Call Option: Strike Price {call_options['strike']}, Last Price {call_options['lastPrice']}")
    st.write(f"Suggested Put Option: Strike Price {put_options['strike']}, Last Price {put_options['lastPrice']}")
    st.write(f"Max Loss: {max_loss} INR, Expected Profit: {expected_profit} INR")

# Streamlit UI
st.title('NSE Index Options Analysis')

# Sidebar for user inputs
st.sidebar.header('User Inputs')
ticker = st.sidebar.selectbox('Index Ticker', ['^NSEI'])  # Nifty 50 index
start_date = st.sidebar.date_input('Start Date', datetime.today() - timedelta(days=365))
end_date = st.sidebar.date_input('End Date', datetime.today())
prediction_days = st.sidebar.slider('Days for Prediction', 1, 30, 7)
max_loss = st.sidebar.number_input('Max Loss (INR)', value=1000)
expected_profit = st.sidebar.number_input('Expected Profit (INR)', value=2000)

# Fetch and display stock data
df = get_stock_data(ticker, start_date, end_date)
st.header(f'Stock Data for {ticker}')
st.write(df.tail())

# Plot candlestick chart
st.header('Candlestick Chart')
plot_candlestick(df)

# Option chain analysis
st.header('Option Chain Analysis')
expiry_dates = yf.Ticker(ticker).options
if expiry_dates:
    selected_expiry = st.selectbox('Select Expiry Date', expiry_dates)
    calls, puts = get_options_chain(ticker, selected_expiry)
    st.subheader('Calls')
    st.write(calls)
    st.subheader('Puts')
    st.write(puts)
else:
    st.write("No options data available for this ticker.")

# Intraday prediction based on time frame selection
st.header('Intraday Prediction')
pred = predict_prices(df, prediction_days)
st.write(f'Predicted closing prices for the next {prediction_days} days:')
st.write(pred)

# Technical Analysis
st.header('Technical Analysis Summary')
analysis_summary = get_technical_analysis(ticker.replace('.NS', ''))
analysis_df = pd.DataFrame(list(analysis_summary.items()), columns=['Indicator', 'Value'])
st.write(analysis_df)

# Historical analysis
st.header('Historical Analysis')
st.line_chart(df['Close'])

# Prediction forecast
st.header('Prediction Forecast')
forecast = predict_prices(df, prediction_days)
forecast_dates = pd.date_range(start=end_date, periods=prediction_days).tolist()
forecast_df = pd.DataFrame(data=forecast, index=forecast_dates, columns=['Predicted Close'])
st.line_chart(forecast_df)

# Option Strategy Suggestion
st.header('Option Buying Strategy')
if expiry_dates:
    spot_price = df['Close'].iloc[-1]
    suggest_option_strategy(calls, puts, spot_price, max_loss, expected_profit)

st.write("Note: The option strategy is a placeholder. Detailed strategy requires more complex logic and historical options data.")
