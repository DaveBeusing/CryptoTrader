#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) Dave Beusing <david.beusing@gmail.com>
# Rename this file to config.py
#



class Config:
    # Amount of USDT which will be invested per trade
    Investment = 100
    TargetProfit = 0.8
    StopLoss = 1.0 # We need to have fee's in mind 0.1% each direction so 0.2 total for trade
    BreakEven = 0.2 # At least we need the fee's to be paid
    # Indicator settings
    minROC = 1
    Logfile = '/path/to/logfile.log'
    Database = '/path/to/database.sqlite3'
    CryptoTrader = '/path/to/CryptoTrader.py'
    CryptoStream = '/path/to/CryptoStream.py'
    STDOUT = 'path/to/name.stdout'