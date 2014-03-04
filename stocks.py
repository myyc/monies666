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


@app.route("/stocks/<symbols>", defaults={"startdate": None, "enddate": None})
@app.route("/stocks/<symbols>/<enddate>", defaults={"startdate": None})
@app.route("/hi/<symbols>/<startdate>/<enddate>")
def hello(symbols=None, startdate=None, enddate=None):
    if symbols is None:
        symbols = "AAPL"
    args = symbols
    if startdate is not None:
        args += "/" + startdate
    if enddate is not None:
        args += "/" + enddate
    return render_template("main.html", args=args)




@app.route("/fetch/<symbols>", defaults={"startdate": None, "enddate": None})
@app.route("/fetch/<symbols>/<startdate>", defaults={"enddate": None})
@app.route("/fetch/<symbols>/<startdate>/<enddate>")
def fetch(symbols, startdate=None, enddate=None):
    enddate = datetime.datetime.today() if enddate is None else datetime.datetime.strptime(enddate, "%Y-%m-%d")
    startdate = datetime.datetime.today() - datetime.timedelta(
        days=360) if startdate is None else datetime.datetime.strptime(startdate, "%Y-%m-%d")
    symbols = symbols.split(",")
    return json.dumps([reweigh(get(sym, startdate, enddate), len(symbols)) for sym in symbols])


def get(symbol, startdate, enddate):
    conn = pymongo.Connection("127.0.0.1")
    coll = conn["stocks"]["daily"]
    cur = coll.find({"symbol": symbol, "date": {"$gte": startdate, "$lte": enddate}}).sort([("date", 1)])
    if cur.count() == 0:
        return getfromyahoo(symbol, startdate, enddate)
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


def getfromyahoo(symbol, startdate, enddate):
    url = "http://ichart.finance.yahoo.com/table.csv"
    p = {
        "s": symbol,
        "f": enddate.year,
        "d": enddate.month - 1,
        "e": enddate.day,
        "c": startdate.year,
        "a": startdate.month - 1,
        "b": startdate.day,
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


def getfrommorningstar(isin, startdate, enddate, currency):
    url = "http://tools.morningstar.it/api/rest.svc/timeseries_price/jbyiq3rhyf"
    
    p = {
        "currencyId": currency,
        "frequency": "daily",
        "startDate": startdate.strftime("%Y-%m-%d"),
        "endDate": enddate.strftime("%Y-%m-%d"),
        "priceType": "",
        "outputType": "COMPACTJSON",
        "idType": "isin",
        "id": isin
    }
    &priceType=&outputType=COMPACTJSON&id=LU0418790928"

if __name__ == "__main__":
    app.run(debug=True)

