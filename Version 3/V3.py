import sqlite3
import hashlib

from pandas_datareader import data
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime , timedelta

from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager , Screen , NoTransition
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ListProperty
from kivy.garden.matplotlib import FigureCanvasKivyAgg

from kivymd.app import MDApp
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.tab import MDTabsBase
from kivymd.uix.button import MDFlatButton
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.dialog import MDDialog

from kivy.core.window import Window
Window.maximize()

from kivy.config import Config
Config.set('kivy', 'exit_on_escape', '0')

global conn
conn = sqlite3.connect('stock_users.db')

yf.pdr_override()

def get_price(ticker):

    END_DATE = str(datetime.now().strftime('%Y-%m-%d')) # get current date
    WEEK_DATE = datetime.now() - timedelta(days=7) # date a week ago
    WEEK_DATE = WEEK_DATE.strftime('%Y-%m-%d')

    week_data = data.get_data_yahoo(ticker,start=WEEK_DATE,end=END_DATE)
    week_price = clean_data(week_data,'Adj Close',WEEK_DATE,END_DATE)

    number = float(week_price[-1])
    number = str(f"{number:.2f}")

    return float(number) # most recent price

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

def get_balance(UserID):

    c = conn.execute(f"SELECT Balance from USERS WHERE Username = '{UserID}'")
    for i in c:
        balance = float(i[0])
        balance = str(f"{balance:.2f}")
        return float(balance)

def hash_func(item):

    x = hashlib.md5(item.encode()).hexdigest() # returns the md5 hash
    return x

def clean_data(stock_data, col,START_DATE,END_DATE):

    weekdays = pd.date_range(start=START_DATE,end=END_DATE)
    clean_data = stock_data[col]
    return clean_data.fillna(method='ffill') # returns only the data about prices

class CompanyButtons(RecycleDataViewBehavior,BoxLayout): # buttons in the search list

    value = StringProperty()
    def __init__(self,**kwargs):
        super().__init__(**kwargs)

class PortfolioWidget(RecycleDataViewBehavior,BoxLayout):

    ticker_name = StringProperty()
    units = StringProperty()
    value = StringProperty()
    total_value = StringProperty()
    def __init__(self,**kwargs):
        super().__init__(**kwargs)

class Tab(MDFloatLayout, MDTabsBase):
    pass

class SuggestContent(BoxLayout):
    pass

class LoginScreen(Screen): # template for the login
    
    def login(self):
        valid_username = False
        username = sm.get_screen("loginScreen").ids.username.text
        password = sm.get_screen("loginScreen").ids.password.text # get values from text fields
        password_hash = hash_func(password)

        c = conn.execute("SELECT Username from USERS")
        for row in c:
            if username == row[0]:
                valid_username = True # check if username is in database
                sm.get_screen("loginScreen").ids.username.error = False

        if valid_username: # get password from database
            c = conn.execute(f"SELECT Password from USERS WHERE Username = '{username}'")
            for i in c:
                database_password = i[0]
            
            if password_hash == database_password:  # if password is correct
                c = conn.execute(f"SELECT Username from USERS WHERE Username = '{username}'")
                for i in c:
                    MyApp().set_user(i[0])

                sm.current = "mainScreen"

            else: # password is wrong
                sm.get_screen("loginScreen").ids.password.text = "" # remove the text from the input box
                sm.get_screen("loginScreen").ids.password.error = True # turn input box red
        
        else: # username is invalid
            sm.get_screen("loginScreen").ids.username.text = ""
            sm.get_screen("loginScreen").ids.username.error = True

    def signUp(self):
        sm.current = "signUpScreen"

class SignUpScreen(Screen): # template for the sign up

    def signUp(self):
        user_valid = False
        password_valid = False
        username = sm.get_screen("signUpScreen").ids.username.text
        password = sm.get_screen("signUpScreen").ids.password.text
        REpassword = sm.get_screen("signUpScreen").ids.REpassword.text # get values from text fields
        password_hash = hash_func(password)

        # check username is unique

        c = conn.execute(f"SELECT Username from USERS WHERE Username = '{username}'")

        if len(list(c)) == 0:
            user_valid = True

        else: # username is taken
            sm.get_screen("signUpScreen").ids.username.text = ""
            sm.get_screen("signUpScreen").ids.username.error = True
        
        # check both passwords are the same

        if user_valid:
            if password == REpassword:
                password_valid = True

            else: # passwords do not match
                sm.get_screen("signUpScreen").ids.REpassword.text = ""
                sm.get_screen("signUpScreen").ids.REpassword.error = True

        # store account in database

        if user_valid and password_valid:
            conn.execute("INSERT INTO USERS VALUES(?,?,?)", (username,password_hash,"10000"))
            conn.commit()
            sm.current = "loginScreen" # user has made an account and can now login
    

    def back_to_login(self):
        sm.current = "loginScreen"

