#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) Dave Beusing <david.beusing@gmail.com>
#
#

from math import floor

from binance import Client
from decimal import Decimal, ROUND_DOWN

from utils import fetch_OHLCV, applyIndicators

import numpy as np
import pandas as pd
import datetime as dt


class Asset:

    def __init__( self, client, symbol, OHLCV=None, Indicators=None ):
        
        self.binance = client
        self.symbol = symbol
        self.OHLCV = None

        self.fetchMetadata()

        if OHLCV is not None:
            self.fetchOHLCV()

        if OHLCV and Indicators is not None:    
            self.applyOHLCVindicators()


    def fetchOHLCV(self):
        self.OHLCV = fetch_OHLCV( self.binance, self.symbol, interval='1m', start_date='60 minutes ago UTC' )


    def applyOHLCVindicators(self):
        applyIndicators( self.OHLCV )


    def calculateQTY( self, amount, price=None ):
        if not price:
            price = price
        else:
            price = self.getRecentPrice()
        return Decimal( floor( Decimal(amount) / ( Decimal( price ) * self.minQTY ) ) *  self.minQTY  )


    def getRecentPrice( self ):
        #TODO catch Exceptions
        return Decimal( self.binance.get_symbol_ticker( symbol=self.symbol )['price'] )


    def fetchMetadata( self ):
        #TODO catch Exceptions
        data = self.binance.get_symbol_info( self.symbol )
        self.base = data['baseAsset']
        self.precision = int( data['baseAssetPrecision'] )
        self.quote = data['quoteAsset']
        self.quotePrecision = int( data['quoteAssetPrecision'] )
        self.isSpot = data['isSpotTradingAllowed']
        self.isMargin = data['isMarginTradingAllowed']
        self.minQTY = Decimal( data['filters'][2]['minQty'] )
        self.maxQTY = Decimal( data['filters'][2]['maxQty'] )
        self.step = Decimal( data['filters'][2]['stepSize'] )
        '''
        {'symbol': 'LRCUSDT',
        'status': 'TRADING',
        'baseAsset': 'LRC',
        'baseAssetPrecision': 8,
        'quoteAsset': 'USDT',
        'quotePrecision': 8,
        'quoteAssetPrecision': 8,
        'baseCommissionPrecision': 8,
        'quoteCommissionPrecision': 8,
        'orderTypes': ['LIMIT',
         'LIMIT_MAKER',
         'MARKET',
         'STOP_LOSS_LIMIT',
         'TAKE_PROFIT_LIMIT'],
        'icebergAllowed': True,
        'ocoAllowed': True,
        'quoteOrderQtyMarketAllowed': True,
        'isSpotTradingAllowed': True,
        'isMarginTradingAllowed': True,
        'filters': [{'filterType': 'PRICE_FILTER',
          'minPrice': '0.00010000',
          'maxPrice': '1000.00000000',
          'tickSize': '0.00010000'},
         {'filterType': 'PERCENT_PRICE',
          'multiplierUp': '5',
          'multiplierDown': '0.2',
          'avgPriceMins': 5},
         {'filterType': 'LOT_SIZE',
          'minQty': '1.00000000',
          'maxQty': '9000000.00000000',
          'stepSize': '1.00000000'},
         {'filterType': 'MIN_NOTIONAL',
          'minNotional': '10.00000000',
          'applyToMarket': True,
          'avgPriceMins': 5},
         {'filterType': 'ICEBERG_PARTS', 'limit': 10},
         {'filterType': 'MARKET_LOT_SIZE',
          'minQty': '0.00000000',
          'maxQty': '448756.44475330',
          'stepSize': '0.00000000'},
         {'filterType': 'MAX_NUM_ORDERS', 'maxNumOrders': 200},
         {'filterType': 'MAX_NUM_ALGO_ORDERS', 'maxNumAlgoOrders': 5}],
        'permissions': ['SPOT', 'MARGIN']}
        '''


