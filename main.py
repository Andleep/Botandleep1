# main.py - Smart TradeBot (no pandas)
# - Flask app with backtester and UI
# - Pure-Python indicators (EMA, RSI, ATR) to avoid building pandas on Render
# - Compounding equity after each trade, position sizing via risk-per-trade and SL%
import os, time, math, csv
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_file
import requests

# CONFIG (override with env variables on Render)
SYMBOLS = os.getenv("SYMBOLS", "ETHUSDT,BTCUSDT,BNBUSDT,SOLUSDT,ADAUSDT").split(",")
INITIAL_BALANCE = float(os.getenv("INITIAL_BALANCE", "10.0"))
EMA_FAST = int(os.getenv("EMA_FAST", "8"))
EMA_SLOW = int(os.getenv("EMA_SLOW", "21"))
RSI_PERIOD = int(os.getenv("RSI_PERIOD", "14"))
VOLUME_MULTIPLIER = float(os.getenv("VOLUME_MULTIPLIER", "1.0"))
STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", "0.01"))  # 1%
RISK_PER_TRADE = float(os.getenv("RISK_PER_TRADE", "0.02"))  # 2%
KL_LIMIT = int(os.getenv("KL_LIMIT", "1000"))
BINANCE_KLINES = os.getenv("BINANCE_KLINES", "https://api.binance.com/api/v3/klines")

DEBUG_LOG = "bot_debug.log"
TRADE_LOG = "trades.csv"

app = Flask(__name__, template_folder="templates", static_folder="static")

# ---------------- utilities ----------------
def debug(msg):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(DEBUG_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass
    print(f"[{ts}] {msg}")

def fetch_klines_page(symbol, interval="1m", limit=1000, start_time=None):
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    if start_time is not None:
        params["startTime"] = int(start_time)
    headers = {"User-Agent":"TradeBot-Smart/1.0"}
    r = requests.get(BINANCE_KLINES, params=params, headers=headers, timeout=20)
    if r.status_code != 200:
        # propagate error (451 etc.)
        raise Exception(f"Binance API error {r.status_code}: {r.text[:200]}")
    data = r.json()
    out = []
    for k in data:
        out.append({"time": int(k[0]), "open": float(k[1]), "high": float(k[2]), "low": float(k[3]), "close": float(k[4]), "volume": float(k[5])})
    return out

def fetch_klines(symbol, interval="1m", limit=500, start_time=None):
    # convenience wrapper, fetch up to `limit` candles (<=1000)
    if limit <= 1000:
        return fetch_klines_page(symbol, interval=interval, limit=limit, start_time=start_time)
    # otherwise paginate
    all_candles = []
    remaining = limit
    st = start_time
    while remaining > 0:
        page = fetch_klines_page(symbol, interval=interval, limit=min(1000, remaining), start_time=st)
        if not page:
            break
        all_candles.extend(page)
        remaining -= len(page)
        st = page[-1]["time"] + 1
        time.sleep(0.12)
    return all_candles

# -------------- indicators (pure python) --------------
def ema_list(values, span):
    if not values:
        return []
    alpha = 2.0 / (span + 1)
    out = [values[0]]
    for v in values[1:]:
        out.append((v - out[-1]) * alpha + out[-1])
    return out

def sma_list(values, period):
    out = []
    s = 0.0
    for i, v in enumerate(values):
        s += v
        if i >= period:
            s -= values[i-period]
            out.append(s/period)
        elif i == period-1:
            out.append(s/period)
    return out

def rsi_list(values, period=14):
    n = len(values)
    if n < period+1:
        return [50.0]*n
    deltas = [values[i]-values[i-1] for i in range(1,n)]
    ups = [d if d>0 else 0 for d in deltas]
    downs = [-d if d<0 else 0 for d in deltas]
    up_avg = sum(ups[:period]) / period
    down_avg = sum(downs[:period]) / period if sum(downs[:period])!=0 else 1e-9
    out = [50.0]*(period+1)
    for u,d in zip(ups[period:], downs[period:]):
        up_avg = (up_avg*(period-1) + u) / period
        down_avg = (down_avg*(period-1) + d) / period
        rs = up_avg / (down_avg + 1e-12)
        out.append(100 - (100/(1+rs)))
    # align to same length as values by prepending
    if len(out) < n:
        out = [out[0]]*(n - len(out)) + out
    return out

def atr_list(highs, lows, closes, period=14):
    n = len(closes)
    if n < 2:
        return [0.0]*n
    trs = []
    for i in range(1, n):
        tr = max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1]))
        trs.append(tr)
    if len(trs) < period:
        avg = sum(trs)/len(trs) if trs else 0.0
        return [avg]*n
    sma_tr = sma_list(trs, period)
    # sma_tr length = len(trs)-period+1
    prefix = [sma_tr[0]]*(period)
    return prefix + sma_tr

