import config
from mybinance import binance_client


# нужен для хранения и обновления свеч определенного symbol
class MyCandlesManager:
    def __init__(self, symbol, limit, interval="5m"):
        self.symbol = symbol
        self.candles = []
        self.limit = limit
        self.interval = interval

    def init_candles(self):
        self.candles = binance_client.get_klines(symbol=self.symbol, interval=self.interval, limit=self.limit)

    def on_kline(self, data):
        now_candle = self._read_kline(data)
        if len(self.candles) == 0:
            self.candles.append(now_candle)
            return
        last_candle = self.candles[-1]
        if last_candle[0] == now_candle[0]:
            self.candles[-1] = now_candle
        elif last_candle[0] < now_candle[0]:
            if len(self.candles) == config.check_candles:
                del self.candles[0]
            self.candles.append(now_candle)

    def get_candles(self):
        return self.candles.copy()

    # по websocket свеча приходит в другом формате, преобразуем к нужному
    def _read_kline(self, kline):
        return [
            kline['t'],
            kline['o'],
            kline['h'],
            kline['l'],
            kline['c'],
            kline['v'],
            kline['T'],
            kline['q'],
            kline['n'],
            kline['V'],
            kline['Q'],
            kline['B']
        ]

    ###[
    # 1499040000000,      // Open time
    # "0.01634790",       // Open
    # "0.80000000",       // High
    # "0.01575800",       // Low
    # "0.01577100",       // Close
    # "148976.11427815",  // Volume
    # 1499644799999,      // Close time
    # "2434.19055334",    // Quote asset volume
    # 308,                // Number of trades
    # "1756.87402397",    // Taker buy base asset volume
    # "28.46694368",      // Taker buy quote asset volume
    # "17928899.62484339" // Ignore.
    # ]##
