# Stock Screener (Stock Exchange Simulator)

Full-stack web app simulating a stock exchange: look up stock quotes, buy and sell with a virtual cash balance, and track transaction history and portfolio performance.

> Note: the app fetches market data from the IEX Cloud API, which appears to have been discontinued — live quotes may no longer work. Registration, trading with virtual cash, and portfolio tracking are unaffected.

## Features
- Stock search and quotes
- Buy/sell stocks with a virtual cash account (add funds anytime)
- Portfolio tracking and full transaction history
- User registration and login

## Tech Stack
- Python, Flask, Jinja
- SQLite
- HTML/CSS, JavaScript

## Setup

Prerequisites: Python 3.x

```bash
git clone https://github.com/anniecee/stock-screener.git
cd stock-screener
pip install -r requirements.txt
export FLASK_APP=application.py
flask run
```

Then open http://127.0.0.1:5000 in your browser. Create an account to start trading.

## Demo
![Demo of project](https://i.imgur.com/qIPwKsB.png)
