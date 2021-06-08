import json

with open('config.json') as config_file:
    data = json.load(config_file)

# во сколько раз объем плотности должен быть больше объема 5минутки
multiplex = data['multiplex']

telegram_token = data['telegram_token']

# на стадии инициализации надо сделать ~130 запросов. они делаются параллельно thread_count потоками
thread_count = data['thread_count']

# из скольки последних свеч брать максимум по объему в свече
check_candles = data['check_candles']

# в каком %м диапазоне ловим большие плотности
percentage = data['percentage']

# время, в течение которого следим спуфер или не спуфер
spoofer_minutes_after_notify = data['spoofer_timeout_minutes']

# время, через которое сбрасываем данные по валюте и плотности
holding_timeout_minutes = data['holding_timeout_minutes']

# куда слать уведомления
output_channel = data['output_channel']

# можно добавить валюты в черный список. их парсить не будет
blacklist_ticker = data['blacklist_ticker']

# глубина стакана, которую запрашиваем и храним
stock_depth = data['stock_depth']
