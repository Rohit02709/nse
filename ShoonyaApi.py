import streamlit as st
import pyotp
import pandas as pd
from datetime import datetime
from api_helper import ShoonyaApiPy
from time import sleep

# Initialize the API
api = ShoonyaApiPy()

# Function to connect and retrieve scrip details
def connect_and_get_scrip():
    try:
        ret = api.login(userid=userid, password=password,
                        twoFA=pyotp.TOTP(totp).now(),
                        vendor_code=vendor_code,
                        api_secret=api_secret,
                        imei=imei)
        st.success("Connected Successfully!")

        # Display scrip details
        scrip = api.searchscrip('NFO', inp_symbol)
        df = pd.DataFrame.from_dict(scrip['values'])
        return df
    except Exception as e:
        st.error(f"Connection failed: {e}")
        return None

# Function to get live data (WebSocket connection)
def start_websocket():
    socket_opened = False

    def open_callback():
        nonlocal socket_opened
        socket_opened = True
        st.success("WebSocket Connected")

    def event_handler_order_update(message):
        st.write("Order event: " + str(message))

    def event_handler_quote_update(message):
        global ltp
        ltp = float(message['lp'])
        st.write(f"Current LTP: {ltp}")

    api.start_websocket(order_update_callback=event_handler_order_update,
                         subscribe_callback=event_handler_quote_update,
                         socket_open_callback=open_callback)

    while not socket_opened:
        st.write("Connecting to WebSocket...")
        sleep(1)  # Polling for connection

# Trading logic
def trading_logic():
    global pos, entry, stoploss, target, strike

    if ltp < stoploss:
        # Sell logic
        order_id = api.place_order(buy_or_sell='S', product_type='C',
                                    exchange='NFO', tradingsymbol=strike,
                                    quantity=qty, discloseqty=0, price_type='MKT')
        st.write(f"Sold: {strike}, Order ID: {order_id}")
        reset_trade()
    elif ltp <= target:
        # Target hit logic
        order_id = api.place_order(buy_or_sell='S', product_type='C',
                                    exchange='NFO', tradingsymbol=strike,
                                    quantity=qty, discloseqty=0, price_type='MKT')
        st.write(f"Target hit: Sold {strike}, Order ID: {order_id}")
        reset_trade()

def reset_trade():
    global pos, entry, stoploss, target, strike
    pos = 0
    entry = 0
    stoploss = 0
    target = 0

# Streamlit UI
st.title("Trading Terminal")

# User Input Section
st.sidebar.header("Client Details")
userid = st.sidebar.text_input("User ID")
password = st.sidebar.text_input("Password", type="password")
totp = st.sidebar.text_input("2FA TOTP")
vendor_code = st.sidebar.text_input("Vendor Code")
api_secret = st.sidebar.text_input("API Secret")
imei = st.sidebar.text_input("IMEI")

st.sidebar.header("Trade Parameters")
inp_symbol = st.sidebar.text_input("Symbol", 'BANKNIFTY')
expiry = st.sidebar.text_input("Expiry Date", '25SEP24')
qty = st.sidebar.number_input("Quantity", min_value=1, value=15)

# Variables for trading logic
ltp = 0
pos = 0
entry = 0
stoploss = 0
target = 0
strike = ''

if st.sidebar.button("Connect"):
    scrip_df = connect_and_get_scrip()
    if scrip_df is not None:
        st.write(scrip_df)

if st.button("Start Live Updates"):
    start_websocket()

# Placeholder for trading logic
if st.button("Execute Trade"):
    if pos == 0:
        # Example trade initiation
        strike = f"{inp_symbol}{expiry}P{round(ltp, -2)}"
        entry = ltp
        stoploss = entry + 100  # Example stop loss logic
        target = entry - 300  # Example target logic
        pos = 1
        st.write(f"Trade initiated for {strike} at entry price {entry}")
    trading_logic()
