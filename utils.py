#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) Dave Beusing <david.beusing@gmail.com>
#
#

import os
import ta
import time

import pandas as pd
import datetime as dt

from binance import Client
from binance.exceptions import BinanceAPIException

from decimal import Decimal, ROUND_DOWN

class Credentials:
    """ Load key and secret from file.
    Expected file format is key and secret on separate lines.
    :param path: path to keyfile
    :type path: str
    :returns: None
    """
    def __init__(self, path):
        self.key = ''
        self.secret = ''
        self.path = os.path.dirname( os.path.abspath(__file__) ) + '/' + path

        with open(self.path, 'r') as fd:
            self.key = fd.readline().strip()
            self.secret = fd.readline().strip()


class IPC:

    isRunning = 'isRunning'
    isPaused = 'isPaused'

    def get( signal ):
        #TODO make it a global config
        path = getPath() + '/ipc/' + signal
        if os.path.isfile( path ):
            return True
        else:
            return False    

    def set( signal, remove=False ):
        #TODO make it a global config
        path = getPath() + '/ipc/' + signal
        with open( path, 'a+' ) as fd:
            fd.close()
        if remove:
            os.remove( path )    


class Tools:

    def round_crypto( amount ):
        return Decimal( amount ).quantize(Decimal('.00000001'), rounding=ROUND_DOWN)

    def round_fiat( amount ):
        return Decimal( amount ).quantize(Decimal('.01'), rounding=ROUND_DOWN)

#import os
import signal
import subprocess
class Processing:
    '''
    #https://stackoverflow.com/a/7224186
    #https://stackoverflow.com/a/51950538
    #https://docs.python.org/3/library/subprocess.html#module-subprocess
    '''
    def start( script, logfile=None ):
        if logfile is not None:
            with open( logfile, 'a+' ) as lf:
                proc = subprocess.Popen( [ '/usr/bin/python', script ], close_fds=True, stdout=lf, stderr=lf )
        else:
            proc = subprocess.Popen( [ '/usr/bin/python', script ], close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )
        return proc.pid

    def stop( pid:int ):
        os.kill( pid, signal.SIGTERM )




def getPath():
    ''' Returns the current script path
    '''
    return os.path.dirname( os.path.abspath( __file__ ) )




def log( file, data, timestamp=True ):
    ts = dt.datetime.now()
    with open( file, 'a+' ) as fd:
        if timestamp:
            fd.write( f'{ts} {data}\n' )
        else:
            fd.write( f'{data}\n' )    


def calculate_commission( quantity: float, fee: float ) -> float:
    ''' Calculate trading commission based on given quantity and fee %
    :param quantity (float): amount of CC you will trade
    :param fee (float): applicable fee in %
    :return (float): commission quantity of CC
    '''
    #return float( round( ( quantity / 100 ) * fee, self.asset_precision ) )
    # precision varies with CC
    return float( round( ( quantity / 100 ) * fee ) )


def fetch_NonLeveragedTradePairs( client, quoteAsset='USDT' ):
    ''' Return a List of Non Leveraged Trade Pairs

    :param client       -> binance.Client object
    :param quoteAsset   -> type:str: Symbol of quote Asset
    :return List
    '''
    data = client.get_exchange_info()
    symbols = [ x['symbol'] for x in data['symbols'] ]
    # leveraged tokens contain UP/DOWN BULL/BEAR in name
    # Was ist mit FIAT paaren -> EUR/USDT, AUD, BIDR, BRL, GBP, RUB, TRY, TUSD, USDC, DAI. IDTZ, UAH, NGN, VAI, USDP 'EUR', 'GBP', 'USD', 'AUD', 'JPY', 'RUB'
    exclude_pairs = [ 'UP', 'DOWN', 'BEAR', 'BULL' ] 
    non_pairs = [ symbol for symbol in symbols if all( excludes not in symbol for excludes in exclude_pairs ) ]
    pairs = [ symbol for symbol in non_pairs if symbol.endswith( quoteAsset ) ]
    return pairs


