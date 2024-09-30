import time
import requests
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

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
            record['CE']['type'] = 'Call'
            calls.append(record['CE'])
        if 'PE' in record:
            record['PE']['type'] = 'Put'
            puts.append(record['PE'])

    calls_df = pd.DataFrame(calls)
    puts_df = pd.DataFrame(puts)

    return calls_df, puts_df

# Streamlit application
def main():
    st.sidebar.title("Option Chain Dashboard")
    
    symbol = st.sidebar.selectbox("Select Symbol", ["NIFTY", "BANKNIFTY"])
    
    while True:
        data = fetch_option_chain(symbol)
        
        if data:
            calls_df, puts_df = process_data(data)
            
            underlying_value = data['records']['underlyingValue']
            
            st.title(f"NIFTY: {underlying_value}")
            st.write(f"Data last refreshed at: {time.strftime('%H:%M:%S')} IST")
            
            expiry_dates = sorted(calls_df['expiryDate'].unique())
            expiry_date = st.selectbox("Select Expiry Date", expiry_dates)
            
            min_strike_price = st.number_input("Select Min Strike Price", min_value=min(calls_df['strikePrice']), max_value=max(calls_df['strikePrice']), value=min(calls_df['strikePrice']))
            max_strike_price = st.number_input("Select Max Strike Price", min_value=min(calls_df['strikePrice']), max_value=max(calls_df['strikePrice']), value=max(calls_df['strikePrice']))
            
            filtered_calls = calls_df[(calls_df['expiryDate'] == expiry_date) & (calls_df['strikePrice'] >= min_strike_price) & (calls_df['strikePrice'] <= max_strike_price)]
            filtered_puts = puts_df[(puts_df['expiryDate'] == expiry_date) & (puts_df['strikePrice'] >= min_strike_price) & (puts_df['strikePrice'] <= max_strike_price)]
            
            st.subheader("Calls")
            st.dataframe(filtered_calls)
            
            st.subheader("Puts")
            st.dataframe(filtered_puts)

            # Assuming we can use the last price, high, low, and open from filtered_calls for candlestick
            if not filtered_calls.empty:
                candlestick_data = pd.DataFrame({
                    'Date': pd.to_datetime(data['records']['timestamp']),
                    'Open': filtered_calls['lastPrice'],  # Replace with actual open price if available
                    'High': filtered_calls['highPrice'],  # Replace with actual high price if available
                    'Low': filtered_calls['lowPrice'],     # Replace with actual low price if available
                    'Close': filtered_calls['lastPrice']   # Replace with actual close price if available
                })
                
                candlestick_fig = go.Figure(data=[go.Candlestick(x=candlestick_data['Date'],
                                                                  open=candlestick_data['Open'],
                                                                  high=candlestick_data['High'],
                                                                  low=candlestick_data['Low'],
                                                                  close=candlestick_data['Close'])])
                candlestick_fig.update_layout(title=f'Live Candlestick Chart for {symbol}', xaxis_title='Date', yaxis_title='Price')
                st.plotly_chart(candlestick_fig)

            time.sleep(120)  # Wait for 2 minutes before refreshing data
        else:
            st.error("Failed to fetch data from NSE API")

if __name__ == "__main__":
    main()
