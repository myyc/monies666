Stocks
======

A sandbox to monitor a bunch of crap (stocks, funds). The idea is to evolve it into some sort of portfolio monitoring
tool with maybe something to do with forecasting etc.

Dependencies:

* Python3 (tested on v3.3)
* MongoDB (tested on v2.4)
* Pymongo (tested on v2.6)
* Flask (tested on v0.10)
* Requests (tested on v2.2)
* Beaker (tested on v1.6)

No hardcore caching/DB operations yet so earlier versions should be fine too.

Warnings
========

1. The MongoDB serialising calls are absolute crap: the DB check verifies whether an entry in the DB exists, regardless
of whether it is up-to-date (in which case you will get old data).
2. The code looks a bit hideous.
3. DO NOT USE, IT IS NOT USABLE.

TODO
====

* Fix \#1. so that everything works decently in my machine
* Implement a bunch of things (the "am I rich" idea sounds cool)
* Restructure the code a bit (`stocks.py` is dreadful, although it did get better)
