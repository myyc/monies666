import datetime
from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options

import configparser
from flask import json
import requests
import time
from mongo666 import insertintomongo, getfundcurrency

cache_opts = {
    "cache.type": 'file',
    "cache.data_dir": "/tmp/cache/data",
    "cache.lock_dir": "/tmp/cache/lock"
}

cache = CacheManager(**parse_cache_config_options(cache_opts))

getts = lambda d: int(time.mktime(datetime.datetime.strptime(d, "%Y-%m-%d").timetuple()))

app = None

def getfromyahoo(symbol, startdate, enddate):
    @cache.cache("yahoostocks", expire=600)
    def geturlandparams(sym, sy, sm, sd, ey, em, ed):
        app.logger.info("Cache outdated, fetching from Yahoo.")
        return "http://ichart.finance.yahoo.com/table.csv", {
            "s": sym,
            "c": sy,
            "a": sm - 1,
            "b": sd,
            "f": ey,
            "d": em - 1,
            "e": ed,
            "g": "d",
            "ignore": ".csv"
        }

    url, p = geturlandparams(symbol, startdate.year, startdate.month, startdate.day,
                             enddate.year, enddate.month, enddate.day)
    text = requests.get(url, params=p).text

    insertintomongo(symbol, text)

    def dec(r):
        r = r.split(",")
        return {
            "x": getts(r[0]),
            "y": float(r[4])
        }

    return [dec(r) for r in text.strip().split("\n")[1:]]


def getfrommorningstar(isin, startdate, enddate, currency=None):
    @cache.cache("funds", expire=1200)
    def geturlandparams(_isin, sd, ed, currency):
        app.logger.info("Cache outdated, fetching from Morningstar.")
        return getmorningstarurl(), {
            "currencyId": currency,
            "frequency": "hourly",
            "startDate": sd,
            "endDate": ed,
            "priceType": "",
            "outputType": "COMPACTJSON",
            "idType": "isin",
            "id": _isin
        }

    if currency is None:
        currency = getfundcurrency(isin)
    url, p = geturlandparams(isin, startdate.strftime("%Y-%m-%d"), enddate.strftime("%Y-%m-%d"), currency)

    return [{"x": d[0] / 1000., "y": d[1]} for d in json.loads(requests.get(url, params=p).text)]


def getmorningstarurl():
    config = configparser.RawConfigParser()
    config.read(app.root_path + "/conf/default.cfg")
    return config.get("morningstar", "url")