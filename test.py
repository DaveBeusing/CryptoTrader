#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) Dave Beusing <david.beusing@gmail.com>
#
#

import datetime as dt
from binance import Client
from utils import Credentials, applyIndicators, fetch_OHLCV

from models import Asset

credentials = Credentials( 'key/binance.key' )
client = Client( credentials.key, credentials.secret )
client.timestamp_offset = -2000 #binance.exceptions.BinanceAPIException: APIError(code=-1021): Timestamp for this request was 1000ms ahead of the server's time.

#asset = Asset( client, 'LRCUSDT' )


#start = str( int( dt.datetime.timestamp( dt.datetime.now() - dt.timedelta(minutes=60) ) ) )
#start = str( int( ( dt.datetime.now() - dt.timedelta(minutes=60) ).timestamp() ) )


#df = fetch_OHLCV( client, asset.symbol, interval='1m', start_date='60 minutes ago UTC' )

#applyIndicators( df )

#print( f'{df.ROC.iloc[-1]} {df.ROC.iloc[-1:]}' )
#print(df)




#https://stackoverflow.com/a/7224186
#https://stackoverflow.com/a/51950538
#https://docs.python.org/3/library/subprocess.html#module-subprocess
#import subprocess
#proc = subprocess.Popen(["rm","-r","some.file"])
#proc = subprocess.Popen( [ 'python', '/home/dave/code/crypto/bot/CryptoPro.py' ], close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )
#with open( '/home/dave/code/crypto/bot/log/stdout.log', 'a+' ) as logfile:
#    proc = subprocess.Popen( [ 'python', '/home/dave/code/crypto/bot/CryptoPro.py' ], close_fds=True, stdout=logfile, stderr=subprocess.STDOUT )
#print( proc.pid )
#proc.terminate()
# oder
#import os
#import signal
#os.kill(proc.pid, signal.SIGTERM) #or signal.SIGKILL 


start = '2021-11-24 18:53:21.726234'
end = '2021-11-24 21:53:45.679110'

#runtime = dt.datetime.fromisoformat( start )
