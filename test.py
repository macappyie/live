from flask import Flask, render_template_string
from kiteconnect import KiteConnect
import datetime as dt
import pytz
import pandas as pd

# =====================================================
# CONFIG
# =====================================================

API_KEY = "awh2j04pcd83zfvq"

kite = KiteConnect(api_key=API_KEY)

with open("access_token.txt") as f:
    kite.set_access_token(f.read().strip())

with open("watchlist.txt") as f:
    WATCHLIST = [f"NSE:{x.strip()}" for x in f if x.strip()]


IST = pytz.timezone("Asia/Kolkata")

INS = pd.read_csv("instruments.csv", low_memory=False)
INS["expiry"] = pd.to_datetime(
    INS["expiry"],
    errors="coerce"
)

# =====================================================
# FLASK
# =====================================================

app = Flask(__name__)

# =====================================================
# DATA ENGINE
# =====================================================


def get_option(stock, opt_type, ref_price):

    try:

        today = dt.date.today()

        df = INS[
            (INS["name"] == stock) &
            (INS["segment"] == "NFO-OPT") &
            (INS["instrument_type"] == opt_type) &
            (INS["expiry"].dt.date >= today)
        ]

        if df.empty:
            return "-"

        df = df.sort_values("expiry")

        df["diff"] = abs(df["strike"] - ref_price)

        atm = df.sort_values("diff").iloc[0]

        return atm["tradingsymbol"]

    except:
        return "-"

def get_breakout_info(symbol, side):

    try:

        token = kite.ltp(symbol)[symbol]["instrument_token"]

        now = dt.datetime.now(IST)

        from_dt = IST.localize(
            dt.datetime.combine(now.date(), dt.time(9,15))
        )

        df = pd.DataFrame(
            kite.historical_data(
                token,
                from_dt,
                now,
                "5minute"
            )
        )

        if df.empty:
            return "-", "-"

        df["date"] = pd.to_datetime(df["date"])

        # 9:30 candle
        c930 = df[
            (df["date"].dt.hour == 9) &
            (df["date"].dt.minute == 30)
        ]

        if c930.empty:
            return "-", "-"

        if side == "GAINER":

            buy_price = round(
                c930.iloc[0]["high"],
                2
            )

            after = df[df["date"] > c930.iloc[0]["date"]]

            for _, row in after.iterrows():

                if row["close"] > buy_price:

                    return (
                        buy_price,
                        row["date"].strftime("%H:%M")
                    )

        else:

            buy_price = round(
                c930.iloc[0]["low"],
                2
            )

            after = df[df["date"] > c930.iloc[0]["date"]]

            for _, row in after.iterrows():

                if row["close"] < buy_price:

                    return (
                        buy_price,
                        row["date"].strftime("%H:%M")
                    )

        return "-", "-"

    except:
        return "-", "-"




def generate_rows():

    quotes = kite.quote(WATCHLIST)

    all_stocks = []

    gainers_count = 0
    losers_count = 0
    sideways_count = 0

    for symbol in WATCHLIST:

        try:

            q = quotes[symbol]

            stock = symbol.replace("NSE:", "")

            ltp = q["last_price"]
            prev_close = q["ohlc"]["close"]

            if prev_close <= 0:
                continue

            change = round(
                ((ltp - prev_close) / prev_close) * 100,
                2
            )

            if change > 0:
                side = "GAINER"
                gainers_count += 1

            elif change < 0:
                side = "LOSER"
                losers_count += 1

            else:
                side = "SIDEWAYS"
                sideways_count += 1



            buy_price, buy_time = get_breakout_info(
                symbol,
                side
            )

            if buy_price != "-":

                option_name = get_option(
                    stock,
                    "CE" if side == "GAINER" else "PE",
                    buy_price
                )

            else:

                option_name = "-"

        except Exception:
            continue

    top_gainers = sorted(
        [x for x in all_stocks if x["change_percent"] > 0],
        key=lambda x: x["change_percent"],
        reverse=True
    )[:100]

    top_losers = sorted(
        [x for x in all_stocks if x["change_percent"] < 0],
        key=lambda x: x["change_percent"]
    )[:100]

    rows = top_gainers + top_losers

    for i, row in enumerate(rows, start=1):
        row["rank"] = i

    sentiment = (
        "BULLISH"
        if gainers_count > losers_count
        else "BEARISH"
        if losers_count > gainers_count
        else "SIDEWAYS"
    )

    return rows, gainers_count, losers_count, sideways_count, sentiment



# =====================================================
# HTML
# =====================================================

HTML = """

<html>

<head>

<title>Top 100 Gainers & Losers</title>

<style>

body{
    background:black;
    color:white;
    font-family:Arial;
}

h1{
    text-align:center;
    color:#00ffff;
}

h2{
    text-align:center;
}

table{
    width:100%;
    border-collapse:collapse;
}

th{
    background:white;
    color:black;
    padding:8px;
}

td{
    border:1px solid #333;
    padding:6px;
    text-align:center;
}

.gainer{
    background:#0a5d0a;
}

.loser{
    background:#8b0000;
}

</style>

<meta http-equiv="refresh" content="10">

</head>

<body>

<h1>TOP 100 GAINERS & LOSERS</h1>

<h2>
GAINERS: {{g}}
 |
LOSERS: {{l}}
 |
SIDEWAYS: {{s}}
</h2>

<h2>
MARKET SENTIMENT :
{{sentiment}}
</h2>

<table>

<tr>
    <th>Rank</th>
    <th>Stock</th>
    <th>LTP</th>
    <th>Volume</th>
    <th>% Change</th>
    <th>Type</th>
    <th>Option Name</th>
    <th>Buy Time</th>
    <th>Buy Price</th>
</tr>

{% for r in rows %}

<tr class="{% if r.gainer_loser=='GAINER' %}gainer{% else %}loser{% endif %}">

    <td>{{r.rank}}</td>
    <td>{{r.stock_name}}</td>
    <td>{{r.LTP}}</td>
    <td>{{"{:,}".format(r.volume)}}</td>
    <td>{{r.change_percent}}%</td>
    <td>{{r.gainer_loser}}</td>
    <td>{{r.option_name}}</td>
    <td>{{r.buy_time}}</td>
    <td>{{r.buy_price}}</td>

</tr>

{% endfor %}

</table>

</body>
</html>
"""

# =====================================================
# ROUTE
# =====================================================


@app.route("/")
def index():

    rows, g, l, s, sentiment = generate_rows()

    return render_template_string(
        HTML,
        rows=rows,
        g=g,
        l=l,
        s=s,
        sentiment=sentiment
    )


# =====================================================
# START
# =====================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=6870,
        debug=False
    )
