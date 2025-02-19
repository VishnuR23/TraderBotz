from lumibot.brokers import Alpaca 
from lumibot.backtesting import YahooDataBacktesting
from lumibot.strategies import Strategy
from lumibot.traders import Trader 
from datetime import datetime
from alpaca_trade_api import REST
from datetime import timedelta
from mlstrat import estimate_sentiment
import time

API_KEY = "PK7PQB1OBJ1DS670PBGN"
APi_SECRET = "4MB6ZaQiFF5LOfxUBMQg6T4GPfxPn5emobxgXVNc"
BASE_URL = "https://paper-api.alpaca.markets/v2"

ALPACA_CREDS = {
    "API_KEY" : API_KEY,
    "API_SECRET" : APi_SECRET,
    "PAPER": True
}

class TraderStrat(Strategy): 
    def initialize(self, symbol:str = "SPY", cash_at_risk:float = 0.3):
        self.symbol = symbol
        self.sleeptime = "24H"
        self.last_trade = None
        self.cash_at_risk = cash_at_risk
        self.api = REST(base_url = BASE_URL, key_id = API_KEY, secret_key= APi_SECRET)
    
    def position_sizing(self):
        cash = self.get_cash()
        last_price = self.get_last_price(self.symbol)
        quantity = round(cash * self.cash_at_risk / last_price, 0)
        return cash, last_price, quantity
    
    def get_dates(self):
        today = self.get_datetime()
        prior = today - timedelta(days = 3)
        return today.strftime('%Y-%m-%d'), prior.strftime('%Y-%m-%d')
    
    def get_sentiment(self):
        today, prior = self.get_dates()
        news = self.api.get_news(symbol = self.symbol, start = prior, end = today)

        news = [ev.__dict__["_raw"]["headline"] for ev in news]
        probability, sentiment = estimate_sentiment(news)
        return probability, sentiment

    def on_trading_iteration(self):
        cash, last_price, quantity = self.position_sizing()
        probability, sentiment = self.get_sentiment()
        if cash > last_price: 
            if sentiment == "positive" and probability > 0.999:
                if self.last_order == "sell":
                    self.sell_all()
                order = self.create_order(
                    self.symbol,
                    quantity,
                    "buy",
                    type = "bracket",
                    take_profit_price = last_price * 1.20,
                    stop_loss_price = last_price * 0.95
                )
                self.submit_order(order)
                self.last_trade = "buy"
            elif sentiment == "negative" and probability > 0.999:
                if self.last_order == "buy":
                    self.sell_all()
                order = self.create_order(
                    self.symbol,
                    quantity,
                    "sell",
                    type = "bracket",
                    take_profit_price = last_price * 0.8,
                    stop_loss_price = last_price * 1.05
                )
                self.submit_order(order)
                self.last_trade = "sell"

start_date = datetime(2023, 12, 15)
end_date = datetime(2023, 12, 31)
time.sleep(3)
broker = Alpaca(ALPACA_CREDS)
strategy = TraderStrat(name = 'tradestrat', broker = broker, parameters = {"symbol": "SPY", "cash_at_risk": .3})

strategy.backtest(
    YahooDataBacktesting,
    start_date,
    end_date,
    parameters = {"symbol": "SPY", "cash_at_risk": .3}
)