class StreamError(Exception):
    """Base class for all streamz exceptions"""


class StreamClosedError(StreamError):
    """
    Raised when a stream is closed and a new item is pushed
    or when a stream is iterated over after it is closed
    """


class StreamConsumerError(StreamError):
    """
    Raised when a task tries to iterate over a stream that is
    already being consumed by another task
    """


class StreamShortCircuitError(StreamError):
    """
    Raised when a stream is being consumed by the same task
    and a new item is pushed
    """
