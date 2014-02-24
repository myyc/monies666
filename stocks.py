from flask import Flask, render_template, json
import requests
import time, datetime

app = Flask(__name__)

from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options

cache_opts = {
    'cache.type': 'file',
    'cache.data_dir': '/tmp/cache/data',
    'cache.lock_dir': '/tmp/cache/lock'
}

cache = CacheManager(**parse_cache_config_options(cache_opts))


@app.route("/")
@app.route("/hi/")
@app.route("/hi/<symbols>")
def hello(symbols=None):
    if symbols is None:
        symbols = "AAPL"
    return render_template("main.html", sym=symbols)


@app.route("/fetch/")
@app.route("/fetch/<symbols>")
def fetch(symbols=None):
    symbols = symbols.split(",")
    return json.dumps([get(sym, len(symbols)) for sym in symbols])


#@cache.cache("getsym", expire=600)
def get(symbol, n):
    url = "http://ichart.finance.yahoo.com/table.csv"
    p = {
        "s": symbol,
        "e": 18,
        "d": 2,
        "f": 2014,
        "b": 18,
        "a": 2,
        "c": 2013
    }

    def dec(r):
        r = r.split(",")
        return {
            "x": int(time.mktime(datetime.datetime.strptime(r[0], "%Y-%m-%d").timetuple())),
            "y": float(r[4])
        }

    data = [dec(r) for r in requests.get(url, params=p).text.split("\n")]
    m = list(map(lambda d: {"x": d["x"], "y": d["y"] / (n * data[-1]["y"])}, data))
    m.reverse()
    print(m)
    return {"key": symbol, "values": m}


if __name__ == "__main__":
    app.run()

