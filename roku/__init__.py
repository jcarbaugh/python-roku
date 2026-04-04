from roku.core import Roku, __version__  # noqa
from roku.models import Application, Channel, RokuException  # noqa


def __getattr__(name):
    if name == "AsyncRoku":
        from roku._async import AsyncRoku

        return AsyncRoku
    raise AttributeError(f"module 'roku' has no attribute {name}")
