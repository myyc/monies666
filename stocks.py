from flask import Flask, render_template, json
import requests
import time
import datetime
import pymongo

app = Flask(__name__)

from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options

cache_opts = {
    'cache.type': 'file',
    'cache.data_dir': '/tmp/cache/data',
    'cache.lock_dir': '/tmp/cache/lock'
}

cache = CacheManager(**parse_cache_config_options(cache_opts))

getts = lambda d: int(time.mktime(datetime.datetime.strptime(d, "%Y-%m-%d").timetuple()))


def reweigh(l, n):
    l["values"] = [{"x": d["x"], "y": d["y"] / (0.0001 + n * l["values"][0]["y"])} for d in l["values"]]
    return l


@app.route("/hi/<symbols>", defaults={"fromdate": None, "todate": None})
@app.route("/hi/<symbols>/<todate>", defaults={"fromdate": None})
@app.route("/hi/<symbols>/<fromdate>/<todate>")
def hello(symbols=None, fromdate=None, todate=None):
    if symbols is None:
        symbols = "AAPL"
    args = symbols
    if fromdate is not None:
        args += "/" + fromdate
    if todate is not None:
        args += "/" + todate
    return render_template("main.html", args=args)


@app.route("/fetch/<symbols>", defaults={"fromdate": None, "todate": None})
@app.route("/fetch/<symbols>/<fromdate>", defaults={"todate": None})
@app.route("/fetch/<symbols>/<fromdate>/<todate>")
def fetch(symbols, fromdate=None, todate=None):
    todate = datetime.datetime.today() if todate is None else datetime.datetime.strptime(todate, "%Y-%m-%d")
    fromdate = datetime.datetime.today() - datetime.timedelta(
        days=360) if fromdate is None else datetime.datetime.strptime(fromdate, "%Y-%m-%d")
    symbols = symbols.split(",")
    return json.dumps([reweigh(get(sym, fromdate, todate), len(symbols)) for sym in symbols])


def get(symbol, fromdate, todate):
    conn = pymongo.Connection("127.0.0.1")
    coll = conn["stocks"]["daily"]
    cur = coll.find({"symbol": symbol, "date": {"$gte": fromdate, "$lte": todate}}).sort([("date", 1)])
    if cur.count() == 0:
        return getfromyahoo(symbol, fromdate, todate)
    else:
        return {"key": symbol, "values": [{"x": time.mktime(d["date"].timetuple()), "y": d["close"]} for d in cur]}


def insertintomongo(symbol, text):
    conn = pymongo.Connection("127.0.0.1")
    coll = conn["stocks"]["daily"]

    def dec(r):
        r = r.split(",")
        return {
            "symbol": symbol,
            "date": datetime.datetime.strptime(r[0], "%Y-%m-%d"),
            "open": float(r[1]),
            "high": float(r[2]),
            "close": float(r[3]),
            "volume": float(r[4]),
            "adjclose": float(r[5])
        }

    o = [dec(r) for r in text.strip().split("\n")[1:]]
    coll.insert(o)


def getfromyahoo(symbol, fromdate, todate):
    url = "http://ichart.finance.yahoo.com/table.csv"
    p = {
        "s": symbol,
        "f": todate.year,
        "d": todate.month - 1,
        "e": todate.day,
        "c": fromdate.year,
        "a": fromdate.month - 1,
        "b": fromdate.day,
        "g": "d",
        "ignore": ".csv"
    }
    text = requests.get(url, params=p).text

    insertintomongo(symbol, text)

    def dec(r):
        r = r.split(",")
        return {
            "x": getts(r[0]),
            "y": float(r[4])
        }

    return {"key": symbol, "values": [dec(r) for r in text.strip().split("\n")[1:]]}


if __name__ == "__main__":
    app.run(debug=True)

