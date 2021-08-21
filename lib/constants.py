import os
import pathlib

import colorama


IS_EFI = pathlib.Path("/sys/firmware/efi/efivars").exists()
DEBUG = os.getenv("DEBUG", False)

SUCCESS_COLOR = colorama.Style.NORMAL + colorama.Fore.GREEN
ERROR_COLOR = colorama.Fore.RED + colorama.Style.BRIGHT
WARN_COLOR = colorama.Style.NORMAL + colorama.Fore.YELLOW
INFO_COLOR = colorama.Style.NORMAL + colorama.Fore.CYAN
NOTE_COLOR = colorama.Style.DIM + colorama.Fore.RESET
DEBUG_COLOR = colorama.Style.NORMAL + colorama.Fore.BLUE
CMD_COLOR = colorama.Style.NORMAL + colorama.Fore.MAGENTA
