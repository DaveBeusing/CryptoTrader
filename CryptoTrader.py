#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) Dave Beusing <david.beusing@gmail.com>
#
#

import asyncio
from decimal import Decimal, ROUND_DOWN
import numpy as np
import pandas as pd
import datetime as dt

from binance import Client, BinanceSocketManager
from sqlalchemy import create_engine

from config import Config
from utils import Credentials, IPC, queryDB, build_Frame, log
from models import Asset, Order, Trade

credentials = Credentials( 'key/binance.key' )
client = Client( credentials.key, credentials.secret )
client.timestamp_offset = -2000 #binance.exceptions.BinanceAPIException: APIError(code=-1021): Timestamp for this request was 1000ms ahead of the server's time.
engine = create_engine( f'sqlite:///{Config.Database}' )

### Start Bot place order
if not IPC.get( IPC.isRunning ): 

    # pull all symbols from DB
    symbols = pd.read_sql( 'SELECT name FROM sqlite_master WHERE type = "table"', engine ).name.to_list()

    # calculate cumulative return for each symbol
    returns = []
    for symbol in symbols:
        prices = queryDB( engine, symbol, 2 ).Price #last 2 minutes
        cumulative_return = ( prices.pct_change() + 1 ).prod() - 1
        returns.append( { 'symbol' : symbol, 'cumret' : cumulative_return } )

    # sort descending
    sorted_returns = sorted(returns, key=lambda d: d['cumret'], reverse=True) 

    # prepare our Asset
    asset = Asset( client, sorted_returns[0]['symbol'], OHLCV=True, Indicators=True )

    # if the momentum already ends skip to next asset or wait a moment
    if asset.OHLCV.ROC.iloc[-1] < Config.minROC:
        print( f'{str(dt.datetime.now())} Opportunity not given, we skip this trade : {asset.symbol} (LvL0)' )
        # check next Symbol
        asset = Asset( client, sorted_returns[1]['symbol'], OHLCV=True, Indicators=True )
        if asset.OHLCV.ROC.iloc[-1] < Config.minROC:
            print( f'{str(dt.datetime.now())} Opportunity not given, we skip this trade : {asset.symbol} (LvL1)' )
            # check next Symbol
            asset = Asset( client, sorted_returns[2]['symbol'], OHLCV=True, Indicators=True )
            if asset.OHLCV.ROC.iloc[-1] < Config.minROC:
                print( f'{str(dt.datetime.now())} Opportunity not given, we skip this trade : {asset.symbol} (LvL2)' )
                print( f'{str(dt.datetime.now())} No opportunities we give up and wait a moment...' )
                quit()

    ### Momentum detected so place order
    # check again if an instance is already running
    if not IPC.get( IPC.isRunning ):
        IPC.set( IPC.isRunning )
        price = asset.getRecentPrice() # vielleicht sollten wir den letzten preis aus der DB nehmen? -> spart uns ein HTTP query + laufzeit 
        qty = asset.calculateQTY( Config.Investment, price=price )
        order = Order( client, asset, Order.BUY, qty, price )
        ##TODO: implement logging
    else:
        ### bot is already running
        print( f'{str(dt.datetime.now())} Found an opportunity, but we are already invested.' )
        quit() 

else:
    ### bot is already running
    print( f'{str(dt.datetime.now())} We are already invested.' )
    quit()    



