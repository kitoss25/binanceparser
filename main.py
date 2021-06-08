import time

from binance import ThreadedWebsocketManager

import config
import mycandles

import mydepth

from mybinance import binance_client


def get_needed_symbols():
    # берем все фьючерсные тикеры, которые есть также на споте, и которые не находятся в blacklist
    spot_ticker = binance_client.get_ticker()
    spot_symbols = [x['symbol'] for x in spot_ticker if x['symbol'].endswith("USDT")]

    fut_ticker = binance_client.futures_ticker()
    fut_symbols = [x['symbol'] for x in fut_ticker if x['symbol'].endswith("USDT")]

    fut_symbols = [x for x in fut_symbols if x in spot_symbols and x not in config.blacklist_ticker]
    return fut_symbols


# стаканы
# symbol->depthcache
depths = {

}

# symbol-> candlemanager
candles = {

}

import mytelegram


# инициализация начальных данных для валюты
def init_symbol(symbol):
    depth_manager = mydepth.MyDepthManager(symbol, limit=config.stock_depth)
    depths[symbol] = depth_manager
    depth_manager._init_cache()
    time.sleep(5)
    candles_manager = mycandles.MyCandlesManager(symbol, limit=config.stock_depth)
    candles_manager.init_candles()
    candles[symbol] = candles_manager
    time.sleep(5)


import mystorage

plotnost_states = mystorage.PlotnostStates()


def check_tick(symbol):
    symbol = symbol.upper()

    depth_manager, candles_manager = depths[symbol], candles[symbol]
    get_candles = candles_manager.get_candles()
    best_candle = max(get_candles, key=lambda x: float(x[5]))
    candle_v = float(best_candle[5])  # максимальный объем 5минутной свечи из последних свеч

    depth_cache = depth_manager.get_depth_cache()
    bids, asks = depth_cache.get_bids(), depth_cache.get_asks()
    best_bid, best_ask = bids[0], asks[0]

    price_to_bid = {float(x[0]): x[1] for x in bids}
    price_to_ask = {float(x[0]): x[1] for x in asks}

    price_to_bids_multiples = [mystorage.PlotnostData(x[0], x[1], 'bid', symbol) for x in bids if
                               x[1] > candle_v * config.multiplex]
    price_to_asks_multiples = [mystorage.PlotnostData(x[0], x[1], 'ask', symbol) for x in asks if
                               x[1] > candle_v * config.multiplex]

    stored_bid = plotnost_states.get_plotnost(symbol, "bid")
    stored_ask = plotnost_states.get_plotnost(symbol, "ask")

    def check_price_on_side(type, stored_plotn: mystorage.PlotnostData, price_to_multiples, price_to_plotnost,
                            best_data):
        if stored_plotn is None:
            # если еще не следили недавно за плотностью
            if len(price_to_multiples) == 0:
                return

            first_mul = price_to_multiples[0]
            if first_mul.from_price_percentage(best_data[0]) > config.percentage:
                return
            cons = first_mul.pass_by_5minvolume(candle_v, config.multiplex)
            if not cons:
                return
            plotnost_states.new_plotnost(symbol, type, first_mul)
            mytelegram.notify_first(symbol, type, first_mul, best_data, candle_v)
            return

        ###если уже есть данные по плотности###

        if stored_plotn.long_time_ago():
            # если давно взаимодействовали с плотностью - стираем данные
            plotnost_states.clear_plotnost(symbol, type)
            return

        # если прошло spoofer_minutes_after_notify минут с первого оповещения, то про спуфер не надо оповещать
        can_notify_spoofer = stored_plotn.first_notify_seconds_ago() < config.spoofer_minutes_after_notify * 60

        if stored_plotn.price not in price_to_plotnost:
            # если цена плотности пропала из стакана
            if not stored_plotn.is_spoofer_notified() and can_notify_spoofer:
                stored_plotn.spoofer_notify_time = time.time()
                print(stored_plotn.price)
                print(price_to_plotnost)
                print(f"{symbol} notify spoofer by not price in to plot")
                mytelegram.spoofer_notify(symbol, type, stored_plotn)
            return

        current_volume_at_price = price_to_plotnost[stored_plotn.price]
        stored_plotn.update_data(stored_plotn.price, current_volume_at_price)

        loss = stored_plotn.loss_percentage()

        if loss < -60:
            # проседает объем в 2х случаях
            # либо плотность реально разъело
            # либо плотность переставили
            # и в том и в другом случае необходимо уведомить о спуфере

            if not stored_plotn.is_spoofer_notified() and can_notify_spoofer:
                stored_plotn.spoofer_notify_time = time.time()
                print(f"{symbol} notify spoofer by loss ({loss})")
                mytelegram.spoofer_notify(symbol, type, stored_plotn)
            return

    check_price_on_side("bid", stored_bid, price_to_bids_multiples, price_to_bid, best_bid)
    check_price_on_side("ask", stored_ask, price_to_asks_multiples, price_to_ask, best_ask)

    # bid - покупка, лонги, зеленые
    # ask - продажа, шорты, красные


from multiprocessing.pool import ThreadPool


def main():
    twm = ThreadedWebsocketManager()
    twm.start()

    needed_symbols = get_needed_symbols()
    # инициализация
    tp = ThreadPool(config.thread_count)
    tp.map(init_symbol, needed_symbols)
    tp.close()
    tp.join()
    print("init depths done")

    # стримы для  multistream socket (см websocket доки binance)
    # kline https://binance-docs.github.io/apidocs/spot/en/#kline-candlestick-streams
    # depth diff https://binance-docs.github.io/apidocs/spot/en/#diff-depth-stream
    streams = {}
    for sym in needed_symbols:
        sl = sym.lower()
        streams[sl] = [f"{sl}@kline_5m",
                       f"{sl}@depth"]  # depth may be <symbol>@depth<levels> ie btcusdt@depth20

    def handle_socket_message(msg):
        stream = msg['stream']
        data = msg['data']
        e_type = data['e']
        if e_type == 'kline':
            symbol = data['s']
            candles[symbol.upper()].on_kline(data['k'])
            # print(f"kline {symbol}")
        elif e_type == 'depthUpdate':
            symbol = stream.split("@")[0].upper()
            if symbol not in depths:
                print(f"no {symbol} in depths!!")
                return
            # print(f"depth update {data['s']}")
            depths[symbol]._depth_event(data)
            # когда приходит depthUpdate, надо
            check_tick(symbol)

    def handle_socket_printmsg(msg):
        print(msg)

    for s in streams:
        ss = streams[s]
        twm.start_multiplex_socket(callback=handle_socket_message, streams=ss)
    print("started all streams")


if __name__ == '__main__':
    main()
