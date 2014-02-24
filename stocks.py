from flask import Flask, render_template, json
import urllib.request
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
    url = "http://ichart.finance.yahoo.com/table.csv?s={}&d=2&e=18&f=2014&a=2&b=18&c=2013&ignore=.csv".format(symbol)
    with urllib.request.urlopen(url) as f:
        next(f)

        def dec(r):
            r = r.decode("utf-8").split(",")
            return {
                "x": int(time.mktime(datetime.datetime.strptime(r[0], "%Y-%m-%d").timetuple())),
                "y": float(r[4])
            }

        data = [dec(r) for r in f]
        m = list(map(lambda d: {"x": d["x"], "y": d["y"] / (n*data[-1]["y"])}, data))
        m.reverse()
        return {"key": symbol, "values": m}


if __name__ == "__main__":
    app.run()