def fetch_OHLCV( client, symbol, interval='1d', start_date='1 day ago UTC', end_date=None ):    
    '''Fetch historical kline data (Candlesticks)
    
    https://binance-docs.github.io/apidocs/spot/en/#kline-candlestick-data
    
    :param client   -> binance.Client object
    :param symbol   -> type:str: Name of symbol pair e.g BTCUSDT
    :param interval -> type:str: Data interval e.g. 1m | 3m | 5m | 15m | 30m | 1h | 2h | 4h | 6h | 8h | 12h | 1d | 3d | 1W | 1M
    :param start    -> type:str|int: Start date string in UTC format or timestamp in milliseconds
    :param end      -> type:str|int: (optional) - end date string in UTC format or timestamp in milliseconds (default will fetch everything up to now)
    :return DataFrame['Date','Open','High','Low','Close','Volume'] | None
    '''
    if end_date is not None:
        try:
            data = client.get_historical_klines( symbol, interval, start_date, end_date ) 
        except BinanceAPIException as e:
            print(e)
            time.sleep(60)
            data = client.get_historical_klines( symbol, interval, start_date, end_date )    
    else:     
        try:
            data = client.get_historical_klines( symbol, interval, start_date ) 
        except BinanceAPIException as e:
            print(e)
            time.sleep(60)
            data = client.get_historical_klines( symbol, interval, start_date )   

    # convert result to DataFrame
    df = pd.DataFrame( data )
    # We fetched more data than we need, we just need the first six columns
    df = df.iloc[:,:6]
    # Now we will name our columns to the standard OHLCV
    df.columns = ['Date','Open','High','Low','Close','Volume']
    # Our index will be the UNIX timestamp, therefore we set datetime to index and make it more readable
    df = df.set_index('Date')        
    df.index = pd.to_datetime( df.index, unit='ms' )
    # We are handling mostly currencies so using float is necessary to calculate on the values later on
    df = df.astype(float)
    return df


def fetch_Portfolio( client ):
    '''Fetch Assets in Portolio

    https://binance-docs.github.io/apidocs/spot/en/#account-information-user_data

    :return Dict | None
    '''
    try:
        assets = client.get_account()['balances']
    except BinanceAPIException as e:
        print(e)
    portfolio = {}
    for asset in assets:
        if float( asset['free'] ) > 0.00000000:
            portfolio[asset['asset']] = float( asset['free'] )
    return portfolio


def fetch_Balance( client ):
    assets = client.get_account()['balances']
    for asset in assets:
        if asset['asset'] == 'USDT':
            return float( asset['free'] )


