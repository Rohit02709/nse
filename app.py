import requests
import pandas as pd
import streamlit as st
import plotly.express as px

# Function to fetch data from NSE API
def fetch_option_chain(symbol):
    url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    headers = {
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.106 Safari/537.36",
        "Cookie": "nseappid=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhcGkubnNlIiwiYXVkIjoiYXBpLm5zZSIsImlhdCI6MTU5ODcxNjAzNywiZXhwIjoxNjMwMjUyMDM3fQ.09OgbRnabzO6jsU-YuNYn0SStRQ1Miv-LFXi7wB9hjQ; Path"
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
            calls.append(record['CE'])
        if 'PE' in record:
            puts.append(record['PE'])

    calls_df = pd.DataFrame(calls)
    puts_df = pd.DataFrame(puts)

    return calls_df, puts_df

# Streamlit application
def main():
    st.sidebar.title("Option Chain Dashboard")
    
    # Symbol selection
    symbol = st.sidebar.selectbox("Select Symbol", ["NIFTY", "BANKNIFTY"])
    data = fetch_option_chain(symbol)
    
    if data:
        calls_df, puts_df = process_data(data)
        
        st.title(f"Option Chain Dashboard for {symbol}")
        
        # Expiry date selection
        expiry_dates = sorted(calls_df['expiryDate'].unique())
        expiry_date = st.selectbox("Select Expiry Date", expiry_dates)
        
        # Filter data based on selected expiry date
        filtered_calls = calls_df[calls_df['expiryDate'] == expiry_date]
        filtered_puts = puts_df[puts_df['expiryDate'] == expiry_date]
        
        # Display dataframes
        st.subheader("Calls")
        st.dataframe(filtered_calls)
        
        st.subheader("Puts")
        st.dataframe(filtered_puts)
        
        # Plot open interest for calls
        fig = px.line(filtered_calls, x='strikePrice', y='openInterest', title='Call Open Interest by Strike Price')
        st.plotly_chart(fig)
        
        # Plot open interest for puts
        fig = px.line(filtered_puts, x='strikePrice', y='openInterest', title='Put Open Interest by Strike Price')
        st.plotly_chart(fig)
        
    else:
        st.error("Failed to fetch data from NSE API")
