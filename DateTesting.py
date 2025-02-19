import yfinance as yf
data = yf.download("SPY", start="2023-12-15", end="2024-1-31")
print(data)