def applyIndicators( df ):
    ''' Apply Technical Indicators to given DataFrame

    We expect the following OHLCV columns within the given DataFrame
    ['Time','Open','High','Low','Close','Volume']

    Basic reading https://www.investopedia.com/terms/t/technical-analysis-of-stocks-and-trends.asp
    '''

    ## Momentum Indicators
    # https://www.investopedia.com/investing/momentum-and-relative-strength-index/
    ##

    '''
    Relative Strength Index (RSI)

    Compares the magnitude of recent gains and losses over a specified time period to measure speed and change of price movements of a security. 
    It is primarily used to attempt to identify overbought or oversold conditions in the trading of an asset.

    https://www.investopedia.com/terms/r/rsi.asp
    https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.momentum.rsi
    '''
    df[ 'RSI' ] = ta.momentum.rsi( df.Close, window=14, fillna=True )


    '''
    Moving Average Convergence Divergence (MACD)

    Is a trend-following momentum indicator that shows the relationship between two moving averages of prices.
    The MACD is calculated by subtracting the 26-period exponential moving average (EMA) from the 12-period EMA.

    https://www.investopedia.com/terms/m/macd.asp
    https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.MACD
    '''
    macd = ta.trend.MACD( df.Close, window_fast=12, window_slow=26, window_sign=9, fillna=True )
    df[ 'MACD' ] = macd.macd()
    df[ 'MACD_Diff' ] = macd.macd_diff()
    df[ 'MACD_Signal' ] = macd.macd_signal()


    '''
    Simple Moving Average (SMA)
    
    A simple moving average is an arithmetic moving average calculated by adding recent prices and then dividing that figure by the number of time periods in the calculation average. 
    For example, one could add the closing price of a security for a number of time periods and then divide this total by that same number of periods. 
    Short-term averages respond quickly to changes in the price of the underlying security, while long-term averages are slower to react.

    https://www.investopedia.com/terms/s/sma.asp
    https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.sma_indicator
    '''
    # SMAs according to Binance
    df[ 'SMA7' ] = ta.trend.sma_indicator( df.Close, window=7, fillna=True )
    df[ 'SMA25' ] = ta.trend.sma_indicator( df.Close, window=25, fillna=True )
    df[ 'SMA60' ] = ta.trend.sma_indicator( df.Close, window=60, fillna=True )
    # Commonly used SMAs
    df[ 'SMA12' ] = ta.trend.sma_indicator( df.Close, window=12, fillna=True )
    df[ 'SMA26' ] = ta.trend.sma_indicator( df.Close, window=26, fillna=True )
    df[ 'SMA50' ] = ta.trend.sma_indicator( df.Close, window=50, fillna=True )
    df[ 'SMA200' ] = ta.trend.sma_indicator( df.Close, window=200, fillna=True )


    '''
    Parabolic Stop and Reverse (Parabolic SAR)

    The parabolic SAR is a widely used technical indicator to determine market direction, but at the same moment to draw attention to it once the market direction is changing. 
    This indicator also can be called the "stop and reversal system," the parabolic SAR was developed by J. Welles Wilder Junior. - the creator of the relative strength index (RSI).
    
    https://www.investopedia.com/terms/p/parabolicindicator.asp
    https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.trend.PSARIndicator
    '''
    psar = ta.trend.PSARIndicator( high=df.High, low=df.Low, close=df.Close, step=0.02, max_step=2, fillna=True )
    df[ 'PSAR' ] = psar.psar()
    df[ 'PSAR_down' ] = psar.psar_down()
    df[ 'PSAR_down_ind' ] = psar.psar_down_indicator()
    df[ 'PSAR_up' ] = psar.psar_up()
    df[ 'PSAR_up_ind' ] = psar.psar_up_indicator()


    '''
    Bollinger Bands

    A Bollinger Band is a technical analysis tool outlined by a group of trend lines with calculated 2 standard deviations (positively and negatively) far from a straightforward moving average (SMA) of a market's value, 
    however which may be adjusted to user preferences. Bollinger Bands were developed and copyrighted by notable technical day trader John Bollinger and designed to get opportunities that could offer investors a better 
    likelihood of properly identifying market conditions (oversold or overbought). Bollinger Bands are a highly popular technique. Many traders believe the closer the prices move to the upper band, 
    the more overbought the market is, and the closer the prices move to the lower band, the more oversold the market is.

    https://www.investopedia.com/terms/b/bollingerbands.asp
    https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volatility.BollingerBands
    '''
    bb = ta.volatility.BollingerBands( close=df.Close, window=20, window_dev=2, fillna=True )
    df[ 'bb_avg' ] = bb.bollinger_mavg()
    df[ 'bb_high' ] = bb.bollinger_hband()
    df[ 'bb_low' ] = bb.bollinger_lband()


    '''
    Average True Range (ATR)
    
    The indicator provide an indication of the degree of price volatility. Strong moves, in either direction, are often accompanied by large ranges, or large True Ranges.

    The average true range (ATR) is a technical analysis indicator, introduced by market technician J. Welles Wilder Jr. in his book New Concepts in Technical Trading Systems, 
    that measures market volatility by decomposing the entire range of an asset price for that period.
    The true range indicator is taken as the greatest of the following: current high less the current low; the absolute value of the current high less the previous close; and the absolute value of the current low less the previous close. 
    The ATR is then a moving average, generally using 14 days, of the true ranges.

    https://www.investopedia.com/terms/a/atr.asp
    https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volatility.AverageTrueRange
    '''
    df[ 'ATR' ] = ta.volatility.AverageTrueRange( high=df.High, low=df.Low, close=df.Close, window=14, fillna=True ).average_true_range()


    '''
    On-balance volume (OBV)

    It relates price and volume in the stock market. OBV is based on a cumulative total volume.

    What is On-Balance Volume (OBV)?
    On-balance volume (OBV) is a technical trading momentum indicator that uses volume flow to predict changes in stock price. Joseph Granville first developed the OBV metric in the 1963 book Granville's New Key to Stock Market Profits.
    Granville believed that volume was the key force behind markets and designed OBV to project when major moves in the markets would occur based on volume changes. 
    In his book, he described the predictions generated by OBV as "a spring being wound tightly." 
    He believed that when volume increases sharply without a significant change in the stock's price, the price will eventually jump upward or fall downward.
    
    https://www.investopedia.com/terms/o/onbalancevolume.asp
    https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.volume.OnBalanceVolumeIndicator
    '''
    df[ 'OBV' ] = ta.volume.OnBalanceVolumeIndicator( close=df.Close, volume=df.Volume, fillna=True).on_balance_volume()


    '''
    Rate of Change (ROC)

    The Rate-of-Change (ROC) indicator, which is also referred to as simply Momentum, is a pure momentum oscillator that measures the percent change in price from one period to the next. 
    The ROC calculation compares the current price with the price “n” periods ago. 
    The plot forms an oscillator that fluctuates above and below the zero line as the Rate-of-Change moves from positive to negative. 
    As a momentum oscillator, ROC signals include centerline crossovers, divergences and overbought-oversold readings. 
    Divergences fail to foreshadow reversals more often than not, so this article will forgo a detailed discussion on them. 
    Even though centerline crossovers are prone to whipsaw, especially short-term, these crossovers can be used to identify the overall trend. 
    Identifying overbought or oversold extremes comes naturally to the Rate-of-Change oscillator.

    https://www.investopedia.com/terms/p/pricerateofchange.asp
    https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#ta.momentum.ROCIndicator
    '''
    df[ 'ROC' ] = ta.momentum.ROCIndicator( close=df.Close, window=3, fillna=True ).roc()



    '''
    return the augmented DataFrame
    '''
    return df


