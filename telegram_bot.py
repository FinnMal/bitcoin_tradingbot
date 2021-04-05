import sys
import random
import requests
from time import time, sleep
import websocket
import json
import ssl
import sqlite3
import telegram
import matplotlib
import os
import time
from telegram import InputMediaPhoto
import matplotlib.pyplot as plt
import logging


class Telegram:
    def __init__(self, main):
        self.mainObj = main
        self.last_mes_send_at = time.time()
        self.bot = telegram.Bot('****')
        self.bot.send_message(chat_id=0, text='TradingBot started')
        """
        self.updater = Updater(token='****', use_context=True)
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)

        start_handler = CommandHandler('start_strategy_test', self.start_strategy_test)
        self.updater.dispatcher.add_handler(start_handler)

        show_full_balance_view = CommandHandler('show_full_balance_view', self.mainObj.show_full_balance_view)
        self.updater.dispatcher.add_handler(show_full_balance_view)

        hide_full_balance_view = CommandHandler('hide_full_balance_view', self.mainObj.hide_full_balance_view)
        self.updater.dispatcher.add_handler(hide_full_balance_view)

        show_restart_points = CommandHandler('show_restart_points', self.mainObj.show_restart_points)
        self.updater.dispatcher.add_handler(show_restart_points)

        hide_restart_points = CommandHandler('hide_restart_points', self.mainObj.hide_restart_points)
        self.updater.dispatcher.add_handler(hide_restart_points)

        self.updater.start_polling()
        """

    def start_strategy_test(self, update, context):
        self.send_message('restarting bot ...')
        python = sys.executable
        os.execl(python, python, 'main.py'.encode(), 'True')

    def send_message(self, text=""):
        self.last_mes_send_at = time.time()
        mes = self.bot.send_message(chat_id=866153882, text=text, parse_mode=telegram.ParseMode.HTML)
        return mes.message_id

    def send_image(self, img, caption=""):
        self.last_mes_send_at = time.time()
        mes = self.bot.send_photo(chat_id=866153882, photo=open(img, 'rb'), caption=caption,
                                  parse_mode=telegram.ParseMode.HTML)
        return mes.message_id

    def edit_message(self, mes_id, text=""):
        if not text:
            return

        if time.time() - self.last_mes_send_at < 1:
            return

        self.last_mes_send_at = time.time()
        try:
            self.bot.edit_message_text(chat_id=866153882, message_id=mes_id, text=text,
                                       parse_mode=telegram.ParseMode.HTML)
        except Exception as e:
            pass

    def edit_image(self, mes_id, img, text=""):
        if time.time() - self.last_mes_send_at < 1:
            return

        self.last_mes_send_at = time.time()
        try:
            self.bot.edit_message_media(chat_id=866153882, message_id=mes_id, media=InputMediaPhoto(
                media=open(img, 'rb'),
                caption=text,
                parse_mode=telegram.ParseMode.HTML
            ))
        except Exception as e:
            pass

    def delete_message(self, mes_id):
        try:
            if mes_id > 0:
                self.bot.delete_message(chat_id=866153882, message_id=mes_id)
        except Exception as e:
            pass
