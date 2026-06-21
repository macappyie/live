from flask import Flask, render_template_string
from kiteconnect import KiteConnect
import pandas as pd
import datetime as dt
import pytz

# ---------- CONFIG ----------
API_KEY = "awh2j04pcd83zfvq"
kite = KiteConnect(api_key=API_KEY)

with open("access_token.txt") as f:
    kite.set_access_token(f.read().strip())

IST = pytz.timezone("Asia/Kolkata")


# ✅ NEW (time tracking)
entry_time_map = {}
target_time_map = {}

with open("watchlist.txt") as f:
    WATCHLIST = [f"NSE:{x.strip()}" for x in f if x.strip()]

INS = pd.read_csv("instruments.csv", low_memory=False)
INS["expiry"] = pd.to_datetime(INS["expiry"], errors="coerce")

# ============================================================
# SIGNAL LOGIC (same as tera)
# ============================================================

def get_930_signal(symbol, side):
    try:
        token = kite.ltp(symbol)[symbol]["instrument_token"]

        now = dt.datetime.now(IST)
        from_dt = IST.localize(dt.datetime.combine(now.date(), dt.time(9, 15)))
        to_dt   = IST.localize(dt.datetime.combine(now.date(), dt.time(9, 35)))

        df = pd.DataFrame(kite.historical_data(token, from_dt, to_dt, "5minute"))
        if df.empty:
            return None

        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)

        pre = df[(df.index.hour == 9) & (df.index.minute.isin([15,20,25]))]
        c930 = df[(df.index.hour == 9) & (df.index.minute == 30)]

        if pre.empty or c930.empty:
            return None

        if side == "GAINER":
            if c930["high"].iloc[0] < pre["high"].max():
                return round(c930["high"].iloc[0] + 1, 2)

        elif side == "LOSER":
            if c930["low"].iloc[0] > pre["low"].min():
                return round(c930["low"].iloc[0] - 1, 2)

        return None
    except:
        return None


def get_after_930_high(symbol):
    try:
        token = kite.ltp(symbol)[symbol]["instrument_token"]
        now = dt.datetime.now(IST)

        from_dt = IST.localize(dt.datetime.combine(now.date(), dt.time(9,15)))
        df = pd.DataFrame(kite.historical_data(token, from_dt, now, "5minute"))

        if df.empty:
            return None

        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)

        c = df[(df.index.hour == 9) & (df.index.minute == 30)]
        if c.empty:
            return None

        after = df[df.index > c.index[0]]
        return round(after["high"].max(), 2) if not after.empty else None

    except:
        return None


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
            return None, 0

        df = df.sort_values("expiry")
        df["diff"] = abs(df["strike"] - ref_price)

        atm = df.sort_values("diff").iloc[0]

        return f"NFO:{atm['tradingsymbol']}", int(atm["lot_size"])
    except:
        return None, 0

# ============================================================
# MAIN ENGINE
# ============================================================

