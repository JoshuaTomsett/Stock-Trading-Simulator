import sqlite3
import csv
import hashlib

conn = sqlite3.connect('stock_users.db')
print(type(conn))

def Read_file(directory):

    List_ = []
    with open(directory, 'rt') as text_file:
        reader = csv.reader(text_file)
        List_ = list(reader)
        
    return List_


# conn.execute('''CREATE TABLE USERS
#             (Username TEXT PRIMARY KEY NOT NULL,
#             Password TEXT NOT NULL,
#             Balance INT NOT NULL
#                         )''')

# conn.execute('''CREATE TABLE userENTRY
#             (Username INT NOT NULL,
#             StockID TEXT NOT NULL,
#             Amount int NOT NULL,
#             FOREIGN KEY (Username) REFERENCES USERS (Username)
#             FOREIGN KEY (StockID) REFERENCES STOCKS (StockID)
#             PRIMARY KEY (Username,StockID)
#                         )''')

# conn.execute('''CREATE TABLE STOCKS
#             (StockID TEXT PRIMARY KEY NOT NULL
#                         )''')

# stock_tickers = Read_file("Tickers.csv")

# for item in stock_tickers:
#     conn.execute("INSERT INTO STOCKS VALUES(?)", (item[0],))

# password = "password1"
# password_hash = hashlib.md5(password.encode()).hexdigest()
# conn.execute("INSERT INTO userENTRY VALUES(?,?,?)", ("1","AMZN","10"))

# conn.execute("UPDATE userENTRY SET Amount = 5 WHERE Username = 'Hawk' AND StockID = 'AMZN'")

# username = input("Enter username: ")
# c = conn.execute(f"SELECT Username from USERS WHERE Username = '{username}'")

# if len(list(c)) == 0:
#    print("unique")
# else:
#    print("taken")

# conn.execute("INSERT INTO USERS VALUES(?,?,?)", ("abc","abc","175.52"))

conn.commit()
# conn.close()

print("done")