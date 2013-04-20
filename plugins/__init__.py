import os

__all__ = []

for path in os.listdir('plugins'):
    if path[0] != "_" and path[-4:] != ".pyc":
        if path[-3:] == ".py":
            path = path[:-3]
        __all__.append(path)
