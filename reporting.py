#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) Dave Beusing <david.beusing@gmail.com>
#
#

import os
import time
import ast
import numpy as np
import pandas as pd
import datetime as dt


from config import Config

#logfile = Config.Logfile
logfile = '/home/dave/code/crypto/bot/log/ms_test9-2.log'


data = []
with open( logfile ) as fd:
    lines = fd.readlines()
for line in lines:
    data.append( ast.literal_eval( line.rstrip() ) )
fd.close()
df = pd.DataFrame( data )
df.ask = df.ask.astype(float)
df.ask_qty = df.ask_qty.astype(float)
df.bid = df.bid.astype(float)
df.bid_qty = df.bid_qty.astype(float)
df.profit = df.profit.astype(float)
df.total_profit = df.total_profit.astype(float)
df.duration = pd.to_timedelta(df.duration)

# set index to timestamp
df = df.set_index('ts')

# change state to boolean indicator
#df.state = (df.state == 'WON').astype(int)

# change state to +1/-1 values
df.loc[df.state == 'WON', 'state'] = 1
df.loc[df.state == 'LOST', 'state'] = -1



import matplotlib.pyplot as plt
#plt.style.use('seaborn-whitegrid')
#plt.figure( figsize=(20,10) )
#plt.title( 'CryptoPro Bot Test' )
#plt.xlabel( 'Time' )
#plt.ylabel( 'State/ATR/ROC' )
#plt.plot(df.index, df.state, label='State')
#plt.plot(df.index, df.ATR, label='ATR')
#plt.plot(df.index, df.ROC, label='ROC')
#plt.plot(df.index, df.RSI, label='RSI')
#plt.plot(df.index, df.OBV, label='OBV')
#plt.legend()
#plt.show()



plt.figure( figsize=(20,10) )

fig, [ax1, ax2, ax3, ax4] = plt.subplots( 4, 1, sharex=True )

ax1.set_title('Trade Status', loc='left', y=0.85, x=0.02, fontsize='medium')
ax1.plot(df.state, label='State')
ax1.grid(True)
ax1.text(0.5, 0.5, 'BSNG Quantitative Private Equity', transform=ax1.transAxes, fontsize=10, color='black', alpha=0.5, ha='center', va='center', rotation='30')

ax2.set_title('OBV', loc='left', y=0.85, x=0.02, fontsize='medium')
ax2.plot(df.OBV, label='OBV')
ax2.grid(True)

ax3.set_title('ROC', loc='left', y=0.85, x=0.02, fontsize='medium')
ax3.plot(df.ROC, label='ROC')
ax3.grid(True)

ax4.set_title('ATR', loc='left', y=0.85, x=0.02, fontsize='medium')
ax4.plot(df.ATR, label='ATR')
ax4.grid(True)

plt.show()

