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
import database_handler
import trade
import telegram_bot
import threading
import logging
import strategy
import condition
import pydotplus
from sklearn import tree
from sklearn.datasets import load_iris
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
import collections
from binance.client import Client
from binance.websockets import BinanceSocketManager
from joblib import dump, load
import pandas as pd
import datetime as dt


# result = request_client.get_exchange_information()
# PrintMix.print_data(result.symbols)


class Main:
    def test_tick(self, tick):
        new_price = float(tick['c'])
        new_thread = threading.Thread(target=self.process_tick, args=(tick,))
        if self.cur_thread:
            if self.cur_thread.is_alive():
                return
        new_thread.start()
        self.cur_thread = new_thread

    def __init__(self):
        client = Client('****',
                        '****')
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)

        self.order_id = 0
        self.has_trade = False
        self.cur_thread = None
        self.cur_thread_started_at = 0
        self.file_last_modified = os.path.getmtime('main.py')
        self.tele = telegram_bot.Telegram(self)
        self.db = database_handler.DatabaseHandler(self.tele, False)
        self.db.create_trading_session()
        self.db.delete_tests()
        # self.db.delete_old_strategies()

        self.db.send_balance_image()

        self.strategies = []
        self.create_primary_strategy()
        self.db.set_strategies(self.strategies)
        self.db.set_balance(1000, strategy='primary')

        # load ai
        self.clf = load('tests/ai.joblib')

        with_strategy_test = False
        if len(sys.argv) > 1:
            with_strategy_test = sys.argv[1] == 'True'

        if not with_strategy_test:
            bm = BinanceSocketManager(client)
            bm.start_symbol_ticker_socket('BTCUSDT', self.test_tick)
            bm.start()

    def restart_on_file_change(self):
        cur_modified = os.path.getmtime('main.py')
        if self.file_last_modified != cur_modified:
            self.file_last_modified = cur_modified
            self.tele.send_message('restarting bot ...')
            python = sys.executable
            os.execl(python, python, *sys.argv)

    def process_tick(self, tick, in_strategy_test=False):
        self.restart_on_file_change()

        new_price = float(tick['c'])

        self.db.set_day_low(float(tick['l']) - 100)
        self.db.set_day_high(float(tick['h']) + 100)
        self.db.set_current_price(new_price)
        self.db.save_tick(int(tick['E']), new_price)

        for s in self.strategies:
            s.get_trade().set_current_price(new_price)

        for s in self.strategies:
            if s.should_sell():
                s.sell()

        for s in self.strategies:
            if s.should_buy():
                s.buy(new_price)

        if self.db.get_balance() == 0:
            sys.exit()

        trades = []
        for s in self.strategies:
            trades.append(s.get_trade())

        threading.Thread(target=self.db.send_price_image, args=(trades,)).start()

    def create_primary_strategy(self):
        # primary strategy
        s3 = strategy.Strategy(self.db, self.tele, name='primary', color='teal', order=1)

        # BUY
        c1 = condition.Condition(function='percentage_to_last', operator='>', value=0.01)
        c2 = condition.Condition(function='trend_of_last_seconds', param=70, operator='<', value=-0.24)
        s3.add_should_buy([c1, c2], text='percentage to last is positive')

        c1 = condition.Condition(function='percentage_to_last', operator='>', value=0)
        c2 = condition.Condition(function='trend_of_last_seconds', param=70, operator='<', value=0.4)
        s3.add_should_buy([c1, c2], text='percentage to last is positive')

        # c = condition.Condition(function='percentage_to_last', operator='<', value=-0.03)
        # s3.add_should_buy([c], text='high loss in cur tick')

        # SELL
        c1 = condition.Condition(function='percentage_to_last', operator='<', value=-0.01)
        c2 = condition.Condition(function='trade.percentage', operator='>=', value=0)
        s3.add_should_sell([c1, c2], text='high loss in cur tick and has profit')

        c1 = condition.Condition(function='percentage_to_last', operator='<', value=0)
        c2 = condition.Condition(function='trade.percentage', operator='<', value=-0.4)
        s3.add_should_sell([c1, c2], text='percentage to last is negative and profit is lower than -0.4%')

        # c = condition.Condition(function='trend_of_last_seconds', param=30, operator='<', value=0.005)
        # s3.add_should_sell([c], text='no significant change in last 30 seconds')

        c = condition.Condition(function='trade.percentage', operator='>=', value=1)
        s3.add_should_sell([c], text='enough profit (>0.1%)')

        # c = condition.Condition(function='trend_of_last_seconds', param=10, operator='<', value=0)
        # s3.add_should_sell([c], text='no positive trend in last 10 seconds')

        c1 = condition.Condition(function='trade.percentage', operator='>=', value=0)
        c2 = condition.Condition(function='trade.last_percentage', operator='<', value=0)
        s3.add_should_sell([c1, c2], text='has profit, after no profit')

        self.strategies.append(s3)
        # self.strategies.append(s2)
        # self.strategies.append(s1)

    def show_full_balance_view(self, update, context):
        self.tele.delete_message(update['message']['message_id'])
        self.db.set_show_full_balance_view(True)

    def hide_full_balance_view(self, update, context):
        self.tele.delete_message(update['message']['message_id'])
        self.db.set_show_full_balance_view(False)

    def show_restart_points(self, update, context):
        self.tele.delete_message(update['message']['message_id'])
        self.db.set_show_restart_points(True)

    def hide_restart_points(self, update, context):
        self.tele.delete_message(update['message']['message_id'])
        self.db.set_show_restart_points(False)

    def get_current_position_entry_price(self):
        result = self.request_client.get_position()
        return result[0].entryPrice


m = Main()
