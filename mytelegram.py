import telebot
import config
import traceback
import time

telegram_bot = telebot.TeleBot(config.telegram_token)


def human_format(num):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    # add more suffixes if you need them
    return '%.3f%s' % (num, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])


def spoofer_notify(symbol, side, plotnost):
    usd_volume = "%.4f" % (float(plotnost.price) * float(plotnost.volume))
    trademark = "S"
    side_img = "🔴" if side == 'ask' else '🟢'
    telega_text = f"""⚠️ SPOOFER {side_img} {trademark} {symbol} 📶{human_format(float(plotnost.volume))} (${human_format(float(usd_volume))}) at {plotnost.price}"""
    print(telega_text)
    try:
        telegram_bot.send_message(config.output_channel, telega_text)
    except:
        traceback.print_exc()
        print("sleeping")
        time.sleep(60)


def notify_first(symbol, side, plotnost, best_data, value):
    usd_volume = "%.4f" % (float(plotnost.price) * float(plotnost.volume))
    best_price = best_data[0]
    price_delta = abs(plotnost.price - best_price) / best_price * 100
    price_delta_formatted = "%.2f" % price_delta
    side_img = "🔴" if side == 'ask' else '🟢'
    telega_text = f"""{side_img} {symbol} 📶{human_format(float(plotnost.volume))} (${human_format(float(usd_volume))}) at {plotnost.price} ↕️{price_delta_formatted}% 5min:{human_format(float(value))}"""
    print(telega_text)
    try:
        telegram_bot.send_message(config.output_channel, telega_text)
    except:
        traceback.print_exc()
        print("sleeping")
        time.sleep(60)
