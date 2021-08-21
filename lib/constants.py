import os
import pathlib

import colorama


IS_EFI = pathlib.Path("/sys/firmware/efi/efivars").exists()
DEBUG = os.getenv("DEBUG", False)

SUCCESS_COLOR = colorama.Fore.GREEN
ERROR_COLOR = colorama.Fore.RED + colorama.Style.BRIGHT
WARN_COLOR = colorama.Fore.YELLOW
INFO_COLOR = colorama.Fore.CYAN
NOTE_COLOR = colorama.Fore.RESET + colorama.Style.DIM
DEBUG_COLOR = colorama.Fore.BLUE
CMD_COLOR = colorama.Fore.MAGENTA
