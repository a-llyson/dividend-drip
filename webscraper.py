from bs4 import BeautifulSoup
import requests
from env import MONGO_URI
import pymongo
import string

# connects to mongodb
client = pymongo.MongoClient(MONGO_URI)
db = client.stonks
col = db.stocks

# web parsing
URL = "https://maplemoney.com/canadian-dividend-stocks/"
r = requests.get(URL)
soup = BeautifulSoup(r.content, 'html5lib')


table = soup.findAll('tr')
for item in table:
    # adds new stock ticker and name to mongodb
    stockData = {
        "name": "",
        "ticker": "",
        "exdiv-date": '',
        "payment-date": '',
        "type": '',
        "dividend-per-share": '',
        "dividend-yield-percentage": '',
        "cost": '',
        "country": 'Canada'
    }

    # find name and ticker on site
    name = item.find('td', attrs={'class': 'column-1'})
    ticker = item.find('td', attrs={'class': 'column-2'})

    # if name and ticker exist then add to stock info
    if name and ticker:
        stockData["name"] = name.text
        ticker_name = ticker.text
        ticker_name = ticker_name.replace('.', '-')
        stockData["ticker"] = ticker_name

    # add to mongodb
    col.insert_one(stockData)
