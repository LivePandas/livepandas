from decorator import decorator




def register(name, **kwargs):
    """ Function that creates a decorator. """

    # Add a dictionary to this function.
    if not hasattr(register, '_functions'):
        regiser._functions = {}

    def _register(f, *args, **kw):
        # Register this to a tornado web server.
        return f(*args, **kwargs)

    def register(f):
        register._functions[name] = f
        return decorator(_register, f)

    return register