#################################
### Monitor the current trade ###
#################################
async def main( asset, BuyOrder ):
    bsm = BinanceSocketManager( client )
    ts = bsm.trade_socket( asset.symbol )
    print( f'{str(dt.datetime.now())} Start trading {asset.symbol}' )
    async with ts as tscm:
        while True:
            response = await tscm.recv()
            if response:
                # build df from BSM response
                frame = build_Frame( response )
                CurrentPrice = frame.Price.iloc[-1] 

                TargetProfit = Decimal( BuyOrder.price ) + ( Decimal( BuyOrder.price ) * Decimal( Config.TargetProfit ) ) / 100
                StopLoss = Decimal( BuyOrder.price ) + ( Decimal( BuyOrder.price ) * Decimal( -Config.StopLoss ) ) / 100
                BreakEven = Decimal( BuyOrder.price ) + ( Decimal( BuyOrder.price ) * Decimal( Config.BreakEven ) ) / 100

                # Trailing TakeProfit
                if BuyOrder.TTP is not None:
                    TargetProfit = Decimal( BuyOrder.trail( 'get', 'TTP' ) )
                    StopLoss = Decimal( BuyOrder.trail( 'get', 'TSL' ) )

                if CurrentPrice > TargetProfit:                    
                    TargetProfit = Decimal( CurrentPrice ) + ( Decimal( CurrentPrice ) * Decimal( .1 ) ) / 100
             
                    StopLoss = Decimal( TargetProfit ) + ( Decimal( TargetProfit ) * Decimal( -.1 ) ) / 100

                    BuyOrder.trail( 'set', 'TTP', TargetProfit )
                    BuyOrder.trail( 'set', 'TSL', StopLoss )
                    print( f'{str(dt.datetime.now())} TTP set TP:{TargetProfit} SL:{StopLoss}' )

                #print( f'{str(dt.datetime.now())} {asset.symbol} BP:{BuyOrder.price:.4f} CP:{CurrentPrice} TP:{TargetProfit:.4f} SL:{StopLoss:.4f}' )

                # benchmark for TSL!
                if CurrentPrice < StopLoss or CurrentPrice > TargetProfit:
       
                    # This trade is closed, set Signal for a new one immediately
                    IPC.set( IPC.isRunning, remove=True )

                    # binance.exceptions.BinanceAPIException: APIError(code=-2010): Account has insufficient balance for requested action
                    # If we buy an asset we pay fee's with the bought asset, therefore we need to deduct the fee amount before we try to sell the position
                    # If we sell an asset the fee will be calculated (in our case) in USDT                     
                    
                    SellQTY = Decimal( BuyOrder.qty - BuyOrder.commission ) # floor???

                    # binance.exceptions.BinanceAPIException: APIError(code=-1013): Filter failure: LOT_SIZE
                    #order = client.create_order( symbol=symbol, side='SELL', type='MARKET', quantity=sell_qty )
                    SellOrder = Order( client, asset, Order.SELL, SellQTY, CurrentPrice )

                    Dust = Decimal( BuyOrder.qty - SellOrder.qty )
                    ProfitPerShare = Decimal( SellOrder.price - BuyOrder.price ).quantize(Decimal('.00000001'), rounding=ROUND_DOWN)
                    ProfitTotal = Decimal( ProfitPerShare * SellOrder.qty ).quantize(Decimal('.00000001'), rounding=ROUND_DOWN)
                    ProfitRelative = Decimal( ( SellOrder.price - BuyOrder.price ) / BuyOrder.price ).quantize(Decimal('.00000001'), rounding=ROUND_DOWN)

                    Diff = round(( SellOrder.price - BuyOrder.price ) / BuyOrder.price *100, 2 )

                    #p = P / G


                    Duration = str( dt.datetime.now() - dt.datetime.fromtimestamp( BuyOrder.timestamp ) )

                    # create Trade Object
                    #FinalTrade = Trade()

                    # TODO: implement logging
                    
                    state = None
                    if SellOrder.price > BuyOrder.price:
                        state = 'WON'
                    else:
                        state = 'LOST' 
                    
                    ds = { 'ts' : str(dt.datetime.now()), 'state' : state, 'symbol' : asset.symbol, 'duration' : str(Duration), 'ask' : str(BuyOrder.price), 'ask_qty' : str(BuyOrder.qty), 'bid' : str(SellOrder.price), 'bid_qty' : str(SellOrder.qty), 'profit' : str(ProfitPerShare), 'total_profit' : str(ProfitTotal), 'ROC' : asset.OHLCV.ROC.iloc[-1], 'RSI' : asset.OHLCV.RSI.iloc[-1], 'ATR' : asset.OHLCV.ATR.iloc[-1], 'OBV' : asset.OHLCV.OBV.iloc[-1] }
                    log( Config.Logfile, ds, timestamp=False )

                    print( f'###_Report_###' )
                    print( f'Symbol: {asset.symbol}' )
                    print( f'Condition: {state}' )
                    print( f'Investment: {Config.Investment} USDT' )
                    print( f'TP: {Config.TargetProfit}% SL: {Config.StopLoss}%')
                    print( f'Opened: {dt.datetime.fromtimestamp(BuyOrder.timestamp)}' )
                    print( f'Duration: {Duration}' ) 
                    print( f'Closed: {dt.datetime.fromtimestamp(SellOrder.timestamp)}' )
                    print( f'Ask: {BuyOrder.price} ({BuyOrder.qty})' )
                    print( f'Bid: {SellOrder.price} ({SellOrder.qty})' )
                    print( f'Dust: {Dust}' )
                    print( f'PPS: {ProfitPerShare}' )
                    print( f'Profit: {ProfitTotal}' )
                    print( f'Relative Profit: {ProfitRelative}' )
                    print( f'Diff: {Diff}' )
                    print( f'ROC: {asset.OHLCV.ROC.iloc[-1]}')
                    print( f'RSI: {asset.OHLCV.RSI.iloc[-1]}')
                    print( f'ATR: {asset.OHLCV.ATR.iloc[-1]}')
                    print( f'OBV: {asset.OHLCV.OBV.iloc[-1]}')
                    print( f'##############' )

                    #Stop & Exit the Loop
                    loop.stop()
                    # funktioniert ein break hier??
                    #RuntimeError: Event loop stopped before Future completed.

    await client.close_connection()                

                    
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    '''
    Traceback (most recent call last):
    File "/home/dave/code/crypto/bot/CryptoPro.py", line 173, in <module>
    loop.run_until_complete( main( asset, order ) )
    File "/usr/lib/python3.9/asyncio/base_events.py", line 640, in run_until_complete
    raise RuntimeError('Event loop stopped before Future completed.')
    RuntimeError: Event loop stopped before Future completed.
    '''
    try:
        loop.run_until_complete( main( asset, order ) )
    except RuntimeError as e:
        if e == 'Event loop stopped before Future completed.':
            pass    
