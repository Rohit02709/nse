import time
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
            record['CE']['type'] = 'Call'
            calls.append(record['CE'])
        if 'PE' in record:
            record['PE']['type'] = 'Put'
            puts.append(record['PE'])

    calls_df = pd.DataFrame(calls)
    puts_df = pd.DataFrame(puts)

    return calls_df, puts_df

# Function to find ATM strike price
def find_atm_strike(calls_df, puts_df, underlying_value):
    all_strikes = pd.concat([calls_df['strikePrice'], puts_df['strikePrice']]).unique()
    atm_strike = min(all_strikes, key=lambda x: abs(x - underlying_value))
    return atm_strike

# Function to calculate market move based on various parameters
def calculate_market_move(calls_df, puts_df):
    call_oi_change = calls_df['changeinOpenInterest'].sum()
    put_oi_change = puts_df['changeinOpenInterest'].sum()
    total_oi_change = call_oi_change + put_oi_change

    if total_oi_change > 0:
        return "Bullish", total_oi_change
    elif total_oi_change < 0:
        return "Bearish", total_oi_change
    else:
        return "Neutral", total_oi_change

# Function to suggest strike prices for trading
def suggest_strike_prices(calls_df, puts_df):
    call_max_oi_strike = calls_df.loc[calls_df['openInterest'].idxmax()]
    put_max_oi_strike = puts_df.loc[puts_df['openInterest'].idxmax()]

    return call_max_oi_strike, put_max_oi_strike

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
            
            # Find ATM strike price
            atm_strike = find_atm_strike(calls_df, puts_df, underlying_value)
            st.write(f"ATM Strike Price: {atm_strike}")
            
            expiry_dates = sorted(calls_df['expiryDate'].unique())
            expiry_date = st.selectbox("Select Expiry Date", expiry_dates)

            # Select min and max strike prices above ATM
            min_strike_price = atm_strike + 1  # Set min just above ATM
            max_strike_price = st.number_input("Select Max Strike Price", min_value=min(calls_df['strikePrice']), max_value=max(calls_df['strikePrice']), value=max(calls_df['strikePrice']))

            filtered_calls = calls_df[(calls_df['expiryDate'] == expiry_date) & (calls_df['strikePrice'] >= min_strike_price) & (calls_df['strikePrice'] <= max_strike_price)]
            filtered_puts = puts_df[(puts_df['expiryDate'] == expiry_date) & (puts_df['strikePrice'] >= min_strike_price) & (puts_df['strikePrice'] <= max_strike_price)]
            
            st.subheader("Calls")
            st.dataframe(filtered_calls)
            
            st.subheader("Puts")
            st.dataframe(filtered_puts)
            
            # Visualizations
            fig_calls = px.line(filtered_calls, x='strikePrice', y='openInterest', title=f'Open Interest for Calls above ATM Strike Price {min_strike_price}')
            fig_calls.update_traces(name='Call')
            
            fig_puts = px.line(filtered_puts, x='strikePrice', y='openInterest', title=f'Open Interest for Puts above ATM Strike Price {min_strike_price}')
            fig_puts.update_traces(name='Put')
            
            combined_fig = px.line(pd.concat([filtered_calls, filtered_puts]), x='strikePrice', y='openInterest', color='type', title='Combined Open Interest')
            
            oi_bar_chart = px.bar(pd.concat([filtered_calls, filtered_puts]), x='strikePrice', y='openInterest', color='type', barmode='group', title='Open Interest Bar Chart')
            
            st.plotly_chart(fig_calls)
            st.plotly_chart(fig_puts)
            st.plotly_chart(combined_fig)
            st.plotly_chart(oi_bar_chart)
            
            market_move, total_oi_change = calculate_market_move(filtered_calls, filtered_puts)
            st.write(f"Market Move: {market_move}, Total Change in OI: {total_oi_change}")
            
            call_max_oi_strike, put_max_oi_strike = suggest_strike_prices(filtered_calls, filtered_puts)
            st.subheader("Suggested Strike Prices for Trading")
            st.write("Call Option:")
            st.write(call_max_oi_strike)
            st.write("Put Option:")
            st.write(put_max_oi_strike)
            
            time.sleep(120)  # Wait for 2 minutes before refreshing data
        else:
            st.error("Failed to fetch data from NSE API")

if __name__ == "__main__":
    main()
