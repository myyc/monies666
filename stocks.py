import time

from flask import Flask, render_template, json
import requests
import configparser, os

from mongo666 import *


app = Flask(__name__)

from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options

cache_opts = {
    "cache.type": 'file',
    "cache.data_dir": "/tmp/cache/data",
    "cache.lock_dir": "/tmp/cache/lock"
}

cache = CacheManager(**parse_cache_config_options(cache_opts))

getts = lambda d: int(time.mktime(datetime.datetime.strptime(d, "%Y-%m-%d").timetuple()))


def reweigh(l, n):
    l["values"] = [{"x": d["x"], "y": d["y"] / (0.0001 + n * l["values"][0]["y"])} for d in l["values"]]
    return l


def weighfund(isin, v):
    md = getfundweights(isin)
    if md["w"] > 0:
        v["values"] = [{"x": d["x"], "y": d["y"] * md["w"]} for d in v["values"]]
    return v


@app.route("/stocks/", defaults={"symbols": None, "startdate": None, "enddate": None})
@app.route("/stocks/<symbols>", defaults={"startdate": None, "enddate": None})
@app.route("/stocks/<symbols>/<enddate>", defaults={"startdate": None})
@app.route("/stocks/<symbols>/<startdate>/<enddate>")
def stocks(symbols=None, startdate=None, enddate=None):
    if symbols is None:
        symbols = "AAPL"
    args = symbols
    if startdate is not None:
        args += "/" + startdate
    if enddate is not None:
        args += "/" + enddate
    return render_template("main.html", what="getstocks", args=args)


@app.route("/funds/", defaults={"isins": None, "startdate": None, "enddate": None})
@app.route("/funds/<isins>", defaults={"startdate": None, "enddate": None})
@app.route("/funds/<isins>/<enddate>", defaults={"startdate": None})
@app.route("/funds/<isins>/<startdate>/<enddate>")
def funds(isins=None, startdate=None, enddate=None):
    if isins is None or isins == "default":
        isins = ",".join(getallisins())
    args = isins
    if startdate is not None:
        args += "/" + startdate
    if enddate is not None:
        args += "/" + enddate
    return render_template("main.html", what="getfunds", args=args)


@app.route("/getfunds/<isins>", defaults={"startdate": None, "enddate": None})
@app.route("/getfunds/<isins>/<startdate>", defaults={"enddate": None})
@app.route("/getfunds/<isins>/<startdate>/<enddate>")
def getfunds(isins, startdate=None, enddate=None):
    enddate = datetime.datetime.today() if enddate is None else datetime.datetime.strptime(enddate, "%Y-%m-%d")
    startdate = datetime.datetime(2014, 2, 1) if startdate is None else datetime.datetime.strptime(startdate,
                                                                                                   "%Y-%m-%d")
    isins = isins.split(",")
    return json.dumps([weighfund(isin, getfrommorningstar(isin, startdate, enddate, "EUR")) for isin in isins])


@app.route("/getstocks/<symbols>", defaults={"startdate": None, "enddate": None})
@app.route("/getstocks/<symbols>/<startdate>", defaults={"enddate": None})
@app.route("/getstocks/<symbols>/<startdate>/<enddate>")
def getstocks(symbols, startdate=None, enddate=None):
    enddate = datetime.datetime.today() if enddate is None else datetime.datetime.strptime(enddate, "%Y-%m-%d")
    startdate = datetime.datetime.today() - datetime.timedelta(
        days=360) if startdate is None else datetime.datetime.strptime(startdate, "%Y-%m-%d")
    symbols = symbols.split(",")
    return json.dumps([reweigh(get(sym, startdate, enddate), len(symbols)) for sym in symbols])


def get(symbol, startdate, enddate):
    cur = getstocksfrommongo(symbol, startdate, enddate)
    if cur.count() == 0:
        return getfromyahoo(symbol, startdate, enddate)
    else:
        return {"key": symbol, "values": [{"x": time.mktime(d["date"].timetuple()), "y": d["close"]} for d in cur]}


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


@cache.cache("funds", expire=600)
def getfrommorningstar(isin, startdate, enddate, currency):
    url = getmorningstarurl()

    p = {
        "currencyId": currency,
        "frequency": "hourly",
        "startDate": startdate.strftime("%Y-%m-%d"),
        "endDate": enddate.strftime("%Y-%m-%d"),
        "priceType": "",
        "outputType": "COMPACTJSON",
        "idType": "isin",
        "id": isin
    }

    return {
        "key": getfundname(isin).lower(),
        "values": [{"x": d[0] / 1000., "y": d[1]} for d in json.loads(requests.get(url, params=p).text)]
    }


def getmorningstarurl():
    config = configparser.RawConfigParser()
    config.read(app.root_path + "/conf/default.cfg")
    return config.get("morningstar", "url")


if __name__ == "__main__":
    app.run(debug=True)

