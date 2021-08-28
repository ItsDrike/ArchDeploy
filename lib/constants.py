import os
import pathlib

from lib.colors import ANSIColor


IS_EFI = pathlib.Path("/sys/firmware/efi/efivars").exists()
DEBUG = os.getenv("DEBUG", False)

# Define specific colors for certain actions
SUCCESS_COLOR = ANSIColor.RESET + ANSIColor.GREEN
ERROR_COLOR = ANSIColor.RESET + ANSIColor.RED + ANSIColor.BOLD
WARN_COLOR = ANSIColor.RESET + ANSIColor.YELLOW
INFO_COLOR = ANSIColor.RESET + ANSIColor.CYAN
NOTE_COLOR = ANSIColor.RESET + ANSIColor.FAINT
DEBUG_COLOR = ANSIColor.RESET + ANSIColor.BLUE
CMD_COLOR = ANSIColor.RESET + ANSIColor.MAGENTA
QUESTION_COLOR = ANSIColor.RESET + ANSIColor.BOLD
RESET_COLOR = ANSIColor.RESET
