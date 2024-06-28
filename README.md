# Stock screener (Stock exchange simulator)

## Table of Contents
1. [General Info](#general-info)
2. [Technologies](#technologies)
3. [Launch](#launch)

### General Info
***
This web app allows users to search for real-time stock data, buy and sell stocks as well as track historical transactions.
Users can also add more "cash" into their account. Using [IEX](https://iexcloud.io/)'s API. 
**:bulb: Upcoming change:** Set up database again, and adjust front-end, activate API for login, bug (invalid stock symbol)

### Demo
- Website: https://stock-screener-ac.herokuapp.com/register
- Users have to create an account and login
![Demo of project](https://i.imgur.com/qIPwKsB.png)

### Technologies
***
* [Python]: Version 12.3 
* [Flask]: Version 1.1.2
* [SQLite]
* **:wrench: Hosting:** Hosted by Heroku and kept awake by cron-job.org

### Launch
***
To run the web application use these commands:
```
$ export FLASK_APP=application.py
$ flask run
```
