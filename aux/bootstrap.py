import subprocess
import os
import os.path
from flask import request


def flask_compile(app):
    comp = {
        ".less": lambda p: ["lessc", p["inf"], p["outf"]],
        ".coffee": lambda p: ["coffee", "--compile", p["inf"]]
    }

    exts = {
        ".less": "css",
        ".coffee": "js"
    }

    def _getpath():
        p = request.path
        static = app.static_folder
        for path, _, fns in os.walk(static):
            for f in fns:
                np, e = os.path.splitext(f)
                if e in exts:
                    nnp = os.path.join(path, np + "." + exts[e])
                    if p in nnp:
                        return os.path.join(path, f)
        return

    @app.before_request
    def _compile():
        fn = _getpath()
        if fn is None:
            return
        basename, ext = os.path.splitext(fn)
        if ext not in exts:
            return
        newfn = basename + "." + exts[ext]
        tbc = False
        if os.path.exists(newfn):
            if os.path.getmtime(newfn) <= os.path.getmtime(fn):
                os.unlink(newfn)
                tbc = True
        else:
            tbc = True
        if tbc:
            r = subprocess.call(comp[ext]({"inf": fn, "outf": newfn}), shell=False)
            if r == 1:
                raise RuntimeError("Couldn't compile '{}'".format(newfn))
