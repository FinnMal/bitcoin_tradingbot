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
import condition
import trade


def division(n, d):
    return n / d if d else 0


class Strategy:
    def __init__(self, db, tele, name='primary', in_strategy_test=False, color='blue', order=0, muted=False):
        self.db = db
        self.tele = tele
        self.name = name
        self.can_buy_conditions = []
        self.should_buy_conditions = []
        self.should_sell_conditions = []
        self.cur_trade = trade.Trade(0, self.db, self.tele, False, strategy=self.name)
        self.in_strategy_test = in_strategy_test
        self.color = color
        self.order = order
        self.last_sell = time.time_ns()
        self.muted = muted

    def get_name(self):
        return self.name

    def get_color(self):
        if self.color == 'blue':
            return '#0B84FF'
        elif self.color == 'green':
            return '#30D158'
        elif self.color == 'indigo':
            return '#5E5CE6'
        elif self.color == 'orange':
            return '#FF9F0A'
        elif self.color == 'pink':
            return '#FF375F'
        elif self.color == 'purple':
            return '#BF5AF2'
        elif self.color == 'red':
            return '#FF453A'
        elif self.color == 'teal':
            return '#64D2FF'
        elif self.color == 'yellow':
            return '#FFD609'
        return '#0B84FF'

    def get_color_name(self):
        return self.color

    def get_order(self):
        return self.order

    def buy(self, price):
        self.cur_trade = trade.Trade(price, self.db, self.tele, True, self.in_strategy_test, strategy=self.name)

    def sell(self):
        self.last_sell = time.time_ns()
        self.cur_trade.sell()

    def get_trade(self):
        return self.cur_trade

    def should_buy(self):
        if not self.cur_trade.is_active():
            should_buy = False
            info_message = ''
            for c in self.should_buy_conditions:
                if self.check_condition(c['conditions']):
                    should_buy = True
                    if c['text']:
                        print('SHOULD BUY: ' + c['text'])
                        info_message = info_message + '\n\n<i>'+self.name+'</i>\n<b>BUY:</b> ' + c['text']

            if should_buy:
                can_buy = True
                for c in self.can_buy_conditions:
                    if not self.check_condition(c['conditions']):
                        can_buy = False
                        if c['text']:
                            print('CANNOT BUY: ' + c['text'])
                            info_message = info_message + '\n\n<i>'+self.name+'</i>\n<b>CANNOT BUY:</b> ' + c['text']
                if not self.muted:
                    self.db.send_info_message(info_message)
                return can_buy
        return False

    def should_sell(self):
        info_message = ''
        should_sell = False
        if self.cur_trade.is_active():
            for c in self.should_sell_conditions:
                if self.check_condition(c['conditions'], self.cur_trade):
                    should_sell = True
                    if c['text']:
                        print('SHOULD SELL: ' + c['text'])
                        info_message = info_message + '\n\n<i>'+self.name+'</i>\n<b>SELL:</b> ' + c['text']

        if not self.muted:
            self.db.send_info_message(info_message)
        return should_sell

    def add_should_buy(self, c, text=""):
        c_obj = {
            'text': text,
            'conditions': c
        }
        self.should_buy_conditions.append(c_obj)

    def add_can_buy(self, c, text=""):
        c_obj = {
            'text': text,
            'conditions': c
        }
        self.can_buy_conditions.append(c_obj)

    def add_should_sell(self, c, text=""):
        c_obj = {
            'text': text,
            'conditions': c
        }
        self.should_sell_conditions.append(c_obj)

    def check_condition(self, conditions, trade=None):
        for c in conditions:
            if not c.check(self.db, trade, self.last_sell):
                return False
        return True
