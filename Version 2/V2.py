import sqlite3
import hashlib

from pandas_datareader import data
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime , timedelta

global conn
conn = sqlite3.connect('stock_users.db')

yf.pdr_override()

def hash_func(item):

    x = hashlib.md5(item.encode()).hexdigest() # returns the md5 hash
    return x

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

def create_graph(ticker,no_of_days):

    END_DATE = str(datetime.now().strftime('%Y-%m-%d')) # get current date
    WEEK_DATE = datetime.now() - timedelta(days=no_of_days) # date a week ago
    WEEK_DATE = WEEK_DATE.strftime('%Y-%m-%d')

    week_data = data.get_data_yahoo(ticker,start=WEEK_DATE,end=END_DATE)

    try:

        if week_data == "Download Failed":
            print("##### ERROR DISPLAYING GRAPH #####")

    except ValueError:

        week_price = clean_data(week_data,'Adj Close',WEEK_DATE,END_DATE)
        create_plot(week_price,ticker)

def test_ticker(ticker):

    END_DATE = str(datetime.now().strftime('%Y-%m-%d')) # get current date
    WEEK_DATE = datetime.now() - timedelta(days=7) # date a week ago
    WEEK_DATE = WEEK_DATE.strftime('%Y-%m-%d')

    week_data = data.get_data_yahoo(ticker,start=WEEK_DATE,end=END_DATE)

    try:
        if week_data == "Download Failed":
            return False

    except ValueError:
        return True

def get_price(ticker):

    END_DATE = str(datetime.now().strftime('%Y-%m-%d')) # get current date
    WEEK_DATE = datetime.now() - timedelta(days=7) # date a week ago
    WEEK_DATE = WEEK_DATE.strftime('%Y-%m-%d')

    week_data = data.get_data_yahoo(ticker,start=WEEK_DATE,end=END_DATE)
    week_price = clean_data(week_data,'Adj Close',WEEK_DATE,END_DATE)

    number = float(week_price[-1])
    number = str(f"{number:.2f}")

    return float(number) # most recent price

def get_balance():

    c = conn.execute(f"SELECT Balance from USERS WHERE Username = '{UserID}'")
    for i in c:
        return i[0]

