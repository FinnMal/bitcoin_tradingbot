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


def division(n, d):
    return n / d if d else 0


class Trade:
    def __init__(self, buy_in, db, tel, active=True, in_strategy_test=False, strategy='primary'):
        self.buy_in = buy_in
        self.active = active
        self.cur_price = buy_in
        self.percentage = 0
        self.fee_percentage = 0
        self.profit = 0
        self.last_percentage = 0
        self.db = db
        self.telegram = tel
        self.db_id = self.db.create_trade(strategy)
        self.in_strategy_test = in_strategy_test
        self.balance_mes_id = -1
        self.strategy = strategy

        # if active:
        # balance = self.db.get_balance(strategy=strategy)
        # self.fee_percentage = 1/balance
        # self.db.set_balance(self.db.get_balance(strategy=strategy)-1, strategy=strategy)

    def get_message_id(self):
        return self.message_id

    def edit_message(self):
        print(self.in_strategy_test)
        if self.is_active() and not self.in_strategy_test:
            self.telegram.edit_message(self.message_id, "<b>CURRENT TRADE:</b>\n" + self.get_profit(True,
                                                                                                    True) + '€\n' + self.get_percentage(
                True, True) + '%\nTO LAST: ' + self.db.get_percentage_to_last(True, True) + '%')

    def get_buy_in(self):
        return self.buy_in

    def is_active(self):
        return self.active

    def set_active(self, a):
        self.active = a is True

    def set_current_price(self, p):
        self.cur_price = p
        self.last_percentage = self.get_percentage()
        self.percentage = (division(self.cur_price - self.buy_in, self.cur_price)) * 100
        self.profit = (self.get_percentage() / 100) * self.db.get_balance(strategy=self.strategy)
        self.db.set_trade_value(self.db_id, 'percentage', self.get_percentage())
        self.db.set_trade_value(self.db_id, 'profit', self.get_profit())

    def get_percentage(self, r=False, s=False):
        p = self.percentage
        if r:
            p = round(p, 2)
        if s:
            return str(p)
        return p

    def get_last_percentage(self, r=False, s=False):
        p = self.last_percentage
        if r:
            p = round(p, 2)
        if s:
            return str(p)
        return p

    def get_profit(self, r=False, s=False):
        p = self.profit
        if r:
            p = round(p, 2)
        if s:
            return str(p)
        return p

    def sell(self, balance_mes_id=-1):
        print('SELL')
        # print('WIN: ' + self.get_profit(True, True) + ' €')

        if self.get_profit() > self.db.get_max_profit():
            self.db.set_max_profit(self.get_profit())
            self.telegram.send_message('NEW MAX PROFIT: ' + str(round(self.get_profit(), 2)) + '€')

        if self.get_percentage() > self.db.get_max_percentage():
            self.db.set_max_percentage(self.get_percentage())
            self.telegram.send_message('NEW MAX PERCENTAGE: ' + str(round(self.get_percentage(), 2)) + '€')

        # save values
        self.db.set_trade_value(self.db_id, 'profit', self.get_profit())
        self.db.set_trade_value(self.db_id, 'ends_at', int(time.time_ns() / 1000000))

        # print('NEW BALANCE: ' + self.db.get_balance(True, True) + '€')

        print('BALANCE: ' + str(self.db.get_balance()))
        print('PROFIT: ' + str(self.get_profit()))
        print('PERCENTAGE: ' + str(self.get_percentage()))
        self.db.set_balance(self.db.get_balance(strategy=self.strategy) + self.get_profit(), self.strategy)

        if not self.in_strategy_test:
            if self.get_profit() > 0:
                self.db.send_balance_image(
                    '<b>TAKE PROFIT:</b>\n' + self.get_profit(True, True) + '€\n' + self.get_percentage(True,
                                                                                                        True) + '%')
            elif self.get_profit() < 0:
                self.db.send_balance_image(
                    '<b>CUT LOSS:</b>\n' + self.get_profit(True, True) + '€\n' + self.get_percentage(True, True) + '%')
            else:
                self.db.send_balance_image(
                    '<b>CUT TRADE:</b>\n' + self.get_profit(True, True) + '€\n' + self.get_percentage(True, True) + '%')
        else:
            if self.db.get_balance_mes_id() < 0:
                self.db.set_balance_mes_id(
                    self.telegram.send_message('BALANCE: ' + self.db.get_balance(True, True, self.strategy)))
            else:
                self.telegram.edit_message(self.db.get_balance_mes_id(),
                                           'BALANCE: ' + self.db.get_balance(True, True, self.strategy))

        self.set_active(False)

    def get_message_text(self):
        return "<b>CURRENT TRADE:</b>\n" + self.get_profit(True, True) + '€\n' + self.get_percentage(False,
                                                                                                     True) + '%\nTO LAST: ' + self.db.get_percentage_to_last(
            True, True) + '%'
