import time

import config


# данные про плотность на определенной цене
class PlotnostData:
    def __init__(self, symbol, side, price, volume):
        price = float(price)
        volume = float(volume)
        self.side = side
        self.symbol = symbol
        self.first_price = price
        self.price = price
        self.first_volume = volume
        self.volume = volume
        self.created_time = time.time()
        self.first_notify_time = None
        self.spoofer_notify_time = None
        self.half_closed = False

    def is_price_changed(self):
        return self.price != self.first_price

    # когда находим плотность в стакане, вызываем этот метод чтобы обновить цену и объем
    def update_data(self, price, volume):
        self.price, self.volume = price, volume

    def is_first_notified(self):
        return not (self.first_notify_time is None)

    def is_spoofer_notified(self):
        return not (self.spoofer_notify_time is None)

    def created_seconds_ago(self):
        return time.time() - self.created_time

    # как давно оповещали в первый раз
    def first_notify_seconds_ago(self):
        return time.time() - self.first_notify_time

    # как давно оповещали про спуфер
    def spoofer_notify_seconds_ago(self):
        return time.time() - self.spoofer_notify_time

    # сколько потерялось объема в процентном соотношении
    # >0 если объем стал больше
    # <0 если объем стал меньше
    def loss_percentage(self):
        return 100 * (self.volume - self.first_volume) / self.first_volume

    # насколько далеко находится в % от другой цены
    def from_price_percentage(self, price):
        return 100 * abs(self.price - price) / self.price

    # если объем велик по сравнению с 5минуткой, вернет true
    def pass_by_5minvolume(self, volume5min, multiplex):
        return self.volume > volume5min * multiplex

    # давно ли взаимодействовали с этой валютой
    def long_time_ago(self):
        if self.is_spoofer_notified():
            return self.spoofer_notify_seconds_ago() > config.holding_timeout_minutes * 60

        if self.is_first_notified():
            return self.first_notify_seconds_ago() > config.holding_timeout_minutes * 60
        return False
        # return self.created_seconds_ago() > config.holding_timeout_minutes * 60


# хранит в себе плотности по валюте и типу лонг-шорт
# мы помещаем сюда только ближайшие и большие плотности
class PlotnostStates:
    def __init__(self):
        self.data = {

        }

    def get_count(self):
        return len(self.data)

    def get_all(self):
        return list(self.data.values()).copy()

    def new_plotnost(self, symbol, side, plotnost):
        key = f"{symbol}-{side}"
        self.data[key] = plotnost

    def get_plotnost(self, symbol, side):
        key = f"{symbol}-{side}"
        if key in self.data:
            return self.data[key]
        return None

    def clear_plotnost(self, symbol, side):
        key = f"{symbol}-{side}"
        if key in self.data:
            del self.data[key]
