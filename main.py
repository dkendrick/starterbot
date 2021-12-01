import bybit
import math
import pandas as pd
import time

from datetime import datetime
from dateutil.relativedelta import relativedelta

# settings
num_orders = 3
order_size = 1
order_distance = 10
sl_risk = 0.03
tp_distance = 5
api_key = "YOUR_KEY"
api_secret = "YOUR_SECRET"

client = bybit.bybit(test=False, api_key=api_key, api_secret=api_secret)
mid_price = 0

def place_order(price, side, stop_loss, take_profit):
    order = client.Order.Order_new(
        side=side,
        symbol="BTCUSD",
        order_type="Limit",
        qty=order_size, price=price,
        time_in_force="GoodTillCancel",
        take_profit=take_profit,
        stop_loss=stop_loss
    )
    order.result()


def get_result_from_response(response):
    result = response.result()[0] or {}

    return result.get('result', {})


def ensure_buy_order(price, stop_loss, take_profit):
    if ((last_price - order_distance) < price):
        return

    existing_order = list(
        filter(lambda elem: int(elem['price']) == price, buy_orders))
    if any(existing_order):
        existing_order = existing_order[0]

        if (int(float(existing_order['take_profit'])) == take_profit):
            return
        else:
            print("cancelling order, tp has moved")
            close_order(existing_order)

    print("> opening buy order at {} with sl: {} and tp: {}".format(
        price, stop_loss, take_profit))
    place_order(price, "Buy", stop_loss, take_profit)


def ensure_sell_order(price, stop_loss, take_profit):
    if ((last_price + order_distance) > price):
        return

    existing_order = list(
        filter(lambda elem: int(elem['price']) == price, sell_orders))
    if any(existing_order):
        existing_order = existing_order[0]
        if (int(float(existing_order['take_profit'])) == take_profit):
            return
        else:
            print("cancelling order, tp has moved")
            close_order(existing_order)

    print("> opening sell order at {} with sl: {} and tp: {}".format(
        price, stop_loss, take_profit))
    place_order(price, "Sell", stop_loss, take_profit)


def close_order(order):
    client.Order.Order_cancel(
        symbol="BTCUSD", order_id=order['order_id']).result()


def close_all_orders(order_list):
    [close_order(order) for order in order_list]


def check_and_update_orders():
    print("> check and update orders running")
    my_position = get_result_from_response(
        client.Positions.Positions_myPosition(symbol="BTCUSD"))
    position_side = my_position['side']
    entry_price = round(float(my_position['entry_price']))
    sl_distance = mid_price * sl_risk

    for n in range(0, num_orders):
        order_offset = (n + 1) * order_distance
        buy_price = round_to_order_distance(last_price - order_offset)
        sell_price = round_to_order_distance(last_price + order_offset)

        if position_side == "Buy":
            buy_tp = round_to_order_distance(
                entry_price + (order_distance * tp_distance))
            ensure_buy_order(buy_price, mid_price - sl_distance, buy_tp)
            close_all_orders(sell_orders)

        elif position_side == "Sell":
            sell_tp = round_to_order_distance(
                entry_price - (order_distance * tp_distance))
            ensure_sell_order(sell_price, mid_price + sl_distance, sell_tp)
            close_all_orders(buy_orders)

        else:
            buy_tp = round_to_order_distance(
                last_price + (order_distance * tp_distance))
            ensure_buy_order(buy_price, mid_price - sl_distance, buy_tp)

            sell_tp = round_to_order_distance(
                last_price - (order_distance * tp_distance))
            ensure_sell_order(sell_price, mid_price + sl_distance, sell_tp)


def round_to_order_distance(num):
    if num is None or math.isnan(num):
        return

    return order_distance * round(float(num) / order_distance)


def calculate_mid_price():
    kline = pd.DataFrame([])

    for n in range(1, 4):
        from_date = datetime.now() + relativedelta(hours=-(n*3))
        unix_from_date = time.mktime(from_date.timetuple())
        candle_info = get_result_from_response(client.Kline.Kline_get(
            symbol="BTCUSD", interval="1", **{'from': unix_from_date}))
        kline = kline.append(candle_info)

    kline = kline.drop_duplicates()
    kline["time"] = pd.to_datetime(kline["open_time"], unit='s')
    kline = kline.sort_values(by=["time"])
    kline[["open", "high", "low", "close", "volume"]] = kline[[
        "open", "high", "low", "close", "volume"]].apply(pd.to_numeric)
    kline.drop(columns=["open_time", "symbol",
               "interval", "turnover"], inplace=True)
    kline['ma'] = kline['close'].rolling(200).mean()
    kline['rounded_ma'] = kline['ma'].apply(
        lambda n: round_to_order_distance(n))
    mid_price = kline['rounded_ma'].iloc[-1]

    print("> mid price {}".format(mid_price))

    return mid_price


last_price = get_result_from_response(
    client.Market.Market_tradingRecords(symbol="BTCUSD", limit=1))[0]['price']
open_orders = get_result_from_response(
    client.Order.Order_query(symbol="BTCUSD", order_id=""))

buy_orders = list(filter(lambda elem: elem['side'] == "Buy", open_orders))
sell_orders = list(filter(lambda elem: elem['side'] == "Sell", open_orders))

print(buy_orders)

mid_price = calculate_mid_price()

check_and_update_orders()
