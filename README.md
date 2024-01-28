><b>This repo was checked into Git as part of my cleanup work.</b>

<br>
<br>

# CryptoTrader - a Python based full auto crypto trading bot 🔥
Uiiii we will get rich... sry nope 🧐 just a few lines of Python code to trade all sort of sh*tcoins on Binance.<br>
If you not have an Account, please consider to use this Referal-Link: https://accounts.binance.com/en/register?ref=GS2A2GHH it will result in a Fee-Discount for you :)
<br>
<b style="color:red">⚠️To say it loud and clear, in the current state the bot will lose your money!⚠️ <br>
You need to have a basic understanding of the topic and be hands-on to make this piece of code profitable</b>


### 🔹 Dependencies
> pip install pandas <br> pipi install numpy <br> pip install sqlalchemy <br> pip install binance <br> 

### 🔹 Usage
First run CryptoStream to acquire the necessary live datastream
> python CryptoStream.py

After a while we acquired enough data to start the trading bot.
> python CryptoBot.py

U can monitor the Bot using CryptoStats.py or by watching the logstream.
> python CryptoStats.py <br> or <br>
tail -f path/to/logfile.log

### 🔹 Screenshots
<b>Output of CryptoStats.py</b>
![CryptoStats](https://raw.githubusercontent.com/DaveBeusing/CryptoTrader/master/github/example_CryptoStats.png)
<br><br>
<b>Output of logstream created by CryptoTrader.py</b>
![Reporting](https://raw.githubusercontent.com/DaveBeusing/CryptoTrader/master/github/example_Reporting.png)

## ⚠️ DISCLAIMER ⚠️
The Content is for informational purposes only, you should not construe any such information or other material as legal, tax, investment, financial, or other advice.
<br><br>
<b>Please read and understand DISCLAIMER.md in addition to the aforementioned disclaimer.</b>