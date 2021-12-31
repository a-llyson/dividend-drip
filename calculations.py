from env import MONGO_URI
import pymongo
import datetime
import time 
from collections import Counter

client = pymongo.MongoClient(MONGO_URI)
db = client.stonks
col = db.stocks

# step 1
# returns a list of tickers, a list of their prices, a list of their gain per share, and a list of payout dates
def find_prices(budget):
    eligible_stocks = col.find({
        "$and" : [{"exdiv-date": {"$gt": datetime.datetime.now()}},
        {"payment-date": {"$gt": datetime.datetime.now()}}]
        }) # for exdiv dates and payment dates in the future
    
    costs = []
    tickers = [] 
    dividends_per_share = []
    payout_dates = []

    # for each stock it adds the information to the appropriate list
    for stock in eligible_stocks:
        tickers.append(stock["ticker"])
        costs.append(float(stock["cost"]))
        if stock["dividend-per-share"]:
            dividends_per_share.append(stock["dividend-per-share"])
        elif stock["dividend-yield-percentage"]:
            dividends_per_share.append(stock["dividend-yield-percentage"] * stock["cost"])
        else:
            dividends_per_share.append(0)
        payout_dates.append(stock["payment-date"])

    return tickers, costs, dividends_per_share, payout_dates


# step 2 (faster)
# determines all combinations of stocks that are at or below budget
def find_combos2(stock_costs, stock_tickers, stock_payout, stock_cashout_date, budget, multiplier=1):
    
    def individual_calcs(remaining, combo, ticker_list, cashout_list, dividend_list, index):
        if remaining <= smallest_stock: # if the remainder is smaller than the smallest stock end, otherwise you can always add at least the smallest stock
            costs_results.append(combo)
            ticker_results.append(ticker_list)
            cashout_date_results.append(cashout_list)
            dividend_per_share_results.append(dividend_list)
            return
        for i in range(index, len(copy_stock_costs)):
            if copy_stock_costs[i] > remaining:
                break

            # recursion
            individual_calcs(remaining - copy_stock_costs[i], combo + [copy_stock_costs[i]], ticker_list + [tickers_list_sorted[i]], cashout_list + [cashout_dates_sorted[i]], dividend_list + [dividend_per_share_sorted[i]], i)

    # to sort the lists together 
    zipped_lists = zip(stock_tickers, stock_costs, stock_cashout_date, stock_payout)
    sorted_lists = sorted(zipped_lists, key = lambda x:x[1])
    tickers_list_sorted, cost_list_sorted, cashout_dates_sorted, dividend_per_share_sorted = map(list,zip(*sorted_lists)) # each individual sorted list

    copy_stock_costs = cost_list_sorted
    smallest_stock = copy_stock_costs[0] # constant

    #retvals
    costs_results = []
    ticker_results = []
    cashout_date_results = []
    dividend_per_share_results = []
    
    individual_calcs(budget*multiplier, [], [], [], [], 0) 

    return costs_results, ticker_results, cashout_date_results, dividend_per_share_results

# step 2 (slow)
# determines all combinations of stocks that are within 7% of the budget 
def find_combos(stock_costs, stock_tickers, stock_payout, stock_cashout_date, budget):
    combos_costs = []
    combos_tickers = []
    combos_payout = []
    combos_dates = []
    
    def individual_calcs(i, cur, tick, payout, date, total):
        if total >= (budget * 0.93) and total <= (budget * 1.07):
            combos_costs.append(cur.copy())
            combos_tickers.append(tick.copy())
            combos_dates.append(date.copy())
            combos_payout.append(round(payout, 2))
            return
        if i >= len(stock_costs) or total > (budget * 1.1):
            return
        
        date.append(stock_cashout_date[i])
        tick.append(stock_tickers[i])
        cur.append(stock_costs[i])
        individual_calcs(i, cur, tick, payout + stock_payout[i], date, total + stock_costs[i])
        cur.pop()
        tick.pop()
        date.pop()
        individual_calcs(i + 1,  cur, tick, payout, date, total)

    individual_calcs(0, [], [], 0, [], 0)
    return combos_costs, combos_tickers, combos_payout, combos_dates



# step 3
# returns a list of [price, payout date, ticker names, prices of each stock]
def calculate_returns(dlistof_costs, dlistof_tickers, listof_dividends, dlistof_paymentdates):
    temp_list_cashout_dates = []
    temp_list_payouts = [] 

    final_stock_combos = []
    # when dividends payout
    for list_dates in dlistof_paymentdates:
        list_dates.sort()
        # take the last index because that is the furthest date in the future
        if list_dates:
            temp_list_cashout_dates.append(list_dates[-1])
        else:
             temp_list_cashout_dates.append([])
    
    # money earned 
    for dividends in listof_dividends:
        # print(round(sum(dividends)%100)) # dollars
        # print(round(100*(sum(dividends) % 100) % 100)) # cents
        div_sum = sum(dividends)
        temp_list_payouts.append([sum(dividends), int(div_sum), int((div_sum * 100) % 100)])

    # adds each combination and relevant information
    for i in range(len(listof_dividends)):
        ticker_count = Counter(dlistof_tickers[i]) # counts number of occurence of each ticker
        keys = list(ticker_count.keys()) # splits dict into two lists so that it can be sorted
        values = list(ticker_count.values())
        ticker_count_list = zip(keys, values)
        cost_sum = sum(dlistof_costs[i])

        # appending the sum of money earned (dividends total), when it will be paid, dictionary of how many tickers, and sum of cost (eg. budget of $150 and cost is $147.89)
        final_stock_combos.append([temp_list_payouts[i], temp_list_cashout_dates[i].strftime('%m/%d/%Y'), list(ticker_count_list), [int(cost_sum), int((cost_sum * 100) % 100)]])
    
    # sorts in ascending then reverses to get largest return as first item
    final_stock_combos.sort()
    final_stock_combos.reverse()

    return final_stock_combos


# finds the best return when given a budget
def find_best_dividend(budget):
    # grab all relevant information
    ticker_list, cost_list, dividends_list, payout_list = find_prices(budget)

    if min(cost_list) > budget: # if it's empty which means no stocks under $budget then return nothing
        return []

    # create all possible combinations
    combo_numbers, combo_tickers, combo_payoutdates, combo_payouts = find_combos2(cost_list, ticker_list, dividends_list, payout_list, budget)

    # create list of combinations sorted from largest return to smallest
    sorted_returns = calculate_returns(combo_numbers, combo_tickers, combo_payouts, combo_payoutdates)
   
    # with open('test.txt', 'w') as f:
    #     f.write(str(sorted_returns))
    
    return sorted_returns

# find_best_dividend(200)



