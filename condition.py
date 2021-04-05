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


class Condition:
    def __init__(self, function, param=None, operator='==', value=None, weekend_value=None, is_weekend=None,
                 value_range=None):
        if value_range is None:
            value_range = [0, 1]
        self.value = value
        self.function = function
        self.operator = operator
        self.is_weekend = is_weekend
        self.param = param
        self.value_range = value_range
        self.weekend_value = weekend_value

    def check(self, db, trade=None, last_sell=0):
        if db.is_weekend() and self.weekend_value is not None:
            self.value = self.weekend_value

        if self.value is None:
            return False

        value = None
        if self.function == 'trend_of_last_seconds':
            value = db.get_trend_of_last_seconds(self.param)
        elif self.function == 'percentage_to_last':
            value = db.get_percentage_to_last()
        elif self.function == 'is_weekend':
            value = db.is_weekend()
        elif self.function == 'percentage_to_before':
            value = db.get_percentage_to_before(self.param)
        elif self.function == 'percentage_to_high':
            value = db.get_percentage_to_high()
        elif self.function == 'trade.percentage':
            value = trade.get_percentage()
        elif self.function == 'trade.last_percentage':
            value = trade.get_last_percentage()
        elif self.function == 'has_change_in_last_ticks':
            value = db.has_change(self.param)
        elif self.function == 'milliseconds_to_last_sell':
            value = (time.time_ns()-last_sell)/1000000

        if value is not None:
            if self.operator == '>':
                return value > self.value
            elif self.operator == '<':
                return value < self.value
            elif self.operator == '==':
                return value == self.value
            elif self.operator == '!=':
                return value != self.value
            elif self.operator == '>=':
                return value >= self.value
            elif self.operator == '<=':
                return value <= self.value
            elif self.operator == 'range':
                return self.value_range[0] <= value <= self.value_range[1]

        else:
            print('ERROR: '+self.function+' not found')
        return False
