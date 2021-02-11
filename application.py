import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from jinja2 import Template

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
# app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # Extract data from database
    # Transactions data: Group data by stocks, sum all shares of one stock together
    rows = db.execute("""SELECT symbol, name, SUM(shares)
                        FROM transactions
                        WHERE user_id=?
                        GROUP BY symbol
                        ORDER BY symbol""", session["user_id"])
    # Users data: Total cash user owns
    cash = (db.execute("SELECT cash FROM users WHERE id=?", session["user_id"]))[0]["cash"]

    # Create empty list to store extracted data for display
    symbol_display = []
    name_display = []
    shares_display = []
    price_display = [] #Store current price from API for display
    total_stock = [] #Store total value of each stock to calculate
    total_stock_display = [] #Store formatted total value for display

    # Format cash to display
    cash_display = usd(cash)

    for r in rows:
        if r['SUM(shares)'] != 0:
            symbol_display.append(r['symbol'])
            name_display.append(r['name'])
            shares_display.append(r['SUM(shares)'])

            # Update current price from API & save in list
            price = lookup(r['symbol'])['price']
            price_display.append(usd(price))

            # Calculate total value of each stock with the current price & save in list
            stock_cal = r['SUM(shares)']*price
            total_stock.append(stock_cal)
            total_stock_display.append(usd(stock_cal))

    # Calculate grand total value (cash + stocks) that user owns
    total = usd(cash + sum(total_stock))

    # Render template
    return render_template("index.html", total=total, rows=rows, symbol=symbol_display, name=name_display, shares=shares_display, price=price_display, cash=cash_display, total_stock=total_stock_display)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    # User reached route via POST (as by submitting stock's symbol)
    if request.method == "POST":

        # Ensure symbol was entered
        if not request.form.get("symbol"):
            return apology("must provide stock symbol", 412)

        # Ensure symbol is valid
        elif (lookup(request.form.get("symbol")) == None):
            return apology("invalid stock symbol", 412)

        # Ensure number of shares was entered
        elif not request.form.get("shares"):
            return apology("must provide number of shares", 412)

        # Ensure number of shares was valid:
        elif int(request.form.get("shares")) == 0:
            return apology("invalid number of share", 412)

        # If input are valid,
        else:
            # Save information about the stock
            shares = int(request.form.get("shares"))
            name = lookup(request.form.get("symbol"))["name"]
            symbol = lookup(request.form.get("symbol"))["symbol"]
            price = lookup(request.form.get("symbol"))["price"]

            # Extract "cash" data from "users" table in database and save in cash_list
            # Extract value of cash from cash_list and save it in cash
            cash_list = db.execute("SELECT cash FROM users WHERE id=:user_id", user_id=session["user_id"])
            cash = cash_list[0]["cash"]

            # Calculate cash after buying
            updated_cash = cash - (price*shares)

            # Ensure if user has enough cash to buy stock
            if updated_cash < 0:
                return apology("not enough cash", 412)

            else:
                # Update cash-after-buying into "users" table in database
                db.execute("UPDATE users SET cash=:cash WHERE id=:user_id",
                cash=updated_cash, user_id=session["user_id"])

                # Insert new transaction data into "transactions" table in database
                db.execute("INSERT INTO transactions (user_id, symbol, name, shares, price) VALUES (?, ?, ?, ?, ?)",
                session["user_id"], symbol, name, request.form.get("shares"), price)

                # Extract data to display
                # Group data by stocks, sum all shares of one stock together, take average of price per stock
                rows = db.execute("""SELECT symbol, name, SUM(shares)
                                    FROM transactions
                                    WHERE user_id=?
                                    GROUP BY symbol
                                    ORDER BY symbol""", session["user_id"])

                # Create list to save extracted data for display
                symbol_display = []
                name_display = []
                shares_display = []
                price_display = []

                # Create 2 lists to save total price of each stock for calculation & display
                total_stock = []
                total_stock_display = []

                # Save cash of user to display
                cash_display = usd(updated_cash)

                # Loop through "rows" and save extracted data into display lists
                for r in rows:
                    if r['SUM(shares)'] != 0:
                        symbol_display.append(r['symbol'])
                        name_display.append(r['name'])
                        shares_display.append(r['SUM(shares)'])
                        price_display.append(usd(lookup(r['symbol'])['price']))

                        stock_cal = (r['SUM(shares)']*(lookup(r['symbol']))['price'])
                        total_stock.append(stock_cal)
                        total_stock_display.append(usd(stock_cal))

                # Calculate grand total value (cash + stocks) that user owns
                total = usd(updated_cash + sum(total_stock))

                # Flash message
                flash("Bought!")

                # Render template
                return render_template("buy-success.html", total=total, rows=rows, symbol=symbol_display, name=name_display, shares=shares_display, price=price_display, cash=cash_display, total_stock=total_stock_display)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    # Extract data from database
    # Transactions data: Group data by stocks, sum all shares of one stock together
    rows = db.execute("""SELECT symbol, shares, price, time
                        FROM transactions
                        WHERE user_id=?
                        ORDER BY time""", session["user_id"])

    # Create empty list to store extracted data for display
    symbol_display = []
    shares_display = []
    price_display = []
    time_display = []

    for r in rows:
        symbol_display.append(r['symbol'])
        shares_display.append(r['shares'])
        price_display.append(usd(r['price']))
        time_display.append(r['time'])

    # Render template
    return render_template("history.html", rows=rows, symbol=symbol_display, shares=shares_display, price=price_display, time=time_display)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # User reached route via POST (as by submitting stock's symbol)
    if request.method == "POST":

        # Ensure symbol was entered
        if not request.form.get("symbol"):
            return apology("must provide stock symbol", 411)

        # Ensure symbol is valid
        elif (lookup(request.form.get("symbol")) == None):
            return apology("invalid stock symbol", 411)

        # If symbol is valid, redirect to display quoted
        else:
            name = lookup(request.form.get("symbol"))["name"]
            symbol = lookup(request.form.get("symbol"))["symbol"]
            price = lookup(request.form.get("symbol"))["price"]
            return render_template("quoted.html", name=name, symbol=symbol, price=price)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was entered
        if not request.form.get("username"):
            return apology("must provide username", 402)

        # Ensure password was entered
        elif not request.form.get("password"):
            return apology("must provide password", 402)

        # Ensure confirmation for password was submitted
        elif not request.form.get("confirmation"):
            return apology("must confirm password", 402)

        # Ensure confirmation for password was submitted
        elif request.form.get("confirmation") != request.form.get("password"):
            return apology("passwords do not match", 402)

        # Input new user information to database
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :password)",
                          username=request.form.get("username"),
                          password=generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8))

        # Save user information in row
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    # User reached route via POST (as by submitting stock's symbol)
    if request.method == "POST":

        # Extract data of owned stocks
        stock_data = db.execute ("SELECT symbol FROM transactions WHERE user_id = ? GROUP BY symbol", session["user_id"])
        owned_stocks = [i['symbol'] for i in stock_data]

        # Ensure symbol was entered
        if not request.form.get("symbol"):
            return apology("must provide stock symbol", 413)

        # Ensure symbol is valid
        elif request.form.get("symbol") not in owned_stocks:
            return apology("don't own this stock", 413)

        # Ensure number of shares was entered
        elif not request.form.get("shares"):
            return apology("must provide number of shares", 413)

        # Ensure number of shares was valid:
        elif int(request.form.get("shares")) == 0:
            return apology("invalid number of shares", 413)

        else:
            shares = int(request.form.get("shares"))
            symbol = request.form.get("symbol")

            # Extract data of owned shares
            shares_data = db.execute ("SELECT SUM(shares) FROM transactions WHERE user_id = ? AND symbol = ? GROUP BY symbol", session["user_id"], symbol)
            owned_shares = shares_data[0]['SUM(shares)']

            if shares > owned_shares:
                return apology("not enough shares", 413)

            # If inputs are valid, sell the stocks
            else:
                # Save information about the stock
                sell_shares = -(shares)
                price = lookup(symbol)["price"]
                name = lookup(symbol)["name"]

                # Insert new transaction data into "transactions" table in database
                db.execute("INSERT INTO transactions (user_id, symbol, name, shares, price) VALUES (?, ?, ?, ?, ?)",
                session["user_id"], symbol, name, sell_shares, price)

                # Extract "cash" data from "users" table in database and save in cash_list
                # Extract value of cash from cash_list and save it in cash
                cash_list = db.execute("SELECT cash FROM users WHERE id=:user_id", user_id=session["user_id"])
                cash = cash_list[0]["cash"]

                # Calculate cash after selling
                updated_cash = cash + (price*shares)

                # Update cash-after-selling into "users" table in database
                db.execute("UPDATE users SET cash=:cash WHERE id=:user_id",
                cash=updated_cash, user_id=session["user_id"])

                # Extract data to display
                # Group data by stocks, sum all shares of one stock together
                rows = db.execute("""SELECT symbol, name, SUM(shares)
                                    FROM transactions
                                    WHERE user_id=?
                                    GROUP BY symbol
                                    ORDER BY symbol""", session["user_id"])

                # Create list to save extracted data for display
                symbol_display = []
                name_display = []
                shares_display = []
                price_display = []

                # Create 2 lists to save total price of each stock for calculation & display
                total_stock = []
                total_stock_display = []

                # Save cash of user to display
                cash_display = usd(updated_cash)

                # Loop through "rows" and save extracted data into display lists
                for r in rows:
                    if r['SUM(shares)'] != 0:
                        symbol_display.append(r['symbol'])
                        name_display.append(r['name'])
                        shares_display.append(r['SUM(shares)'])
                        price_display.append(usd(lookup(r['symbol'])['price']))

                        stock_cal = (r['SUM(shares)']*(lookup(r['symbol']))['price'])
                        total_stock.append(stock_cal)
                        total_stock_display.append(usd(stock_cal))

                # Calculate grand total value (cash + stocks) that user owns
                total = usd(updated_cash + sum(total_stock))

                # Flash message
                flash("Sold!")

                # Render template
                return render_template("sell-success.html", total=total, rows=rows, symbol=symbol_display, name=name_display, shares=shares_display, price=price_display, cash=cash_display, total_stock=total_stock_display)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        symbol_data = db.execute ("SELECT symbol, SUM(shares) FROM transactions WHERE user_id = ? GROUP BY symbol", session["user_id"])
        symbol = [i['symbol'] for i in symbol_data if i['SUM(shares)'] != 0]
        return render_template("sell.html", symbol=symbol)

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """Add more cash into account"""
    # User reached route via POST (as by submitting amount of cash)
    if request.method == "POST":

        if not request.form.get("added_cash"):
            return apology("not enough shares", 414)

        added_cash = int(request.form.get("added_cash"))

        # Get amount of current cash user owns from database
        cash = db.execute("SELECT cash FROM users WHERE id=:user_id", user_id=session["user_id"])[0]['cash']

        # Calculate cash after adding
        updated_cash = cash + added_cash
        cash_display = usd(updated_cash)

        # Update cash-after-adding into "users" table in database
        db.execute("UPDATE users SET cash=:cash WHERE id=:user_id",
        cash=updated_cash, user_id=session["user_id"])

        flash("Successfully added cash!")
        return render_template("added.html", cash=cash_display)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        cash_data = db.execute ("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]['cash']
        cash_display = usd(cash_data)

        return render_template("add.html", cash=cash_display)

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