class MainScreen(Screen): # template for the mainscreen
    pass

class MyApp(MDApp):
    
    rv_data = ListProperty() 
    profile_data = ListProperty()    # list of dictionarys {'value': 'text on button'}

    def build(self):    # creates the app

        Builder.load_file("V3ui.kv") # loads the design file
        global sm
        sm = ScreenManager(transition=NoTransition()) # remove the transition animation between screens
        sm.add_widget(LoginScreen(name="loginScreen"))
        sm.add_widget(MainScreen(name="mainScreen"))
        sm.add_widget(SignUpScreen(name="signUpScreen")) # add all the screens to the screen manager
        return sm

    def on_start(self):     # equivalent of __init__

        self.weekGraph = None
        self.monthGraph = None
        self.yearGraph = None
        self.current_ticker = None
        self.current_time = "month"
        self.add_item_list()
    
    def set_user(self,username):

        global UserID
        UserID = username

        sm.get_screen("mainScreen").ids.profileLabel.title = f"Balance: £{get_balance(UserID)}"
    
    def sign_out(self):

        sm.get_screen("loginScreen").ids.username.text = ""
        sm.get_screen("loginScreen").ids.password.text = ""
        sm.current = "loginScreen"

    def add_item_list(self, text="", search=False): # adds the stock names the the scrollable list
        
        self.rv_data = []   # reset the list of items so the search only displays the correct one

        def add_item(item): # item is tuple or list
            
            self.rv_data.append({'value': str(item)})
        
        c = conn.execute("SELECT * from STOCKS")
        ticker_list = list(c)

        for i in ticker_list:

            if search: # if user has enter text into search

                if text.lower() in i[0].lower(): # if the search text is in the item
                    add_item(i[0])

            else:
                add_item(i[0])
    
    def add_item_portfolio(self):
        
        self.profile_data = []

        c = conn.execute(f"SELECT StockID , Amount from userENTRY WHERE Username = '{UserID}'")
        
        for i in c:
            self.profile_data.append({'ticker_name': i[0],'units': str(i[1]),'value': "£" + str(get_price(i[0])),'total_value': "£" + str(int(i[1]) * get_price(i[0]))})
            self.profile_data.append({'ticker_name': "",'units': "",'value': "",'total_value': ""}) # the space between
    
    def buy_stock_confirm(self,obj):

        ticker_owned = False
        c = conn.execute(f"SELECT StockID from userENTRY WHERE Username = '{UserID}' AND StockID = '{self.current_ticker}'")
        if len(list(c)) != 0:
            ticker_owned = True

        if ticker_owned is False: # user does not own stock
            conn.execute("INSERT INTO userENTRY VALUES(?,?,?)", (UserID,str(self.current_ticker),str(amount))) # add to portfolio
            conn.commit()

            c = conn.execute(f"SELECT Balance from USERS WHERE Username = '{UserID}'")
            balance = list(c)[0][0]
            conn.execute(f"UPDATE USERS SET Balance = {balance - (get_price(self.current_ticker)*amount)} WHERE Username = '{UserID}'")
            conn.commit()
        
        else: # user owns stock
            c = conn.execute(f"SELECT Amount from userENTRY WHERE Username = '{UserID}' AND StockID = '{self.current_ticker}'")
            old_amount = list(c)[0][0]
            conn.execute(f"UPDATE userENTRY SET Amount = {old_amount + amount} WHERE Username = '{UserID}' AND StockID = '{self.current_ticker}'")
            conn.commit()

            c = conn.execute(f"SELECT Balance from USERS WHERE Username = '{UserID}'")
            balance = list(c)[0][0]
            conn.execute(f"UPDATE USERS SET Balance = {balance - (get_price(self.current_ticker)*amount)} WHERE Username = '{UserID}'")
            conn.commit()
        
        sm.get_screen("mainScreen").ids.amount_text.text = ""
        sm.get_screen("mainScreen").ids.profileLabel.title = f"Balance: £{get_balance(UserID)}"
        self.add_item_portfolio()
        self.buyConfirmDialog.dismiss()

    def buy_stock(self):

        if self.current_ticker == None:
            sm.get_screen("mainScreen").ids.amount_text.text = ""

        else:
            try:
                global amount
                amount = sm.get_screen("mainScreen").ids.amount_text.text
                amount = int(amount)

                if amount <= 0:
                    self.amount_error()

                elif amount * get_price(self.current_ticker) > get_balance(UserID):
                    self.amount_error()
                
                else:
                    # CONFIRMATION DIALOG #
                    self.buy_confirm()

            except:
                self.amount_error()

    def amount_error(self):

        sm.get_screen("mainScreen").ids.amount_text.text = ""
        
        self.AmountErrorDialog = MDDialog(
            text="Invalid Amount",
            buttons=[
                MDFlatButton(text="OK",on_release=self.close_amount_dialog)
            ]
        )
        self.AmountErrorDialog.open()

    def close_amount_dialog(self,obj):

        self.AmountErrorDialog.dismiss()
    
    def buy_confirm(self):

        self.buyConfirmDialog = MDDialog(
            text=f"Buy {amount} shares of {self.current_ticker} for {get_price(self.current_ticker)} a share, total is £{get_price(self.current_ticker)*amount}",
            buttons=[
                MDFlatButton(text="CANCEL",on_release=self.close_buy_confirm_dialog),
                MDRaisedButton(text="BUY",on_release=self.buy_stock_confirm)
            ]
        )
        self.buyConfirmDialog.open()
    
    def close_buy_confirm_dialog(self,obj):

        self.buyConfirmDialog.dismiss()
    
    def sell_stock_confirm(self,obj):

        c = conn.execute(f"SELECT Amount from userENTRY WHERE Username = '{UserID}' and StockID = '{self.current_ticker}'")
        old_amount = list(c)[0][0]

        new_amount = old_amount - amount # amount the user will have after selling

        if new_amount == 0: # all shares have been sold
            conn.execute(f"DELETE FROM userENTRY WHERE Username = '{UserID}' and StockID = '{self.current_ticker}'")
            conn.commit()

            c = conn.execute(f"SELECT Balance from USERS WHERE Username = '{UserID}'")
            balance = list(c)[0][0]
            conn.execute(f"UPDATE USERS SET Balance = {balance + (get_price(self.current_ticker)*amount)} WHERE Username = '{UserID}'")
            conn.commit()
        
        else:
            conn.execute(f"UPDATE userENTRY SET Amount = {new_amount} WHERE Username = '{UserID}' AND StockID = '{self.current_ticker}'")
            conn.commit()

            c = conn.execute(f"SELECT Balance from USERS WHERE Username = '{UserID}'")
            balance = list(c)[0][0]
            conn.execute(f"UPDATE USERS SET Balance = {balance + (get_price(self.current_ticker)*amount)} WHERE Username = '{UserID}'")
            conn.commit()
        
        sm.get_screen("mainScreen").ids.amount_text.text = ""
        sm.get_screen("mainScreen").ids.profileLabel.title = f"Balance: £{get_balance(UserID)}"
        self.add_item_portfolio()
        self.sellConfirmDialog.dismiss()
    
    def sell_stock(self):

        if self.current_ticker == None:
            sm.get_screen("mainScreen").ids.amount_text.text = ""

        else:
            try:
                global amount
                amount = sm.get_screen("mainScreen").ids.amount_text.text
                amount = int(amount)

                c = conn.execute(f"SELECT Amount from userENTRY WHERE Username = '{UserID}' and StockID = '{self.current_ticker}'")
                old_amount = list(c)[0][0]

                if old_amount < amount or amount <= 0: # if amount is to big or small
                    self.amount_error()
                
                else:
                    # CONFIRMATION DIALOG #
                    self.sell_confirm()

            except:
                self.amount_error()
    
    def sell_confirm(self):

        self.sellConfirmDialog = MDDialog(
            text=f"Sell {amount} shares of {self.current_ticker} for {get_price(self.current_ticker)} a share, total is £{get_price(self.current_ticker)*amount}",
            buttons=[
                MDFlatButton(text="CANCEL",on_release=self.close_sell_confirm_dialog),
                MDRaisedButton(text="SELL",on_release=self.sell_stock_confirm)
            ]
        )
        self.sellConfirmDialog.open()
    
    def close_sell_confirm_dialog(self,obj):

        self.sellConfirmDialog.dismiss()
    
    def update_graph(self,time):

        self.current_time = time
        sm.get_screen("mainScreen").ids.graphLayout.clear_widgets() # clear the current graph

        if time == "week":
            sm.get_screen("mainScreen").ids.graphLayout.add_widget(FigureCanvasKivyAgg(self.weekGraph))
        
        elif time == "month": # display the graph with the correct time period
            sm.get_screen("mainScreen").ids.graphLayout.add_widget(FigureCanvasKivyAgg(self.monthGraph))

        elif time == "year":
            sm.get_screen("mainScreen").ids.graphLayout.add_widget(FigureCanvasKivyAgg(self.yearGraph))
    
    def create_plot(self,stock_data,ticker):

        plt.subplots(figsize=(12,8))
        plt.plot(stock_data)
        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.title(ticker)
        plt.xticks(rotation=20)
        return plt.gcf()

    def ticker_error(self):
        
        self.Errordialog = MDDialog(
            text="Invalid ticker",
            buttons=[
                MDFlatButton(text="OK",on_release=self.close_error_dialog)
            ]
        )

        self.Errordialog.open()

    def close_error_dialog(self,obj):

        self.Errordialog.dismiss()

    def suggest_popup(self):

        self.suggestDialog = MDDialog(
            title= "Suggest A Ticker",
            type="custom",
            content_cls=SuggestContent(),
            buttons=[
                MDFlatButton(text="CANCEL",on_release=self.close_suggest_dialog),
                MDRaisedButton(text="SUGGEST",on_release=self.suggest_validation)
            ]
        )

        self.suggestDialog.open()
    
    def close_suggest_dialog(self,obj):
        self.suggestDialog.dismiss()

    def suggest_validation(self,obj):
        ticker = self.suggestDialog.content_cls.ids.suggestTicker.text
        ticker = ticker.upper()

        if ticker == "":
            pass
        
        elif test_ticker(ticker) is True: # ticker is valid

            c = conn.execute(f"SELECT * from STOCKS WHERE StockID = '{ticker}'")

            if len(list(c)) == 0:
                conn.execute("INSERT INTO STOCKS VALUES(?)", (ticker,))
                conn.commit()
                self.suggestDialog.dismiss()
                self.add_item_list()
            
            else:
                self.suggestDialog.content_cls.ids.suggestTicker.text = ""
        
        else:
            self.suggestDialog.content_cls.ids.suggestTicker.text = ""

    def create_graph(self,ticker):

        END_DATE = str(datetime.now().strftime('%Y-%m-%d'))

        WEEK_DATE = datetime.now() - timedelta(days=7)
        WEEK_DATE = WEEK_DATE.strftime('%Y-%m-%d')

        MONTH_DATE = datetime.now() - timedelta(days=31) # get the start dates for each time period
        MONTH_DATE = MONTH_DATE.strftime('%Y-%m-%d')

        YEAR_DATE = datetime.now() - timedelta(days=365)
        YEAR_DATE = YEAR_DATE.strftime('%Y-%m-%d')

        week_data = data.get_data_yahoo(ticker,start=WEEK_DATE,end=END_DATE)
        
        try:
            if week_data == "Download Failed":
                self.ticker_error()

        except ValueError:

            month_data = data.get_data_yahoo(ticker,start=MONTH_DATE,end=END_DATE) # get the data from yahoo
            year_data = data.get_data_yahoo(ticker,start=YEAR_DATE,end=END_DATE)

            week_price = clean_data(week_data,'Adj Close',WEEK_DATE,END_DATE)
            month_price = clean_data(month_data,'Adj Close',MONTH_DATE,END_DATE) # clean the data
            year_price = clean_data(year_data,'Adj Close',YEAR_DATE,END_DATE)

            self.weekGraph = self.create_plot(week_price,ticker)
            self.monthGraph = self.create_plot(month_price,ticker) # create the graphs from each time period
            self.yearGraph = self.create_plot(year_price,ticker)
            self.current_ticker = ticker

            sm.get_screen("mainScreen").ids.stock_info.text = f"Ticker: {ticker}\n\nCurrent Price: {get_price(ticker)}"

            self.update_graph(self.current_time) # display the new graph

MyApp().run()


# TO DO #

# RuntimeWarning: More than 20 figures have been opened
    # close graphs when new ones are created

# FEATURES

    # settings tab
        # dark mode
            # MDSwitch

    # user transaction logs

    # percentage change from purchase in porfolio, green/red for positive/negative

    # total portfolio value in toolbar



