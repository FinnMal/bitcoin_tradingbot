import sys
import random
import requests
from time import time, sleep
import websocket
import json
import ssl
import sqlite3
import matplotlib
import os
import time
import matplotlib.pyplot as plt
import trade
from datetime import datetime


def division(n, d):
    return n / d if d else 0


class DatabaseHandler:
    def __init__(self, tele, in_strategy_test):
        self.start_balance = 1000
        self.balance = -1
        self.telegram = tele
        self.cur_price = 0
        self.last_price = 0
        self.last_percentage = 0
        self.price_img_id = -1
        self.balance_img_id = -1
        self.info_mes_id = -1
        self.in_strategy_test = in_strategy_test
        self.is_test = str(0 if not self.in_strategy_test else 1)
        self.show_full_balance_view = False
        self.balance_mes_id = -1
        self.strategies = []
        self.show_restart_points = False

        self.day_high = -1
        self.day_low = -1

        min_max_values = self.get_value('SELECT MAX(percentage), MAX(profit) FROM trades')
        self.max_trade_percentage = min_max_values[0]
        self.max_trade_profit = min_max_values[1]
        if self.max_trade_percentage is None:
            self.max_trade_percentage = 0
        if self.max_trade_profit is None:
            self.max_trade_profit = 0

        # fetch balance from database
        res = self.get_value('SELECT * FROM balance WHERE strategy == "primary" ORDER BY time DESC LIMIT 1')
        print(res)
        if res:
            self.balance = res[1]
        if not self.balance > 0:
            self.telegram.send_message('Reset balance to ' + str(self.start_balance) + '€')
            self.balance = self.start_balance
            self.save_balance(self.balance, strategy='primary')
        self.start_balance = self.balance
        print('BALANCE: ' + str(self.balance))

    def get_max_profit(self):

        return self.max_trade_profit

    def get_max_percentage(self):
        return self.max_trade_percentage

    def set_max_profit(self, p):
        self.max_trade_profit = p

    def set_max_percentage(self, p):
        self.max_trade_percentage = p

    def set_strategies(self, strategies):
        self.strategies = strategies

    def execute(self, command):
        conn = sqlite3.connect("btc_database.db")
        c = conn.cursor()
        c.execute(command)
        conn.commit()
        conn.close()

    def get_value(self, command):
        conn = sqlite3.connect("btc_database.db")
        c = conn.cursor()
        c.execute(command)
        r = c.fetchone()
        conn.close()
        return r

    def get_values(self, command):
        conn = sqlite3.connect("btc_database.db")
        c = conn.cursor()
        c.execute(command)
        r = c.fetchall()
        conn.close()
        return r

    def get_balance_mes_id(self):
        return self.balance_mes_id

    def set_balance_mes_id(self, mes_id):
        self.balance_mes_id = mes_id

    def set_current_price(self, p):
        self.last_price = self.cur_price
        self.cur_price = p

        if self.last_price < 1:
            self.last_price = p

    def get_percentage_to_last(self, r=False, s=False):
        percentage = division((self.cur_price - self.last_price), self.cur_price) * 100
        if r:
            percentage = round(percentage, 2)

        if not s:
            return percentage
        else:
            return str(percentage)

    def get_percentage_to_before(self, d=0, r=False, s=False):
        last_price = 0
        before_last_price = 0
        res = self.get_values(
            'SELECT * FROM ticks WHERE is_test == ' + self.is_test + ' ORDER BY time DESC LIMIT 1 OFFSET ' + str(d + 1))

        if res:
            before_last_price = res[0][1]

        res = self.get_values(
            'SELECT * FROM ticks WHERE is_test == ' + self.is_test + ' ORDER BY time DESC LIMIT 1 OFFSET ' + str(d))
        if res:
            last_price = res[0][1]
        percentage = division((last_price - before_last_price), last_price) * 100
        if r:
            percentage = round(percentage, 2)
        if s:
            percentage = str(percentage)
        return percentage

    def get_trend(self, ticks=100, r=False, s=False):
        trend = 0
        res = self.get_values(
            'SELECT * FROM ticks WHERE is_test == ' + self.is_test + ' ORDER BY time DESC LIMIT ' + str(
                ticks) + ' OFFSET 2')

        if res:
            if len(res) > ticks - 1:
                if res[ticks - 1]:
                    first = res[0][1]
                    last = res[ticks - 1][1]
                    trend = division(first - last, first) * 100

        if r:
            trend = round(trend, 2)
        if s:
            trend = str(trend)
        return trend

    def get_trend_of_last_seconds(self, sec=25, r=False, s=False):
        cur_tick = self.get_value(
            'SELECT * FROM ticks WHERE is_test == ' + self.is_test + ' ORDER BY time DESC LIMIT 1 OFFSET 0')
        cur_tick_time = cur_tick[0]
        max_tick_time = cur_tick_time - sec * 1000

        last_ticks = self.get_values(
            'SELECT * FROM ticks WHERE time >= ' + str(max_tick_time) + ' AND is_test == ' + self.is_test)
        last_tick = last_ticks[0]
        trend = division(cur_tick[1] - last_tick[1], cur_tick[1]) * 100
        if r:
            trend = round(trend, 2)
        if s:
            trend = str(trend)
        return trend

    def get_range_of_last_seconds(self, sec=25, r=False, s=False):
        max_price = self.cur_price
        min_price = self.cur_price

        cur_tick = self.get_value(
            'SELECT * FROM ticks WHERE is_test == ' + self.is_test + ' ORDER BY time DESC LIMIT 1 OFFSET 0')
        cur_tick_time = cur_tick[0]
        max_tick_time = cur_tick_time - sec * 1000

        last_ticks = self.get_values(
            'SELECT price FROM ticks WHERE time >= ' + str(max_tick_time) + ' AND is_test == ' + self.is_test)

        for tick in last_ticks:
            if tick[0] > max_price:
                max_price = tick[0]

            if tick[0] < min_price:
                min_price = tick[0]

        price_range = division(max_price - min_price, max_price) * 100
        if r:
            price_range = round(price_range, 2)
        if s:
            price_range = str(price_range)
        return price_range

    def has_change(self, ticks=20):
        for i in range(0, ticks):
            if self.get_percentage_to_before(i, True) != 0:
                return True
        return False

    def save_value(self, command):
        conn = sqlite3.connect("btc_database.db")
        c = conn.cursor()
        c.execute(command)
        conn.commit()
        conn.close()

    def save_tick(self, tick_time, price):
        self.save_value('INSERT INTO ticks VALUES (' + str(tick_time) + ', ' + str(price) + ', ' + self.is_test + ');')

    def create_trade(self, strategy='primary'):
        db_id = self.get_value('SELECT count(*) FROM trades')[0] + 1
        self.execute('INSERT INTO trades (starts_at, percentage, profit, trend, percentage_to_high, '
                     'percentage_to_low, percentage_to_last, is_test, strategy) VALUES (' + str(
            int(time.time_ns() / 1000000)) + ', 0, 0, ' + self.get_trend(100, False,
                                                                         True) + ', ' + self.get_percentage_to_high(
            False, True) + ', ' + self.get_percentage_to_low(False, True) + ', ' + self.get_percentage_to_last(False,
                                                                                                               True) + ', ' + self.is_test + ', "' + str(
            strategy) + '");')
        return db_id

    def set_trade_value(self, trade_id, value_name, value):
        self.execute('UPDATE trades SET ' + value_name + ' = "' + str(value) + '" WHERE id = ' + str(trade_id))

    def get_balance(self, r=False, s=False, strategy="primary"):
        balance_info = self.get_value(
            'SELECT amount FROM balance WHERE strategy == "' + strategy + '" ORDER BY time DESC LIMIT 1')
        if balance_info:
            b = balance_info[0]
        else:
            b = self.get_balance()
        if r:
            b = round(b, 2)
        if s:
            return str(b)
        return b

    def set_balance(self, b, strategy='primary'):
        if strategy == 'primary':
            self.balance = b
        self.save_balance(b, strategy)

    def save_balance(self, b, strategy='primary'):
        self.save_value(
            'INSERT INTO balance VALUES (' + str(int(time.time_ns() / 1000000)) + ', ' + str(
                b) + ', ' + self.is_test + ', "' + strategy + '");')
        print('BALANCE SAVED -> ' + str(round(b, 2)) + '€')

    def get_day_high(self):
        return self.day_high

    def set_day_high(self, high):
        self.day_high = high

    def set_day_low(self, low):
        self.day_low = low

    def get_day_low(self):
        return self.day_low

    def get_percentage_to_high(self, r=False, s=False):
        percentage = division(self.day_high - self.cur_price, self.day_high) * 100
        if r:
            percentage = round(percentage, 2)
        if s:
            percentage = str(percentage)
        return percentage

    def get_percentage_to_low(self, r=False, s=False):
        percentage = division(self.cur_price - self.day_low, self.day_low) * 100
        if r:
            percentage = round(percentage, 2)
        if s:
            percentage = str(percentage)
        return percentage

    def send_price_image(self, trades):
        primary_trade = trades[0]
        # self.telegram.delete_message(self.price_img_id)
        if self.in_strategy_test:
            return

        if self.price_img_id < 0:
            self.price_img_id = self.telegram.send_image(self.export_price_image())
        else:
            if primary_trade.is_active():
                text = "<b>CURRENT TRADE:</b>\n" + primary_trade.get_profit(True,
                                                                            True) + '€\n' + primary_trade.get_percentage(
                    False, True) + '%\nTO LAST: ' + primary_trade.db.get_percentage_to_last(True,
                                                                                            True) + '%\nTREND OF LAST 70 SEC: ' + self.get_trend_of_last_seconds(
                    70,
                    True,
                    True) + '\nTREND OF LAST 10 SEC: ' + self.get_trend_of_last_seconds(10,
                                                                                        True,
                                                                                        True)
                self.telegram.edit_image(self.price_img_id, self.export_price_image(), text)

            else:
                self.telegram.edit_image(self.price_img_id, self.export_price_image(),
                                         'PERCENTAGE TO LAST: ' + self.get_percentage_to_last(True,
                                                                                              True) + '%\nPERCENTAGE TO HIGH: ' + self.get_percentage_to_high(
                                             True, True) + '%\nPERCENTAGE TO LOW: ' + self.get_percentage_to_low(True,
                                                                                                                 True) + '%\nTREND: ' + self.get_trend(
                                             100, True,
                                             True) + '%\nTREND OF LAST 70 SEC: ' + self.get_trend_of_last_seconds(70,
                                                                                                                  True,
                                                                                                                  True) + '\nTREND OF LAST 10 SEC: ' + self.get_trend_of_last_seconds(
                                             10,
                                             True,
                                             True))

    def send_balance_image(self, caption=""):
        if self.in_strategy_test:
            return

        caption = caption + '\n' + self.get_balance_stats_str()

        if self.balance_img_id < 0:
            self.balance_img_id = self.telegram.send_image(self.export_balance_image(), caption)
        else:
            self.telegram.edit_image(self.balance_img_id, self.export_balance_image(), caption)

    def send_info_message(self, text=""):
        if self.in_strategy_test or not text:
            return

        if self.info_mes_id < 0 or self.info_mes_id < self.price_img_id:
            if self.info_mes_id > 0:
                self.telegram.delete_message(self.info_mes_id)
            self.info_mes_id = self.telegram.send_message(text)
        else:
            self.telegram.edit_message(self.info_mes_id, text)

    def get_balance_stats_str(self):
        balance_24h_ago = self.get_value('SELECT * FROM balance WHERE time > ' + str(
            int(
                time.time_ns() / 1000000) - 86400000) + ' AND strategy == "primary" AND is_test == ' + self.is_test + ' ORDER BY time LIMIT 1')
        if balance_24h_ago:
            balance_24h_ago = balance_24h_ago[1]
        else:
            balance_24h_ago = 0

        percentage_24h = division(self.get_balance() - balance_24h_ago, balance_24h_ago) * 100

        strategy_str = ''
        for strategy in self.strategies:
            if strategy.get_name() != 'primary':
                strategy_str = strategy_str + '\nStrategy <b>' + strategy.get_name() + '</b>: ' + self.get_balance(True,
                                                                                                                   True,
                                                                                                                   strategy.get_name()) + '€ (' + str(
                    round(self.get_average_percentage_per_day(strategy.get_name()), 2)) + '%)'

        return '\n<b>BALANCE:</b> ' + self.get_balance(True, True) + '€\n<b>BALANCE 24H AGO: </b>' + str(
            round(balance_24h_ago, 2)) + '€\n<b>PROFIT IN LAST 24h:</b> ' + str(
            round(self.get_balance() - balance_24h_ago, 2)) + '€ (' + str(
            round(percentage_24h, 2)) + '%)\n<b>PROFIT PER DAY: </b>' + str(
            round(self.get_average_percentage_per_day(), 2)) + '%\n' + strategy_str

    def get_time_to_break_even(self, percentage_24h):
        seconds = 0
        first_balance = \
            self.get_value(
                'SELECT * FROM balance WHERE is_test == ' + self.is_test + ' AND strategy == "primary" ORDER BY time LIMIT 1')

        if first_balance:
            first_balance = first_balance[1]
        else:
            first_balance = self.start_balance

        percentage_1_sec = percentage_24h / 86400

        b = self.get_balance()
        while b < first_balance * 2:
            seconds = seconds + 1
            b = b + b * percentage_1_sec / 100

        return self.sec_to_str(seconds) * 100

    def get_average_percentage_per_day(self, strategy='primary'):
        balance = self.get_balance(strategy=strategy)
        timestamp = int(time.time_ns() / 1000000)

        first_timestamp = 0
        first_balance = self.get_value(
            'SELECT * FROM balance WHERE is_test == ' + self.is_test + ' AND strategy == "' + strategy + '" ORDER BY time LIMIT 1')
        if first_balance:
            first_timestamp = int(first_balance[0])
            first_balance = int(first_balance[1])

        days_active = (timestamp - first_timestamp) / 86400000
        return (division(balance, first_balance) ** division(1, days_active) - 1) * 100

    def sec_to_str(self, s):
        s = round(s)
        if s < 60:
            return str(s) + " SECONDS"
        elif s < 3600:
            minutes = round(s / 60)
            seconds = round(s - (minutes * 60))
            if seconds > 0:
                return str(minutes) + ' MIN., ' + str(seconds) + ' SEC.'
            else:
                return str(minutes) + ' MINUTES'
        elif s < 86400:
            hours = round(s / 3600)
            minutes = round((s - (hours * 3600)) / 60)
            if minutes > 0:
                return str(hours) + ' STD., ' + str(minutes) + ' MIN.'
            else:
                return str(hours) + ' HOURS'
        else:
            days = round(s / 86400)
            hours = (s - days * 86400) / 3600
            if hours > 0:
                return str(days) + ' DAYS, ' + str(hours) + ' H.'
            else:
                return str(days) + ' DAYS'

    def export_price_image(self):
        if not self.in_strategy_test:
            last_ticks = self.get_values(
                'SELECT * FROM ticks WHERE is_test == ' + self.is_test + ' ORDER BY time DESC LIMIT 100')
            x_axis = []
            y_axis = []
            x = 0

            for tick in reversed(last_ticks):
                x = x + 1
                x_axis.insert(0, x)
                y_axis.insert(0, tick[1])

            plt.style.use('dark_background')
            plt.plot(x_axis, y_axis, color="#FF453A")

            # add horizontal line
            for s in self.strategies:
                if s.get_trade().is_active():
                    plt.hlines(y=s.get_trade().get_buy_in(), zorder=s.get_order(), xmin=0, xmax=100,
                               color=s.get_color())

            plt.xlabel('Time')
            plt.ylabel('Price')
            plt.savefig('graph.png')
            plt.clf()
        return 'graph.png'

    def export_balance_image(self):
        if not self.in_strategy_test:
            for s in self.strategies:
                if self.show_full_balance_view:
                    last_balances = self.get_values(
                        'SELECT * FROM balance WHERE is_test == ' + self.is_test + ' AND strategy == "' + s.get_name() + '" ORDER BY time DESC')
                else:
                    last_balances = self.get_values(
                        'SELECT * FROM balance WHERE is_test == ' + self.is_test + ' AND strategy == "' + s.get_name() + '" AND time > ' + str(
                            int(time.time_ns() / 1000000) - 90000000) + ' ORDER BY time DESC')

                if len(last_balances) > 0:
                    x_axis = []
                    y_axis = []
                    x = 0
                    for b in reversed(last_balances):
                        x = x + 1
                        timestamp = int(b[0]) / 1000.0
                        x_axis.insert(0, datetime.fromtimestamp(timestamp))
                        y_axis.insert(0, b[1])

                    ax = plt.gca()
                    xfmt = matplotlib.dates.DateFormatter('%H:%M')
                    ax.xaxis.set_major_formatter(xfmt)

                    plt.plot(x_axis, y_axis, color=s.get_color(), zorder=s.get_order())

            if self.show_restart_points:
                if self.show_full_balance_view:
                    sessions = self.get_values('SELECT starts_at FROM sessions')
                else:
                    sessions = self.get_values('SELECT starts_at FROM sessions WHERE starts_at > ' + str(
                        int(time.time_ns() / 1000000) - 90000000))
                for s in sessions:
                    timestamp = int(s[0]) / 1000.0
                    if timestamp > 0:
                        date = datetime.fromtimestamp(timestamp)
                        if date:
                            plt.axvline(x=date, alpha=0.8, color="#FF453A", zorder=-2)

            plt.style.use('dark_background')
            plt.xticks(rotation=20)

            plt.xlabel('Time')
            plt.ylabel('Balance')
            plt.savefig('graph.png')
            plt.clf()
            # bot.send_photo(chat_id=866153882, photo=open('graph.png', 'rb'), caption=caption,
            # parse_mode=telegram.ParseMode.HTML)
        return 'graph.png'

    def delete_tests(self):
        self.execute('DELETE FROM ticks WHERE is_test == 1')
        self.execute('DELETE FROM trades WHERE is_test == 1')
        self.execute('DELETE FROM balance WHERE is_test == 1')

    def delete_old_strategies(self):
        self.execute('DELETE FROM trades WHERE strategy != "primary"')
        self.execute('DELETE FROM balance WHERE strategy != "primary"')

    def set_show_full_balance_view(self, v):
        self.show_full_balance_view = v
        self.send_balance_image()

    def set_show_restart_points(self, v):
        self.show_restart_points = v
        self.send_balance_image()

    def is_weekend(self):
        return datetime.today().weekday() > 4

    def create_trading_session(self):
        db_id = self.get_value('SELECT count(*) FROM sessions')[0] + 1
        self.execute('INSERT INTO sessions (ID, starts_at) VALUES (' + str(db_id) + ', ' + str(
            int(time.time_ns() / 1000000)) + ');')
        return db_id

    def get_ai_values(self):
        return [self.get_percentage_to_before(1), self.get_percentage_to_last(), 0, self.get_trend_of_last_seconds(120),
                self.get_trend_of_last_seconds(90), self.get_trend_of_last_seconds(70),
                self.get_trend_of_last_seconds(60),
                self.get_trend_of_last_seconds(50), self.get_trend_of_last_seconds(40),
                self.get_trend_of_last_seconds(30),
                self.get_trend_of_last_seconds(25), self.get_trend_of_last_seconds(20),
                self.get_trend_of_last_seconds(15),
                self.get_trend_of_last_seconds(10), self.get_trend_of_last_seconds(5)]
