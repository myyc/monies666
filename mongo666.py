import datetime
import pymongo

__author__ = 'marco'


def getstocksfrommongo(symbol, startdate, enddate):
    conn = pymongo.Connection("127.0.0.1")
    coll = conn["stocks"]["daily"]
    return coll.find({"symbol": symbol, "date": {"$gte": startdate, "$lte": enddate}}).sort([("date", 1)])


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


def getfundweights(isin):
    conn = pymongo.Connection("127.0.0.1")
    coll = conn["funds"]["private"]
    w = 0
    eur = 0
    for r in coll.find({"isin": isin}):
        w += r["quotes"]
        eur += r["jewgolds"]
    return {"w": w, "eur": eur}


def getfundname(isin):
    conn = pymongo.Connection("127.0.0.1")
    coll = conn["funds"]["metadata"]
    d = coll.find_one({"isin": isin})
    return isin if d is None else d["abbr"]


def getallisins():
    conn = pymongo.Connection("127.0.0.1")
    coll = conn["funds"]["metadata"]
    return [d["isin"] for d in coll.find()]