class Order:

    BUY = 'BUY'
    SELL = 'SELL'

    def __init__( self, client, asset, side, quantity, price ):
        self.binance = client
        self.asset = asset
        self.symbol = asset.symbol
        self.side = side
        self.qty = quantity
        self.bid = Decimal(price)
        #self.order = client.create_order( symbol=self.symbol, side=self.side, type='MARKET', quantity=self.qty )
        #self.order = {'symbol': 'LRCUSDT', 'orderId': 366051943, 'orderListId': -1, 'clientOrderId': 'W96WjbdkTqPgB0yGAd5jtS', 'transactTime': 1635869565122, 'price': '0.00000000', 'origQty': '61.00000000', 'executedQty': '61.00000000', 'cummulativeQuoteQty': '100.36770000', 'status': 'FILLED', 'timeInForce': 'GTC', 'type': 'MARKET', 'side': 'BUY', 'fills': [{'price': '1.64530000', 'qty': '39.00000000', 'commission': '0.03900000', 'commissionAsset': 'LRC', 'tradeId': 23543885}, {'price': '1.64550000', 'qty': '22.00000000', 'commission': '0.02200000', 'commissionAsset': 'LRC', 'tradeId': 23543886}]}
        '''
        {'symbol': 'LRCUSDT', 'orderId': 366051943, 'orderListId': -1, 'clientOrderId': 'W96WjbdkTqPgB0yGAd5jtS', 'transactTime': 1635869565122, 
        'price': '0.00000000', 'origQty': '61.00000000', 'executedQty': '61.00000000', 'cummulativeQuoteQty': '100.36770000', 'status': 'FILLED', 
        'timeInForce': 'GTC', 'type': 'MARKET', 'side': 'BUY', 'fills': [
            {'price': '1.64530000', 'qty': '39.00000000', 'commission': '0.03900000', 'commissionAsset': 'LRC', 'tradeId': 23543885}, 
            {'price': '1.64550000', 'qty': '22.00000000', 'commission': '0.02200000', 'commissionAsset': 'LRC', 'tradeId': 23543886}]}
        '''
        self.order = self.pseudoOrder( self.side, self.symbol, self.qty, self.bid, self.asset.precision )

        order_prices = []
        order_fees = []
        for val in self.order['fills']:
            order_prices.append( Decimal( val['price'] ) )
            order_fees.append( Decimal( val['commission']) )

        self.price = Decimal( max( order_prices) ).quantize(Decimal('.00000001'), rounding=ROUND_DOWN)
        self.qty = Decimal( self.order['executedQty'] )
        self.commission = Decimal( np.sum( order_fees ) )
        self.slippage = Decimal( self.price - self.bid )
        self.id = self.order['orderId']
        self.timestamp = dt.datetime.now().timestamp()

        self.TP = None
        self.TTP = None
        self.SL = None
        self.TSL = None


    def trail( self, mode, type, value=None ):
        ''' Basic get/set of Traling TakeProfit/StopLoss

        :param mode:str:    -> get|set
        :param type:str:    -> TTP|TSL
        :param value:float: -> value to sets
        '''        
        if type == 'TTP':
            if mode == 'set':
                self.TTP = value
            return self.TTP
        if type == 'TSL':
            if mode == 'set':
                self.TSL = value
            return self.TSL



    def pseudoOrder( self, side, symbol, qty, price, precision ):

        #'origQty': '12.30000000' '0.00020000' '0.01210000'
        origQTY = qty
        quoteQTY = Decimal( qty*price )
        halfedQTY = Decimal( origQTY/2 )
        batch1QTY = Decimal( halfedQTY + (halfedQTY/2) )
        batch1Fee = Decimal( round( ( batch1QTY / 100 ) * Decimal(0.1), precision ) )
        batch2QTY = Decimal( halfedQTY/2 )
        batch2Fee = Decimal( round( ( batch2QTY / 100 ) * Decimal(0.1), precision ) )

        order = {
            'symbol': symbol, 
            'orderId': 22107854, 
            'orderListId': -1, 
            'clientOrderId': 'DkGnomuTY9lz4kkALHQ87f', 
            'transactTime': 1637194823283, 
            'price': '0.00000000', 
            'origQty': origQTY, 
            'executedQty': origQTY, 
            'cummulativeQuoteQty': quoteQTY, 
            'status': 'FILLED', 
            'timeInForce': 'GTC', 
            'type': 'MARKET', 
            'side': side, 
            'fills': [
                {
                'price': price, 
                'qty': batch1QTY, 
                'commission': batch1Fee, 
                'commissionAsset': symbol, 
                'tradeId': 2498963
                }, 
                {
                'price': price, 
                'qty': batch2QTY, 
                'commission': batch2Fee, 
                'commissionAsset': symbol, 
                'tradeId': 2498964
                }
            ]
        }

        return order








class Trade:
    #https://www.investopedia.com/terms/b/bid-and-ask.asp
    def __init__( self, ask, bid ):

        self.ask = ask.price
        self.bid = bid.price