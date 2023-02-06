class StreamError(Exception):
    """Base class for all streamx exceptions"""


class StreamClosedError(StreamError):
    """
    Raised when operations are performed on a closed stream
    """


class StreamShortCircuitError(StreamError):
    """
    Raised when a stream is being consumed by the same task
    and a new item is pushed
    """
