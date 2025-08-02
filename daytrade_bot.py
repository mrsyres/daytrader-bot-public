import yfinance as yf
import pandas as pd
import time
import logging

# Configure logging
logging.basicConfig(filename="trade_log.txt", level=logging.INFO, format='%(asctime)s %(message)s')

# ✅ Final momentum stock list
symbols = ['PLTR', 'MSTR', 'FTNT', 'SHOP', 'NRG']
period = '30d'
interval = '15m'

# Indicator settings
rsi_period = 14
macd_short = 12
macd_long = 26
macd_signal = 9
rsi_buy = 30
rsi_sell = 70

# Track open/closed positions
ticker_positions = {symbol: False for symbol in symbols}

# Download and compute indicators
def fetch_data(symbol):
    df = yf.download(symbol, period=period, interval=interval, auto_adjust=True)
    if df.empty or len(df) < macd_long:
        return pd.DataFrame()
    
    # MACD
    df['EMA_12'] = df['Close'].ewm(span=macd_short, adjust=False).mean()
    df['EMA_26'] = df['Close'].ewm(span=macd_long, adjust=False).mean()
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['Signal'] = df['MACD'].ewm(span=macd_signal, adjust=False).mean()

    # RSI
    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(window=rsi_period).mean()
    loss = -delta.clip(upper=0).rolling(window=rsi_period).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    return df.dropna()

# Signal logic
def check_signals(symbol, df):
    latest = df.iloc[-1]
    rsi = latest['RSI'].item()
    macd = latest['MACD'].item()
    signal = latest['Signal'].item()
    price = latest['Close'].item()

    if rsi < rsi_buy and macd > signal and not ticker_positions[symbol]:
        ticker_positions[symbol] = True
        logging.info(f"BUY signal for {symbol} at ${price:.2f}")

    elif rsi > rsi_sell and macd < signal and ticker_positions[symbol]:
        ticker_positions[symbol] = False
        logging.info(f"SELL signal for {symbol} at ${price:.2f}")

# Main loop
if __name__ == "__main__":
    try:
        while True:
            for symbol in symbols:
                df = fetch_data(symbol)
                if not df.empty:
                    check_signals(symbol, df)
            time.sleep(60)
    except KeyboardInterrupt:
        print("Bot stopped.")
        logging.info("Bot manually stopped.")
