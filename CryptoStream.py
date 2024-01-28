#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) Dave Beusing <david.beusing@gmail.com>
#

import os
import asyncio
from utils import Credentials, fetch_NonLeveragedTradePairs, build_Frame
from binance import Client, AsyncClient, BinanceSocketManager
from sqlalchemy import create_engine, engine

from config import Config

credentials = Credentials( 'key/binance.key' )
client = Client( credentials.key, credentials.secret )

# Cleanup old data
if os.path.exists( Config.Database ):
    os.remove( Config.Database )

engine = create_engine( f'sqlite:///{Config.Database}' )

#prepare multistream list
tp = fetch_NonLeveragedTradePairs( client )
tp = [ i.lower() + '@trade' for i in tp ]

async def main():
    asyncClient = await AsyncClient.create()
    bsm = BinanceSocketManager( asyncClient )
    ms = bsm.multiplex_socket( tp )
    async with ms as tscm:
        while True:
            response = await tscm.recv()
            if response:
                frame = build_Frame( response, isMultiStream=True )
                frame.to_sql( frame.Symbol[0], engine, if_exists='append', index=False )

    await asyncClient.close_connection()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete( main() )

