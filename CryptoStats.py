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

clear = lambda: os.system('clear')

def reporting():
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
    #df = df.set_index('ts')

    # das ist nur die effektive laufzeit des trading, nicht die gesamtlaufzeit des bots!
    #runtime=str( dt.datetime.fromisoformat(df.ts.iloc[-1]) - dt.datetime.fromisoformat(df.ts[1]) )
    runtime=str( dt.datetime.now() - dt.datetime.fromisoformat(df.ts[1]) )
    rt = ( dt.datetime.fromisoformat(df.ts.iloc[-1]) - dt.datetime.fromisoformat(df.ts[1]) )

    rth = rt.seconds//3600
    if rth < 1:
        rth = 1


    invest=100
    SL= Config.StopLoss
    TP = Config.TargetProfit

    trades_total = df.state.count()
    trades_won = np.sum(df.state == 'WON')
    trades_won_rel = round(trades_won/trades_total*100,2)
    trades_won_profit = round( df[df.state == 'WON'].sum()['total_profit'], 4 )
    trades_lost = np.sum(df.state == 'LOST')
    trades_lost_rel = round(trades_lost/trades_total*100,2)
    trades_lost_profit = abs(round( df[df.state == 'LOST'].sum()['total_profit'], 4 ))
    turnover = round( trades_won_profit + trades_lost_profit, 4 )
    turnover_rel = round(turnover/invest*100,2)
    profit = round( trades_won_profit - trades_lost_profit, 4 )
    profit_rel = round(profit/invest*100,2)

    roi = round((profit - invest / invest), 2)

    #tpm = int(trades_total)/60
    tpm = trades_total/(rth*60)
    #tph = tpm*60
    tph = tpm*60
    avg_runtime = df.duration.mean()

    #p = P / G
    print( f'Report {logfile} created at {dt.datetime.now()}' )
    print( f'Bot runtime: {runtime}')
    print( f'Investment:{invest} USDT \nSL:{SL}% \nTP:{TP}%')
    print( f'Trades {trades_total}' )
    print( f'Won {trades_won} ({trades_won_rel}%) {trades_won_profit} USDT' )
    print( f'Lost {trades_lost} ({trades_lost_rel}%) {trades_lost_profit} USDT' )
    print( f'Turnover {turnover} USDT ({turnover_rel}%)')
    print( f'Profit {profit} USDT ({profit_rel}%)' )
    print( f'ROI {roi}%')
    print( f'TpH {tph} \nTpM {tpm}')
    print( f'AVG Duration {avg_runtime}')
    print( f'\nAsset Details\n' )
    trades = df.groupby('symbol')
    print( trades.sum() )


while True:
    reporting()
    time.sleep(3)
    clear()
