from pathlib import Path
from typing import Any, Optional

from lib import constants

PREFIX = f"[{constants.CMD_COLOR}?{constants.RESET_COLOR}]{constants.QUESTION_COLOR}"
PREFIX_FAIL = f"{constants.ERROR_COLOR}>>{constants.QUESTION_COLOR}"


def text(
        message: str,
        name: str = "value",
        default: Optional[str] = None,
        allow_blank: bool = False
    ) -> str:
    if default is not None and allow_blank:
        raise ValueError("Can't allow blanks with a default value (entering blank means default)")

    ask_txt = f"{PREFIX} {message}"
    if default is not None:
        ask_txt += f" ({default=})"
    ask_txt += ": "

    while True:
        value = input(f"{PREFIX} {message} ({default=}): ")
        # If we don't have a default value but we allow blanks
        # return a blank string
        if value == "" and default is None and allow_blank:
            return ""
        # If we don't have a default value and blanks aren't allowed
        # ask for a valid value again.
        elif value == "" and default is None and not allow_blank:
            print("Value can't be blank.")
            continue
        # If we have a default value and the user didn't enter anything
        # return the default value
        elif value == "" and default is not None:
            return default

        return value


def confirm(message: str, name: str = "value", default: bool = False) -> bool:
    suffix = "(y/N): " if default is False else "(Y/n): "
    while True:
        value = input(f"{PREFIX} {message} {suffix}")
        if value.lower() in ("y", "yes"):
            return True
        elif value.lower() in ("n", "no"):
            return False
        elif value == "":
            return default
        else:
            print(f"{PREFIX_FAIL} {name} can only be y/n (yes/no).")


def choice(message: str, choices: list[Any], name: str = "choice") -> Any:
    str_choices = {str(choice): choice for choice in choices}
    option_lines = []
    for index, choice in enumerate(choices):
        option_lines.append(f"{index + 1}. - {str(choice)}")
    option_text = "\n".join(option_lines)

    while True:
        print(option_text)
        value = input(f"{PREFIX} {message}: ")

        if value.isdigit():
            int_value = int(value)
            if len(choices) >= int_value > 0:
                return choices[int_value - 1]  # Lists start at 0, not 1
        if value in str_choices:
            return str_choices[value]

        print(
            f"{PREFIX_FAIL} Invalid input for {name}, expected 1-{len(choices)} "
            "or one of the choice values: value1 or value2, ..."
        )


def multi_choice(message: str, choices: list[Any], name: str = "choice") -> list[Any]:
    str_choices = {str(choice): choice for choice in choices}
    option_lines = []
    for index, choice in enumerate(choices):
        option_lines.append(f"{index + 1}. - {str(choice)}")
    option_text = "\n".join(option_lines)

    while True:
        print(option_text)
        values = input(f"{PREFIX} {message} (enter comma separated list of values): ").split(",")
        picked = []
        for value in values:
            if value.isdigit():
                int_value = int(value)
                if len(choices) >= int_value > 0:
                    picked.append(choices[int_value - 1])
                    continue
            if value in str_choices:
                picked.append(str_choices[value])
                continue

            print(
                f"{PREFIX_FAIL} Invalid input for {name}: '{value}', expected 1-{len(choices)} "
                "or one of the choice values. Example multi-value input: 1,2,3 or value1,value2. "
                "Example single value input: 1 or value1."
            )
            break
        else:
            return picked


def path(message: str, name: str = "path", exists: bool = True, make_absolute: bool = True) -> Path:
    while True:
        value = input(f"{PREFIX} {message}: ")

        # Don't interpret empty input as `.` path`
        if value == "":
            print(f"{PREFIX_FAIL} '{value}' is not a valid {name}.")
            continue
        else:
            value = Path(value)

        if exists and not value.exists():
            print(f"{PREFIX_FAIL} '{value}' is not a valid {name}.")
            continue
        if make_absolute:
            value = value.absolute()
        return value