def menu():

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
        print("\nBalance:", "£" + str(get_balance()), "\n")
        menu()

    elif option == 2: # view data (current price and graphs)
        valid = False
        while not valid:
            ticker = input("\nEnter ticker: ")
            if test_ticker(ticker):
                valid = True
        
        try:
            no_of_days = int(input("Number of days: "))
            if no_of_days > 0:
                print("Current price is:",get_price(ticker))
                create_graph(ticker,no_of_days)
        except:
            print("\nInvalid number of days")
        menu()

    elif option == 3: # portfolio
        print("\nStock Ticker    |    Amount\n")
        c = conn.execute(f"SELECT StockID , Amount from userENTRY WHERE Username = '{UserID}'")
        for i in c:
            print(i[0] , "    |    " , i[1])
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
        
        elif amount * get_price(ticker) > get_balance():
            print("\nYou do not have enough")
        
        else: # ticker and amount is valid
            confirm = input(f"Buy {amount} shares of {ticker} for {get_price(ticker)} a share, total is £{get_price(ticker)*amount} Y/N: ")

            if confirm.upper() == 'Y':
                ticker_owned = False
                c = conn.execute(f"SELECT StockID from userENTRY WHERE Username = '{UserID}' AND StockID = '{ticker}'")
                if len(list(c)) != 0:
                    ticker_owned = True

                if ticker_owned is False: # user does not own stock
                    conn.execute("INSERT INTO userENTRY VALUES(?,?,?)", (UserID,str(ticker),str(amount))) # add to portfolio
                    conn.commit()

                    c = conn.execute(f"SELECT Balance from USERS WHERE Username = '{UserID}'")
                    balance = list(c)[0][0]
                    conn.execute(f"UPDATE USERS SET Balance = {balance - (get_price(ticker)*amount)} WHERE Username = '{UserID}'")
                    conn.commit()
                
                else: # user owns stock
                    c = conn.execute(f"SELECT Amount from userENTRY WHERE Username = '{UserID}' AND StockID = '{ticker}'")
                    old_amount = list(c)[0][0]
                    conn.execute(f"UPDATE userENTRY SET Amount = {old_amount + amount} WHERE Username = '{UserID}' AND StockID = '{ticker}'")
                    conn.commit()

                    c = conn.execute(f"SELECT Balance from USERS WHERE Username = '{UserID}'")
                    balance = list(c)[0][0]
                    conn.execute(f"UPDATE USERS SET Balance = {balance - (get_price(ticker)*amount)} WHERE Username = '{UserID}'")
                    conn.commit()

            else: # confirmation failed
                pass
        menu()

    elif option == 5: # selling
        ticker = input("\nEnter ticker: ")
        
        c = conn.execute(f"SELECT Amount from userENTRY WHERE Username = '{UserID}' and StockID = '{ticker}'")

        try:
            old_amount = list(c)[0][0]

            try:
                amount = int(input("Enter amount: "))

            except ValueError: # if input is not integer
                amount = 0

            if old_amount < amount or amount <= 0: # if amount is to big or small
                print("\nInvalid amount")
            
            else: # amount is valid
                confirm = input(f"\nSell {amount} shares of {ticker} for {get_price(ticker)} a share, total is £{get_price(ticker)*amount} Y/N: ")

                if confirm.upper() == 'Y':
                    new_amount = old_amount - amount # amount the user will have after selling

                    if new_amount == 0: # all shares have been sold
                        conn.execute(f"DELETE FROM userENTRY WHERE Username = '{UserID}' and StockID = '{ticker}'")
                        conn.commit()

                        c = conn.execute(f"SELECT Balance from USERS WHERE Username = '{UserID}'")
                        balance = list(c)[0][0]
                        conn.execute(f"UPDATE USERS SET Balance = {balance + (get_price(ticker)*amount)} WHERE Username = '{UserID}'")
                        conn.commit()
                    
                    else:
                        conn.execute(f"UPDATE userENTRY SET Amount = {new_amount} WHERE Username = '{UserID}' AND StockID = '{ticker}'")
                        conn.commit()

                        c = conn.execute(f"SELECT Balance from USERS WHERE Username = '{UserID}'")
                        balance = list(c)[0][0]
                        conn.execute(f"UPDATE USERS SET Balance = {balance + (get_price(ticker)*amount)} WHERE Username = '{UserID}'")
                        conn.commit()

                else: # confirmation failed
                    pass

        except:
            print("\nInvalid Ticker")

        menu()

    elif option == 6:
        exit()

def login():

    print("""
    
    1 - Login
    2 - Sign up
    3 - Exit
    """)

    option = 0
    while option > 3 or option < 1:
        option = int(input("\nEnter option: "))
    
    if option == 1: # login
        valid_username = False
        username = input("\nEnter username: ")
        password = input("\nEnter password: ")
        password_hash = hash_func(password)

        c = conn.execute("SELECT Username from USERS")
        for row in c:
            if username == row[0]:
                valid_username = True # check if username is in database

        if valid_username: # get password from database
            c = conn.execute(f"SELECT Password from USERS WHERE Username = '{username}'")
            for i in c:
                database_password = i[0]
            
            if password_hash == database_password:  # if password is correct
                print("""
                ################
                Login Successful
                ################
                """)
                global UserID
                UserID = username
                menu()

            else: # password is wrong
                print("\n ## Invalid password ##")
        
        else: # username is invalid
            print("\n ## Invalid username ##")
    
    elif option == 2: # sign up
        username = input("\nEnter username: ")

        user_valid = False
        c = conn.execute(f"SELECT Username from USERS WHERE Username = '{username}'")
        if len(list(c)) == 0: # if username does not exist
            user_valid = True
        
        if user_valid: # username is valid (unique)
            password = input("\nEnter password: ")

            if password != "": # password is not null
                password_hash = hash_func(password)
                conn.execute("INSERT INTO USERS VALUES(?,?,?)", (username,password_hash,"10000"))
                conn.commit()
                print("""
                ###############
                Account created
                ###############
                """)
                login()

            else: # password is null
                print("\n ## Invalid password ##")
                login()

        else: # username is taken
            print("\n ## Username taken ##")
            login()
    
    elif option == 3:
        exit()

login()