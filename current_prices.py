import yfinance as yf

data = yf.download("GR8.SG S7MB.F", period="1d", group_by="ticker")
print(data['S7MB.F']['Close'])