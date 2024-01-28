#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) Dave Beusing <david.beusing@gmail.com>
#
#

import sys
import datetime as dt

from time import sleep
from config import Config
from utils import IPC, Processing

StreamPID = None

def main():

    global StreamPID

    # Clean-up before start
    if IPC.get( IPC.isRunning ):
        IPC.set( IPC.isRunning, remove=True )

    # we first need to start the Stream and wait a little  
    StreamPID = Processing.start( Config.CryptoStream )
    print( f'{str(dt.datetime.now())} CryptoStream started PID:{StreamPID}' )
    sleep(15)

    while True:

        if not IPC.get( IPC.isRunning ):
            Processing.start( Config.CryptoTrader, Config.STDOUT )
        
        sleep(5)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        ##
        # TODO: here must be some cleanup code e.g. shutdown Stream etc.
        ##
        print( f'\n\nBot will be stopped.. this may take 5 seconds...')
        Processing.stop( StreamPID )
        IPC.set( IPC.isRunning, remove=True )
        sleep(5)
        sys.exit(0)