# -------------- backtest engine --------------
def append_trades_csv(trades_list):
    header = ["time","entry","exit","profit","balance_after","reason"]
    exists = os.path.exists(TRADE_LOG)
    try:
        with open(TRADE_LOG, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not exists:
                writer.writerow(header)
            for t in trades_list:
                writer.writerow([t.get("time"), t.get("entry"), t.get("exit"), t.get("profit"), t.get("balance_after"), t.get("reason")])
    except Exception as e:
        debug(f"failed to write trades csv: {e}")

def run_backtest(candles, initial_balance=INITIAL_BALANCE, risk_per_trade=RISK_PER_TRADE, stop_loss_pct=STOP_LOSS_PCT):
    if not candles:
        return {"error":"no candles"}, []
    closes = [c["close"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    vols = [c["volume"] for c in candles]
    times = [c["time"] for c in candles]

    ema_fast = ema_list(closes, EMA_FAST)
    ema_slow = ema_list(closes, EMA_SLOW)
    rsi_vals = rsi_list(closes, RSI_PERIOD)
    atr_vals = atr_list(highs, lows, closes, period=14)

    avg_vol20 = []
    for i in range(len(vols)):
        window = vols[max(0, i-20):i]
        avg_vol20.append(sum(window)/len(window) if window else vols[i])

    balance = float(initial_balance)
    position = None
    trades = []
    wins = 0
    losses = 0

    for i in range(len(closes)):
        # require lookback
        if i < max(EMA_SLOW, RSI_PERIOD) + 2:
            continue
        price = closes[i]
        prev = i-1
        cross_up = (ema_fast[prev] <= ema_slow[prev]) and (ema_fast[i] > ema_slow[i])
        cross_down = (ema_fast[prev] >= ema_slow[prev]) and (ema_fast[i] < ema_slow[i])
        vol_ok = vols[i] > (avg_vol20[i] * VOLUME_MULTIPLIER)
        rsi_ok = (rsi_vals[prev] > 25 and rsi_vals[prev] < 75)

        # ENTER
        if position is None:
            if cross_up and vol_ok and rsi_ok:
                risk_amount = balance * risk_per_trade
                if stop_loss_pct <= 0:
                    qty = balance / price
                else:
                    # qty such that risk_amount = qty * price * stop_loss_pct
                    qty = risk_amount / (price * stop_loss_pct)
                qty = max(qty, 1e-12)
                stop_price = price * (1 - stop_loss_pct)
                position = {"entry": price, "qty": qty, "stop": stop_price, "entry_time": times[i], "entry_idx": i}
        else:
            # stop loss check on candle low
            if lows[i] <= position["stop"]:
                exit_price = position["stop"]
                proceeds = position["qty"] * exit_price
                profit = proceeds - (position["qty"] * position["entry"])
                balance = proceeds  # compound
                trade = {"time": times[i], "entry": position["entry"], "exit": exit_price, "profit": profit, "balance_after": balance, "reason":"SL"}
                trades.append(trade)
                if profit >= 0: wins += 1
                else: losses += 1
                position = None
                continue
            # exit on cross down
            if cross_down:
                exit_price = price
                proceeds = position["qty"] * exit_price
                profit = proceeds - (position["qty"] * position["entry"])
                balance = proceeds
                trade = {"time": times[i], "entry": position["entry"], "exit": exit_price, "profit": profit, "balance_after": balance, "reason":"X"}
                trades.append(trade)
                if profit >= 0: wins += 1
                else: losses += 1
                position = None
                continue

    stats = {
        "initial_balance": initial_balance,
        "final_balance": round(balance, 8),
        "profit_usd": round(balance - initial_balance, 8),
        "trades": len(trades),
        "wins": wins,
        "losses": losses,
        "win_rate": round((wins / (wins + losses) * 100) if (wins + losses) > 0 else 0, 2)
    }

    # append to CSV (helpful for download)
    try:
        append_trades_csv(trades)
    except Exception as e:
        debug(f"csv append failed: {e}")

    return stats, trades

# ---------------- Flask endpoints ----------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/status")
def api_status():
    return jsonify({"balance": INITIAL_BALANCE, "symbols": SYMBOLS})

@app.route("/api/candles")
def api_candles_route():
    symbol = request.args.get("symbol", SYMBOLS[0])
    interval = request.args.get("interval", "1m")
    limit = int(request.args.get("limit", 500))
    try:
        candles = fetch_klines(symbol, interval=interval, limit=limit)
        return jsonify({"symbol": symbol, "candles": candles})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/backtest", methods=["POST"])
def api_backtest():
    # accept JSON or form-data; support CSV file upload as multipart/form-data
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    # CSV upload
    if "csv" in request.files:
        f = request.files["csv"]
        text = f.read().decode("utf-8")
        lines = [ln for ln in text.splitlines() if ln.strip()]
        candles = []
        for i, ln in enumerate(lines):
            if i == 0 and ("time" in ln.lower() and "open" in ln.lower()):
                continue
            parts = ln.split(",")
            if len(parts) < 6:
                continue
            t = parts[0].strip()
            try:
                if t.isdigit() and len(t) > 10:
                    t = int(t)
                else:
                    t = int(datetime.fromisoformat(t).timestamp() * 1000)
            except Exception:
                t = int(datetime.utcnow().timestamp() * 1000)
            candles.append({"time": int(t), "open": float(parts[1]), "high": float(parts[2]), "low": float(parts[3]), "close": float(parts[4]), "volume": float(parts[5])})
        initial = float(data.get("initial_balance", INITIAL_BALANCE))
        risk = float(data.get("risk_per_trade", RISK_PER_TRADE))
        stop = float(data.get("stop_loss_pct", STOP_LOSS_PCT))
        stats, trades = run_backtest(candles, initial_balance=initial, risk_per_trade=risk, stop_loss_pct=stop)
        return jsonify({"stats": stats, "trades": trades})

    symbol = data.get("symbol", SYMBOLS[0])
    months = int(data.get("months", 1))
    interval = data.get("interval", "1m")
    initial = float(data.get("initial_balance", INITIAL_BALANCE))
    risk = float(data.get("risk_per_trade", RISK_PER_TRADE))
    stop = float(data.get("stop_loss_pct", STOP_LOSS_PCT))

    end = datetime.utcnow()
    start = end - timedelta(days=30 * months)
    # paginate from start time to now
    all_candles = []
    start_ms = int(start.timestamp() * 1000)
    while True:
        try:
            part = fetch_klines_page(symbol, interval=interval, limit=1000, start_time=start_ms)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        if not part:
            break
        all_candles.extend(part)
        if len(part) < 1000:
            break
        start_ms = part[-1]["time"] + 1
        time.sleep(0.12)

    if not all_candles:
        return jsonify({"error": "no candles retrieved"}), 500

    stats, trades = run_backtest(all_candles, initial_balance=initial, risk_per_trade=risk, stop_loss_pct=stop)
    return jsonify({"stats": stats, "trades": trades})

@app.route("/download_trades")
def download_trades():
    if os.path.exists(TRADE_LOG):
        return send_file(TRADE_LOG, as_attachment=True)
    return jsonify({"error": "no trades file"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
