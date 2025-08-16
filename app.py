import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime, timedelta

# ------------------ Streamlit Page Config ------------------
st.set_page_config(page_title="📊 Stock Dashboard", layout="wide")
st.title("📊 Stock Dashboard")

# ------------------ Sidebar Controls ------------------
st.sidebar.header("Controls")

# Tickers universe
all_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NFLX", "NVDA", "JPM", "BAC"]

# Dropdown with search
selected_stock = st.sidebar.selectbox("Select Stock", all_tickers, index=0)

# Multi-stock comparison
compare_mode = st.sidebar.multiselect("Compare with other stocks", [t for t in all_tickers if t != selected_stock])

# Date range
end_date = datetime.today()
start_date = st.sidebar.date_input("Start Date", end_date - timedelta(days=365))
end_date = st.sidebar.date_input("End Date", end_date)

# Chart type
use_candles = st.sidebar.checkbox("Show Candlesticks", value=True)

# Indicators
show_bbands = st.sidebar.checkbox("Show Bollinger Bands", value=True)

# ------------------ Download Data ------------------
tickers_to_download = [selected_stock] + compare_mode
data = yf.download(tickers_to_download, start=start_date, end=end_date, group_by="ticker", auto_adjust=False)

# Handle single vs multiple tickers for Adj Close
if isinstance(data.columns, pd.MultiIndex):
    adj_close = data.loc[:, (slice(None), "Adj Close")]
    adj_close.columns = adj_close.columns.droplevel(1)
else:
    adj_close = data[["Adj Close"]].rename(columns={"Adj Close": selected_stock})

adj_close = adj_close.dropna()

# Extract OHLC for main stock (for candlesticks & indicators)
if isinstance(data.columns, pd.MultiIndex):
    df = data[selected_stock].copy()
else:
    df = data.copy()

df = df.dropna()

# ------------------ Indicators ------------------
if show_bbands and "Close" in df.columns:
    df["MiddleBB"] = df["Close"].rolling(window=20).mean()
    df["UpperBB"] = df["MiddleBB"] + 2 * df["Close"].rolling(window=20).std()
    df["LowerBB"] = df["MiddleBB"] - 2 * df["Close"].rolling(window=20).std()

# ------------------ Plotting ------------------
fig = go.Figure()

# Candlestick / Line chart for main stock
if use_candles and {"Open", "High", "Low", "Close"}.issubset(df.columns):
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        name=selected_stock
    ))
else:
    fig.add_trace(go.Scatter(
        x=df.index, y=df["Close"], mode="lines", name=selected_stock
    ))

# Add Bollinger Bands
if show_bbands and "UpperBB" in df.columns:
    fig.add_trace(go.Scatter(x=df.index, y=df["UpperBB"], line=dict(color="gray", width=1), name="Upper BB", opacity=0.7))
    fig.add_trace(go.Scatter(x=df.index, y=df["LowerBB"], line=dict(color="gray", width=1), name="Lower BB", opacity=0.7))
    fig.add_trace(go.Scatter(x=df.index, y=df["MiddleBB"], line=dict(color="blue", width=1), name="Middle BB", opacity=0.7))

# Multi-stock comparison (line charts only)
for comp in compare_mode:
    if comp in adj_close.columns:
        fig.add_trace(go.Scatter(
            x=adj_close.index, y=adj_close[comp], mode="lines", name=comp
        ))

fig.update_layout(
    title=f"{selected_stock} Stock Price",
    xaxis_title="Date",
    yaxis_title="Price (USD)",
    template="plotly_white",
    xaxis_rangeslider_visible=False,
    height=700
)

st.plotly_chart(fig, use_container_width=True)

# ------------------ Show Data Table ------------------
st.subheader("Raw Data")
st.dataframe(df.tail(20))

