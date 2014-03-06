import time

from flask import Flask, render_template, json

from aux.bootstrap import flask_compile
import getters
from mongo666 import *

app = Flask(__name__)
getters.app = app

midnight = lambda d: datetime.datetime(d.year, d.month, d.day)


def reweigh(l, n):
    l = [{"x": d["x"], "y": d["y"] / (0.0001 + n * l[0]["y"])} for d in l]
    return l


def weighfund(isin, v):
    md = getfundweights(isin)
    if md["w"] > 0:
        v = [{"x": d["x"], "y": d["y"] * md["w"]} for d in v]
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
    enddate = midnight(datetime.datetime.today()) if enddate is None else datetime.datetime.strptime(enddate,
                                                                                                     "%Y-%m-%d")
    startdate = datetime.datetime(2014, 1, 1) if startdate is None else datetime.datetime.strptime(startdate,
                                                                                                   "%Y-%m-%d")
    isins = isins.split(",")
    return json.dumps([
        {
            "key": getfundname(isin).lower(),
            "values": weighfund(isin, getters.getfrommorningstar(isin, startdate, enddate, "EUR"))
        } for isin in isins
    ])


@app.route("/getstocks/<symbols>", defaults={"startdate": None, "enddate": None})
@app.route("/getstocks/<symbols>/<startdate>", defaults={"enddate": None})
@app.route("/getstocks/<symbols>/<startdate>/<enddate>")
def getstocks(symbols, startdate=None, enddate=None):
    enddate = midnight(
        datetime.datetime.today() if enddate is None else datetime.datetime.strptime(enddate, "%Y-%m-%d"))
    startdate = midnight(datetime.datetime.today() - datetime.timedelta(
        days=360) if startdate is None else datetime.datetime.strptime(startdate, "%Y-%m-%d"))

    symbols = symbols.split(",")
    return json.dumps([{"key": sym, "values": reweigh(get(sym, startdate, enddate), len(symbols))} for sym in symbols])


@app.route("/")
@app.route("/amirich/")
@app.route("/amirich/<currency>")
def amirich(currency="EUR"):
    return render_template("amirich.html", currency=currency)


@app.route("/amirich/get/")
@app.route("/amirich/get/<currency>")
def nutshell(currency="EUR"):
    isins = getallisins()

    td = midnight(datetime.datetime.today() + datetime.timedelta(days=1))
    sd = td - datetime.timedelta(days=5)

    data = (getfundweights(isin) for isin in isins)
    lvs = (weighfund(isin, getters.getfrommorningstar(isin, sd, td, currency))[-1]["y"] for isin in isins)
    vsorig = {
        isin: (getfundweights(isin)["orig"],
               getfundweights(isin)["w"] * getters.getfrommorningstar(isin, sd, td)[-1]["y"])
        for isin in isins
    }

    return json.dumps({
        "tot": sum(lvs),
        "base": sum(d["eur"] for d in data),
        "orig": {isin: {
            "ret": (vsorig[isin][1] - vsorig[isin][0]) / vsorig[isin][0],
            "abbr": getfundname(isin)
        } for isin in vsorig}
    })


def get(symbol, startdate, enddate):
    cur = getstocksfrommongo(symbol, startdate, enddate)
    if cur.count() == 0:
        return getters.getfromyahoo(symbol, startdate, enddate)
    else:
        return [{"x": time.mktime(d["date"].timetuple()), "y": d["close"]} for d in cur]


if __name__ == "__main__":
    flask_compile(app)
    app.run(debug=True)
