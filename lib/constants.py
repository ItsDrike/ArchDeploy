import os
import sys
import pathlib
from typing import TextIO


IS_EFI = pathlib.Path("/sys/firmware/efi/efivars").exists()
DEBUG = os.getenv("DEBUG", False)

_RED = "\033[0;31m"
_GREEN = "\033[0;32,"
_YELLOW = "\033[1;33m"
_BLUE = "\033[0;34m"
_MAGENTA = "\033[0;35m"
_CYAN = "\033[0;36m"
_BOLD = "\033[1m"
_FAINT = "\033[2m"

RESET_COLOR = "\033[0m"
SUCCESS_COLOR = RESET_COLOR + _GREEN
ERROR_COLOR = RESET_COLOR + _RED + _BOLD
WARN_COLOR = RESET_COLOR + _YELLOW
INFO_COLOR = RESET_COLOR + _CYAN
NOTE_COLOR = RESET_COLOR + _FAINT
DEBUG_COLOR = RESET_COLOR + _BLUE
CMD_COLOR = RESET_COLOR + _MAGENTA
QUESTION_COLOR = RESET_COLOR + _BOLD


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
        self.__wrapped.write(RESET_COLOR)


# Ensure automatic color reset after writing to any of these buffers
sys.stdout = ColorAutoresettingStream(sys.stdout)
sys.stderr = ColorAutoresettingStream(sys.stderr)
