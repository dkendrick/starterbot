# starterbot

A very basic starter bot based on CryptoKKing with a small balance, use at your own risk. I have since upgraded this script significantly and no longer use it. I take no responsibility for any losses. I am only sharing because of how much he helped me.

Even if you are not a coder I highly recommend you check out any script to make sure that the author is not going to try to withdraw your funds. Please at least skip over the script to ensure this.

## Download

All you really need from the source files is `main.py`, you could download that by itself.

## setup

You are going to need to setup python3(https://www.python.org/downloads/) to run the script.

### install python packages

```
pip3 install bybit
pip3 install pandas
```

### update the settings

At the top of the file there are settings to adjust.

```
num_orders = 3
order_size = 1
order_distance = 10
sl_risk = 0.03
tp_distance = 5
api_key = "YOUR_KEY"
api_secret = "YOUR_SECRET"
```

## Run the script

```
python3 main.py
```

I automated this script with cron to run every minute.
