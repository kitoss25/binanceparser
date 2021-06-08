import time

from binance.depthcache import DepthCache

from mybinance import binance_client


# взят из python-binance чтобы хранить стакан
class MyDepthManager:
    def __init__(self, symbol, limit=30):
        self._depth_cache = None
        self._last_update_id = None
        self._refresh_interval = None
        self._symbol = symbol
        self._limit = limit

    def _init_cache(self):

        self._last_update_id = None
        self._depth_message_buffer = []

        res = binance_client.get_order_book(symbol=self._symbol, limit=self._limit)

        """Initialise the depth cache calling REST endpoint

        :return:
        """

        # initialise or clear depth cache
        self._depth_cache = DepthCache(self._symbol, conv_type=float)

        # set a time to refresh the depth cache
        if self._refresh_interval:
            self._refresh_time = int(time.time()) + self._refresh_interval

        self._apply_orders(res)
        for bid in res['bids']:
            self._depth_cache.add_bid(bid)
        for ask in res['asks']:
            self._depth_cache.add_ask(ask)

        # set first update id
        self._last_update_id = res['lastUpdateId']

        # Apply any updates from the websocket
        for msg in self._depth_message_buffer:
            self._process_depth_message(msg)

        # clear the depth buffer
        self._depth_message_buffer = []

    def _apply_orders(self, msg):
        for bid in msg.get('b', []) + msg.get('bids', []):
            self._depth_cache.add_bid(bid)
        for ask in msg.get('a', []) + msg.get('asks', []):
            self._depth_cache.add_ask(ask)

        # keeping update time
        self._depth_cache.update_time = msg.get('E') or msg.get('lastUpdateId')

    def get_depth_cache(self):
        """Get the current depth cache

        :return: DepthCache object

        """
        return self._depth_cache

    def _depth_event(self, msg):
        """Handle a depth event

        :param msg:
        :return:

        """

        if not msg:
            return None

        if 'e' in msg and msg['e'] == 'error':
            return None

        return self._process_depth_message(msg)

    def _process_depth_message(self, msg):
        """Process a depth event message.

        :param msg: Depth event message.
        :return:

        """

        if self._last_update_id is None:
            # Initial depth snapshot fetch not yet performed, buffer messages
            self._depth_message_buffer.append(msg)
            return

        if msg['u'] <= self._last_update_id:
            # ignore any updates before the initial update id
            return
        elif msg['U'] != self._last_update_id + 1:
            # if not buffered check we get sequential updates
            # otherwise init cache again
            self._init_cache()

        # add any bid or ask values
        self._apply_orders(msg)

        # call the callback with the updated depth cache
        res = self._depth_cache

        self._last_update_id = msg['u']

        # after processing event see if we need to refresh the depth cache
        if self._refresh_interval and int(time.time()) > self._refresh_time:
            self._init_cache()

        return res
