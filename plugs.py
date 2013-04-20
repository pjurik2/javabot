from plugins import *

glvars = dir()

def _getmodules():
    results = {}
    for item in glvars:
        if item[0] != "_":
            results[item] = eval(item)

    return results