def generate_rows():

    rows = []
    quotes = kite.quote(WATCHLIST)

    temp = []
    gainer = loser = sideways = 0

    for s in WATCHLIST:
        try:
            q = quotes[s]
            stock = s.replace("NSE:", "")

            ltp = q["last_price"]
            prev = q["ohlc"]["close"]
            open_price = q["ohlc"]["open"]

            change = ((ltp - prev) / prev) * 100
            gap_pct = ((open_price - prev) / prev) * 100

            side = "GAINER" if change > 0 else "LOSER" if change < 0 else "SIDE"

            if side == "GAINER": gainer += 1
            elif side == "LOSER": loser += 1
            else: sideways += 1

            temp.append({
                "stock": stock,
                "ltp": ltp,
                "change": change,
                "gap": gap_pct,
                "side": side
            })
        except:
            pass

    gainers = sorted(temp, key=lambda x: x["change"], reverse=True)[:20]
    losers = sorted(temp, key=lambda x: x["change"])[:20]
    final = gainers + losers

    sentiment = "BULLISH" if gainer > loser else "BEARISH" if loser > gainer else "SIDEWAYS"

    total = target_hit = sl_hit = active = 0

    for r in final:
        try:
            stock = r["stock"]
            side = r["side"]

            gap = round(r["gap"], 2)
            gap_text = f"Gap Up {gap}%" if gap > 0 else f"Gap Down {gap}%"

            stock_930 = get_930_signal(f"NSE:{stock}", side)

            if not stock_930:
                rows.append({
                    "time": dt.datetime.now(IST).strftime("%H:%M:%S"),
                    "entry_time": "-",
                    "target_time": "-",
                    "stock_name": stock,
                    "LTP": round(r["ltp"], 2),
                    "gainer_loser": side,
                    "option_name": "-",
                    "current_price": "-",
                    "buy_price": "-",
                    "qty": "-",
                    "investment": "-",
                    "sl_price": "-",
                    "max_loss": "-",
                    "target_price": "-",
                    "net_profit": "-",
                    "current_pnl": "-",
                    "max_profit": "-",
                    "todays_high": "-",
                    "result": f"{gap_text} | NO TRADE"
                })
                continue

            option, qty = get_option(stock, "CE" if side=="GAINER" else "PE", stock_930)

            current = kite.ltp(option)[option]["last_price"]
            buy = get_930_signal(option, side)
            high = get_after_930_high(option) or 0

            sl = round(buy*0.85,2)
            target = round(buy*1.3,2)

            key = option

            # ✅ Entry freeze
            if key not in entry_time_map:
                entry_time_map[key] = dt.datetime.now(IST).strftime("%H:%M:%S")

            # ✅ Target freeze
            if high >= target:
                if key not in target_time_map:
                    target_time_map[key] = dt.datetime.now(IST).strftime("%H:%M:%S")

                result = f"{gap_text} | TARGET HIT"
                target_hit += 1

            elif current <= sl:
                result = f"{gap_text} | SL HIT"
                sl_hit += 1

            else:
                result = f"{gap_text} | ACTIVE"
                active += 1

            rows.append({
                "time": dt.datetime.now(IST).strftime("%H:%M:%S"),
                "entry_time": entry_time_map.get(option, "-"),
                "target_time": target_time_map.get(option, "-"),
                "stock_name": stock,
                "LTP": round(r["ltp"], 2),
                "gainer_loser": side,
                "option_name": option.replace("NFO:", ""),
                "current_price": round(current, 2),
                "buy_price": buy,
                "qty": qty,
                "investment": round(buy*qty,2),
                "sl_price": sl,
                "max_loss": round(-(buy-sl)*qty,2),
                "target_price": target,
                "net_profit": round((target-buy)*qty,2),
                "current_pnl": round((current-buy)*qty,2),
                "max_profit": round((high-buy)*qty,2),
                "todays_high": high,
                "result": result
            })

        except:
            pass

    return rows, 0,0,0,0, gainer, loser, sideways, sentiment, 0, target_hit, sl_hit, active, 0,0,0,0


# ============================================================
# UI (ORIGINAL RESTORED)
# ============================================================

HTML = """
<html>
<head>
<meta http-equiv="refresh" content="3">
<style>
body{background:#000;color:#fff;font-family:Arial;}
.flash-green{background:#006400;}
.flash-red{background:#8b0000;}
.flash-blue{background:#003366;}

table{width:100%;border-collapse:collapse;}
td,th{border:1px solid #333;padding:5px;}
</style>
</head>

<body>

<table>
<tr>{% for c in cols %}<th>{{c}}</th>{% endfor %}</tr>

{% for r in rows %}
<tr class="
{% if 'TARGET HIT' in r.result %}flash-green
{% elif 'SL HIT' in r.result %}flash-red
{% elif 'ACTIVE' in r.result %}flash-blue
{% endif %}
">
{% for c in cols %}
<td>{{r[c]}}</td>
{% endfor %}
</tr>
{% endfor %}

</table>

</body>
</html>
"""

app = Flask(__name__)

@app.route("/")
def index():

    cols = [
        "time","entry_time","target_time",
        "stock_name","LTP","gainer_loser","option_name",
        "current_price","buy_price","qty","investment",
        "sl_price","max_loss","target_price",
        "net_profit","current_pnl","max_profit",
        "todays_high","result"
    ]

    data,*_ = generate_rows()

    return render_template_string(HTML, rows=data, cols=cols)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)
