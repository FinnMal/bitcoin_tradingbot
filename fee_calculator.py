import sys
import sqlite3
import os
from datetime import datetime

conn = sqlite3.connect("btc_database.db")
c = conn.cursor()
c.execute('SELECT price FROM ticks')
ticks = c.fetchall()
conn.close()

balance = 500
profit = 0
for i in range(len(ticks)):
    if len(ticks)-1 > i:
        percentage = (ticks[i+1][0]-ticks[i][0])/ticks[i][0]
        if percentage > 0.0006:
            balance = balance + balance*percentage
            balance = balance - balance*0.0006
print(str(round(balance))+'€ in '+str(len(ticks))+' ticks')
