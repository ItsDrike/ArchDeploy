import sys
from typing import TextIO


class ANSIColor:
    BLACK = "\033[0;30m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32,"
    BROWN = "\033[0;33m"
    BLUE = "\033[0;34m"
    MAGENTA = "\033[0;35m"
    CYAN = "\033[0;36m"
    LIGHT_GRAY = "\033[0;37m"
    DARK_GRAY = "\033[1;30m"
    LIGHT_RED = "\033[1;31m"
    LIGHT_GREEN = "\033[1;32m"
    YELLOW = "\033[1;33m"
    LIGHT_BLUE = "\033[1;34m"
    LIGHT_PURPLE = "\033[1;35m"
    LIGHT_CYAN = "\033[1;36m"
    LIGHT_WHITE = "\033[1;37m"

    BOLD = "\033[1m"
    FAINT = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    NEGATIVE = "\033[7m"
    CROSSED = "\033[9m"

    RESET = "\033[0m"


class ColorAutoresettingStream:
    """Wrap sys.stdout and sys.stderr and automatically reset the color after each write."""

    def __init__(self, wrapped: TextIO):
        self.__wrapped = wrapped

    def __getattr__(self, name: str):
        return getattr(self.__wrapped, name)

    def __enter__(self, *args, **kwargs):
        return self.__wrapped.__enter__(*args, **kwargs)

    def __exit__(self, *args, **kwargs):
        return self.__wrapped.__exit__(*args, **kwargs)

    def write(self, text: str):
        self.__wrapped.write(text)
        self.__wrapped.flush()
        self.__wrapped.write(ANSIColor.RESET)


# Ensure automatic color reset after writing to stdout or stderr buffer
if not isinstance(sys.stdout, ColorAutoresettingStream):
    sys.stdout = ColorAutoresettingStream(sys.stdout)
if not isinstance(sys.stderr, ColorAutoresettingStream):
    sys.stderr = ColorAutoresettingStream(sys.stderr)
