from bs4 import BeautifulSoup
import requests
from env import MONGO_URI
import pymongo
import datetime

# connect to mongodb
client = pymongo.MongoClient(MONGO_URI)
db = client.stonks
col = db.stocks

# find canadian stock info 
def find_canadian_stock_info():
    dividend_url = "https://ca.finance.yahoo.com/quote/"

    for document in col.find(): # switch to only filter canadian stocks 

        # for each ticker 
        ticker = document['ticker']
        new_dividend_url = dividend_url + ticker + ".TO" # remove .TO for american stocks 
        
        # grab stock info on site
        dividend_r =requests.get(new_dividend_url)
        dividend_soup = BeautifulSoup(dividend_r.content, 'html5lib')
        exdiv_date = dividend_soup.find('td', attrs={'data-test': "EX_DIVIDEND_DATE-value"})
        earnings_date = dividend_soup.find('td', attrs={'data-test': "EARNINGS_DATE-value"})
        current_price = dividend_soup.find('fin-streamer', attrs={'data-test': "qsp-price"})
        dividend_yield = dividend_soup.find('td', attrs={'data-test': "DIVIDEND_AND_YIELD-value"})


        if earnings_date and earnings_date.text != "N/A":
            # split the string and convert to integers
            earnings_year = int(earnings_date.text[-4:])
            earnings_day = int(earnings_date.text[-8:-6])
            earnings_month = datetime.datetime.strptime(earnings_date.text[-13:-10], "%b").month
            # add to mongodb
            col.update_one({"ticker": ticker}, { "$set": {"payment-date" : datetime.datetime(earnings_year, earnings_month, earnings_day)}})

        if dividend_yield and dividend_yield.text != "N/A (N/A)":
            # splits string into two parts
            split_info = dividend_yield.text.split('(')

            # gain per share
            fwd_dividend = float(split_info[0]) 

            # percent per share
            dividend_yield = float(split_info[1][:-2])
            dividend_yield = dividend_yield / 100
            
            # add to mongodb
            col.update_one({"ticker": ticker}, { "$set": {"dividend-per-share" : fwd_dividend, "dividend-yield-percentage": dividend_yield}})

        if exdiv_date and exdiv_date.text != "N/A":
            # split string into day, month, year and turn to ints
            year =  int(exdiv_date.text[-5:])
            day = int(exdiv_date.text[5:7])
            # converts month string to int (eg. Mar -> 3)
            month = datetime.datetime.strptime(exdiv_date.text[0:3], "%b").month
            # update mongo db
            col.update_one({"ticker": ticker}, { "$set": {"exdiv-date" : datetime.datetime(year, month, day), "cost": float(current_price.text)}}) 
        
        # for stocks that do not exist or have no exdiv date
        # else:
        #     print(ticker)

find_canadian_stock_info()