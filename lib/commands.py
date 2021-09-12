import os
import pathlib
import sys
import subprocess

from lib import constants, questions

# Find proper command for root cmd execution
HAS_SUDO = pathlib.Path("/usr/bin/sudo").exists()
HAS_DOAS = pathlib.Path("/usr/bin/doas").exists()


def debug_confirm_run(command: str) -> bool:
    """If DEBUG is on, ask user for confirmation to run given command."""
    if constants.DEBUG:
        cnfrm: bool = questions.confirm(  # type: ignore
            f"{constants.DEBUG_COLOR}[DEBUG] Running command: "
            f"{constants.CMD_COLOR}{command}"
        )
        return cnfrm
    else:
        return True


def run_cmd(cmd: str, capture_out: bool = False, enable_debug: bool = True) -> subprocess.CompletedProcess:
    """Run given command."""
    args = {}
    if capture_out:
        args.update({"stdout": subprocess.PIPE, "stderr": subprocess.STDOUT})
    else:
        # If we aren't capturing output, it will be eachoed, this however won't reset colorama's color
        # which we don't want, the command output should always be without any special coloring
        sys.stdout.write(constants.RESET_COLOR)
        sys.stdout.flush()

    if not enable_debug or debug_confirm_run(cmd):
        return subprocess.run(cmd, shell=True, **args)
    else:
        # If debug confirm returned False, end with error code 1
        return subprocess.CompletedProcess(cmd, returncode=1)


def run_root_cmd(cmd: str, capture_out: bool = False, enable_debug: bool = True) -> subprocess.CompletedProcess:
    """Run given command as root."""
    if os.getuid() != 0:
        # Use available root escalation tool to run given cmd
        if HAS_SUDO:
            root_cmd = f"sudo {cmd}"
        elif HAS_DOAS:
            root_cmd = f"doas {cmd}"
        else:
            # We need to escape double quotes here, because we use them with su command
            print(
                f"{constants.DEBUG_COLOR}Neither sudo nor doas were found, falling back "
                "to su to execute root commands (enter root password, not user password)"
            )
            cmd = cmd.replace('"', r'\"')
            root_cmd = f'su -c "{cmd}"'

        return run_cmd(root_cmd, capture_out, enable_debug)
    else:
        return run_cmd(cmd, capture_out, enable_debug)


def drop_to_shell(enable_debug: bool = False) -> None:
    print(
        f"{constants.INFO_COLOR}Dropping to shell. After you made the desired changes, "
        f"use {constants.CMD_COLOR}exit{constants.INFO_COLOR} to return."
    )
    run_cmd("exec ${SHELL}", enable_debug=enable_debug)


def command_exists(cmd) -> bool:
    """Check if given command can be executed."""
    parts = cmd.split()
    executable = parts[0] if parts[0] not in ("sudo", "source", ".") else parts[1]
    proc = run_cmd(f"command -v {executable}", capture_out=True)
    return proc.returncode == 0
