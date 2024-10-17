import time
import requests
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime
import pytz

# Function to fetch data from NSE API
def fetch_option_chain(symbol):
    url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    headers = {
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.106 Safari/537.36",
        "Cookie": "nseappid=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhcGkubnNlIiwiYXVkIjoiYXBpLm5zZSIsImlhdCI6MTcyOTE0NzY2MCwiZXhwIjoxNzI5MTU0ODYwfQ.6SfINgBuzV8XVHUx4KlHIxuTpYgkn_il3viq-EnxrQ4; Path"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Function to process fetched data
def process_data(data):
    calls = []
    puts = []

    for record in data['records']['data']:
        if 'CE' in record:
            record['CE']['type'] = 'Call'
            calls.append(record['CE'])
        if 'PE' in record:
            record['PE']['type'] = 'Put'
            puts.append(record['PE'])

    calls_df = pd.DataFrame(calls)
    puts_df = pd.DataFrame(puts)

    return calls_df, puts_df

# Function to suggest strike prices for trading
def suggest_strike_prices(calls_df, puts_df):
    call_max_oi_strike = calls_df.loc[calls_df['openInterest'].idxmax()]
    put_max_oi_strike = puts_df.loc[puts_df['openInterest'].idxmax()]

    return call_max_oi_strike, put_max_oi_strike

# Streamlit application
def main():
    st.sidebar.title("Option Chain Dashboard")
    
    symbol = st.sidebar.selectbox("Select Symbol", ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"])
    
    while True:
        data = fetch_option_chain(symbol)
        
        if data:
            calls_df, puts_df = process_data(data)

            # Inspect available columns
            st.write("Available columns in calls_df:")
            st.write(calls_df.columns)

            # Show sample data
            st.write("Sample data in calls_df:")
            st.write(calls_df.head())

            # Calculate premium change if columns are available
            if 'lastPrice' in calls_df.columns and 'previousPrice' in calls_df.columns:
                calls_df['premium_change'] = calls_df['lastPrice'] - calls_df['previousPrice']  # Calculate premium change
            else:
                st.error("Columns 'lastPrice' or 'previousPrice' not found in calls_df")
                calls_df['premium_change'] = None  # Set to None or handle appropriately

            # Calculate volume change if column is available
            if 'totalTradedVolume' in calls_df.columns:
                calls_df['volume_change'] = calls_df['totalTradedVolume'] - calls_df['totalTradedVolume'].shift(1)  # Volume change
            else:
                st.error("Column 'totalTradedVolume' not found in calls_df")
                calls_df['volume_change'] = None  # Set to None or handle appropriately
            
            # Filter for bullish indicators
            bullish_calls = calls_df[(calls_df['premium_change'] > 0) & (calls_df['volume_change'] > 0)]

            st.title(f"{symbol}: {data['records']['underlyingValue']}")
            st.write(f"Data last refreshed at: {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S')} IST")
            
            expiry_dates = sorted(calls_df['expiryDate'].unique())
            expiry_date = st.selectbox("Select Expiry Date", expiry_dates)

            # Display bullish calls
            if not bullish_calls.empty:
                st.subheader("Bullish Call Options")
                st.dataframe(bullish_calls)
            else:
                st.write("No bullish signals found.")

            # Suggested Strike Prices
            call_max_oi_strike, _ = suggest_strike_prices(calls_df, puts_df)
            st.subheader("Suggested Strike Prices for Trading")
            st.write("Call Option with Max OI:")
            st.write(call_max_oi_strike)
            
            time.sleep(60)  # Wait for 1 minute before refreshing data
        else:
            st.error("Failed to fetch data from NSE API")

if __name__ == "__main__":
    main()