def build_Frame( msg, isMultiStream=None ):
    ''' Build a DataFrame from a Websocket response message

    :param msg              -> type:List: Websocket response
    :param isMultiStream    -> type:bool: True if message comes from a Websocket Multistream 
    :return DataFrame[ 'Time', 'Symbol', 'Price']
    '''
    if isMultiStream is not None:
        #https://binance-docs.github.io/apidocs/spot/en/#trade-streams
        '''
            {
                'stream': 'btcusdt@trade', 
                'data': {
                    'e': 'trade',                   // Event type
                    'E': 1637081506351,             // Event time
                    's': 'BTCUSDT',                 // Symbol
                    't': 1148079548,                // Trade ID
                    'p': '60646.40000000',          // Price
                    'q': '0.00031000',              // Quantity
                    'b': 8283146847,                // Buyer order ID
                    'a': 8283146313,                // Seller order ID
                    'T': 1637081506349,             // Trade time
                    'm': False,                     // Is the buyer the market maker?
                    'M': True                       // Ignore
                }
            }
        '''       
        df = pd.DataFrame( [ msg[ 'data' ] ] )
    else:       
        df = pd.DataFrame( [msg] )    

    df = df.loc[ :, [ 'E', 's', 'p' ] ] #E: event time | s: Symbol | p: Price ->https://binance-docs.github.io/apidocs/spot/en/#trade-streams
    df.columns = [ 'Time', 'Symbol', 'Price' ]
    df.Price = df.Price.astype( float )
    df.Time = pd.to_datetime( df.Time, unit='ms' )
    #pd.options.display.float_format = "{:,.8f}".format
    return df


def fetch_Lotsize( client, symbol ):
    info = client.get_symbol_info( symbol )
    return float( info['filters'][2]['minQty'] ) 


def fetch_AssetMetadata( client, symbol ):
    ''' Fetch Metadata needed for placing Orders
    '''
    info = client.get_symbol_info( symbol )    
    precision = info['baseAssetPrecision']
    lotsize = info['filters'][2]['minQty']

    return { 'lotsize' : float(lotsize), 'precision' : precision   }


def queryDB( engine, symbol, lookback:int ):
    ''' Query Crypto.db 

    :param engine -> SQLalchemy Engine Object
    :param symbol
    :param lookback
    '''
    lookback = lookback * 60 #minute to second conversion
    now = dt.datetime.now() - dt.timedelta( hours=1 ) #binance server are 1hour ahead
    before = now - dt.timedelta( seconds=lookback)
    #before = now - dt.timedelta( minutes=lookback )
    querystr = f"SELECT * FROM '{symbol}' WHERE TIME >= '{before}'"
    return pd.read_sql( querystr, engine )



# we need a function to create a pseudo order response for testing
def pseudoMarketOrder( side, symbol, qty, price, precision ):

    #'origQty': '12.30000000' '0.00020000' '0.01210000'
    origQTY = qty
    quoteQTY = Decimal( qty*price )
    halfedQTY = Decimal( origQTY/2 )
    batch1QTY = Decimal( halfedQTY + (halfedQTY/2) )
    batch1Fee = float( round( ( batch1QTY / 100 ) * 0.1, precision ) )
    batch2QTY = float( halfedQTY/2 )
    batch2Fee = float( round( ( batch2QTY / 100 ) * 0.1, precision ) )

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



def pseudoBalance( balance=None ):
    file = '/home/dave/code/crypto/binance/log/balance'
    if balance is not None:
        with open( file, 'r' ) as fd:
            bal = fd.readline().strip()

        if float(balance) > float(0):
            balance = float( float(bal) + float(balance) )
        else:
            balance = float( float(bal) - float(abs(balance)) )

        with open( file, 'w+' ) as fd:
            fd.write( str( balance ) )
    else:
        with open( file, 'r' ) as fd:
            balance = fd.readline().strip()

    return float( balance )


