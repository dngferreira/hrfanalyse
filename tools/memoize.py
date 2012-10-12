class Memoize:
    """
    Memoize class copied from a python cookbook, to be used on the
    compress functions this should reduce the number of calculations
    to be made when building a distance matrix.
    """
    def __init__(self, fn):
        self.fn = fn
        self.cache = {}
    def __call__(self, *args):
        if args not in self.cache:
            self.cache[args] = self.fn(*args)
        return self.cache[args]
