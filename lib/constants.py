import os
import pathlib

import colorama


IS_EFI = pathlib.Path("/sys/firmware/efi/efivars").exists()
DEBUG = os.getenv("DEBUG", False)


RESET_COLOR = colorama.Style.RESET_ALL + colorama.Fore.RESET
SUCCESS_COLOR = RESET_COLOR + colorama.Fore.GREEN
ERROR_COLOR = RESET_COLOR + colorama.Fore.RED + colorama.Style.BRIGHT
WARN_COLOR = RESET_COLOR + colorama.Fore.YELLOW
INFO_COLOR = RESET_COLOR + colorama.Fore.CYAN
NOTE_COLOR = RESET_COLOR + colorama.Style.DIM
DEBUG_COLOR = RESET_COLOR + colorama.Fore.BLUE
CMD_COLOR = RESET_COLOR + colorama.Fore.MAGENTA
QUESTION_COLOR = RESET_COLOR + colorama.Style.BRIGHT
