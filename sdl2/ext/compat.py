"""
Python compatibility helpers.
"""
import sys
import collections
import warnings

__all__ = ["stringify", "byteify", "isiterable", "ISPYTHON2", "ISPYTHON3",
           "platform_is_64bit", "deprecated", "deprecation",
           "UnsupportedError", "ExperimentalWarning", "experimental",
           ]

ISPYTHON2 = False
ISPYTHON3 = False

if sys.version_info[0] < 3:
    # Wrapper around bytes() and decode() for Python 2.x
    byteify = lambda x, enc: x.encode(enc)
    # Wrapper around str() for Python 2.x
    stringify = lambda x, enc: str(x)
    ISPYTHON2 = True
else:
    __all__ += ["long", "unichr", "callable", "unicode"]
    byteify = bytes
    stringify = lambda x, enc: x.decode(enc)
    long = int
    unichr = chr
    callable = lambda x: isinstance(x, collections.Callable)
    ISPYTHON3 = True
    unicode = str

isiterable = lambda x: isinstance(x, collections.Iterable)


def platform_is_64bit():
    """Checks, if the platform is a 64-bit machine."""
    is64bit = sys.maxsize > 2 ** 32
    if sys.platform == "cli":
        is64bit = sys.executable.endswith("ipy64.exe")
    return is64bit


def deprecated(func):
    """A simple decorator to mark functions and methods as deprecated."""
    def wrapper(*fargs, **kw):
        warnings.warn("%s is deprecated." % func.__name__,
                      category=DeprecationWarning, stacklevel=2)
        return func(*fargs, **kw)
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    wrapper.__dict__.update(func.__dict__)
    return wrapper


def deprecation(message):
    """Prints a deprecation message."""
    warnings.warn(message, category=DeprecationWarning, stacklevel=2)


class UnsupportedError(Exception):
    """Indicates that a certain class, function or behaviour is not
    supported.
    """
    def __init__(self, obj, msg=None):
        """Creates an UnsupportedError for the specified obj.

        If a message is passed in msg, it will be printed instead of the
        default message.
        """
        super(UnsupportedError, self).__init__()
        self.obj = obj
        self.msg = msg

    def __str__(self):
        if self.msg is None:
            return "'%s' is not supported" % repr(self.obj)
        return repr(self.msg)


class ExperimentalWarning(Warning):
    """Indicates that a certain class, function or behaviour is in an
    experimental state.
    """
    def __init__(self, obj, msg=None):
        """Creates a ExperimentalWarning for the specified obj.

        If a message is passed in msg, it will be printed instead of the
        default message.
        """
        super(ExperimentalWarning, self).__init__()
        self.obj = obj
        self.msg = msg

    def __str__(self):
        if self.msg is None:
            return "%s is in an experimental state." % repr(self.obj)
        return repr(self.msg)


def experimental(func):
    """A simple decorator to mark functions and methods as experimental."""
    def wrapper(*fargs, **kw):
        warnings.warn("%s" % func.__name__, category=ExperimentalWarning,
                      stacklevel=2)
        return func(*fargs, **kw)
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    wrapper.__dict__.update(func.__dict__)
    return wrapper
