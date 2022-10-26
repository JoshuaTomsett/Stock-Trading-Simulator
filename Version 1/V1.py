import csv

from pandas_datareader import data
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime , timedelta

yf.pdr_override()

def clean_data(stock_data, col,START_DATE,END_DATE):

    weekdays = pd.date_range(start=START_DATE,end=END_DATE)
    clean_data = stock_data[col].reindex(weekdays) # remove all weekends
    return clean_data.fillna(method='ffill') # only have adjusted close price

def create_plot(stock_data,ticker):

    plt.subplots(figsize=(12,8))
    plt.plot(stock_data)
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.title(ticker)
    plt.show()

def create_graph(ticker):

    END_DATE = str(datetime.now().strftime('%Y-%m-%d')) # get current date

    WEEK_DATE = datetime.now() - timedelta(days=7) # date a week ago
    WEEK_DATE = WEEK_DATE.strftime('%Y-%m-%d')

    week_data = data.get_data_yahoo(ticker,start=WEEK_DATE,end=END_DATE)

    try:

        if week_data == "Download Failed":
            print("##### ERROR #####")

    except ValueError:

        week_price = clean_data(week_data,'Adj Close',WEEK_DATE,END_DATE)
        create_plot(week_price,ticker)

def test_ticker(ticker):

    END_DATE = str(datetime.now().strftime('%Y-%m-%d'))
    WEEK_DATE = datetime.now() - timedelta(days=7) # get the date range
    WEEK_DATE = WEEK_DATE.strftime('%Y-%m-%d')

    # get data
    week_data = data.get_data_yahoo(ticker,start=WEEK_DATE,end=END_DATE)

    try:
        if week_data == "Download Failed":
            return False

    except ValueError:
        return True

def get_price(ticker):

    END_DATE = str(datetime.now().strftime('%Y-%m-%d'))
    WEEK_DATE = datetime.now() - timedelta(days=7) # get the date range
    WEEK_DATE = WEEK_DATE.strftime('%Y-%m-%d')

    week_data = data.get_data_yahoo(ticker,start=WEEK_DATE,end=END_DATE)
    week_price = clean_data(week_data,'Adj Close',WEEK_DATE,END_DATE)

    return int(week_price[-1]) # most recent price

def read_csv(directory):

    List_ = []
    with open(directory, 'rt') as text_file:
        reader = csv.reader(text_file)
        List_ = list(reader)
        
    return List_

def write_csv(List_ , directory):
    
    with open(directory, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        writer.writerows(List_)
        csv_file.close()

def menu():

    global balance
    global user_stocks

    print("""
    ########################

    1 - View balance
    2 - View stock data
    3 - View portfolio
    4 - Buy
    5 - Sell
    6 - Exit
    """)

    option = 0
    while option > 6 or option < 1:
        option = int(input("\nEnter option: "))
    
    if option == 1: # view balance

        print("\nBalance:", "£" + str(balance), "\n")
        menu()

    elif option == 2: # view data (current price and graph of weeks data)

        valid = False
        while not valid:
            ticker = input("Enter ticker: ")
            if test_ticker(ticker):
                valid = True
            
        print("Current price is:",get_price(ticker))
        create_graph(ticker)
        menu()

    elif option == 3: # portfolio

        print("\nStock Ticker    |    Amount\n")
        for i in user_stocks:
            print(i[0],"   |   ",i[1])

        menu()

    elif option == 4: # buying

        valid = False
        while not valid:
            ticker = input("\nEnter ticker: ")
            if test_ticker(ticker):
                valid = True
        
        try:
            amount = int(input("Enter amount: "))

        except ValueError: # if input is not integer
            amount = 0
        
        if amount <= 0:
            print("\nInvalid amount")
        
        elif amount * get_price(ticker) > balance:
            print("\nYou do not have enough")
        
        else: # ticker and amount is valid
            confirm = input(f"Buy {amount} shares of {ticker} for {get_price(ticker)} a share, total is £{get_price(ticker)*amount} Y/N: ")

            if confirm.upper() == 'Y':
                ticker_index = False
                for index , i in enumerate(user_stocks): # check if user owns the stock
                    if i[0] == ticker:
                        ticker_index = index
                        break

                if ticker_index is False: # user does not own stock
                    user_stocks.append([ticker,amount]) # update portfolio
                    balance = balance - get_price(ticker) * amount
                
                else: # user owns stock
                    user_stocks[ticker_index][1] = int(user_stocks[ticker_index][1]) + amount # update portfolio
                    balance = balance - get_price(ticker) * amount

            else: # confirmation failed
                pass

            user_stocks.insert(0,[balance,''])
            write_csv(user_stocks, 'Data.csv') # update csv file
            del user_stocks[0]

        menu()

    elif option == 5: # selling

        ticker = input("\nEnter ticker: ")
        ticker_index = False

        for index , i in enumerate(user_stocks): # check if user owns the share they want to sell
            if i[0] == ticker:
                ticker_index = index
                break
        
        if ticker_index is False:
            print("\nInvalid ticker")

        elif ticker_index is not False: # ticker is valid
            try:
                amount = int(input("Enter amount: "))

            except ValueError: # if input is not integer
                amount = 0

            if int(user_stocks[ticker_index][1]) < amount or amount <= 0: # if amount is to big or small
                print("\nInvalid amount")
            
            else: # amount is valid
                confirm = input(f"\nSell {amount} shares of {ticker} for {get_price(ticker)} a share, total is £{get_price(ticker)*amount} Y/N: ")

                if confirm.upper() == 'Y':
                    
                    new_amount = int(user_stocks[ticker_index][1]) - amount # amount the user will have after selling

                    if new_amount == 0: # all shares have been sold
                        del user_stocks[ticker_index] # update portfolio
                        balance = int(balance + (amount * get_price(ticker)))
                    
                    else:
                        user_stocks[ticker_index][1] = new_amount # update portfolio
                        balance = int(balance + (amount * get_price(ticker)))

                else: # confirmation failed
                    pass
            
                user_stocks.insert(0,[balance,''])
                write_csv(user_stocks, 'Data.csv') # update csv file
                del user_stocks[0]
        menu()
    
    elif option == 6:
        exit()
        
global balance
global user_stocks

user_data = read_csv("Data.csv")
balance = int(user_data[0][0])

del user_data[0]
user_stocks = user_data

menu()
