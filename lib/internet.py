import json
import socket
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Literal, Union
import textwrap

import inquirer.shortcuts

from lib import commands, constants


class Interface:
    """Network interface/device class."""
    INTERFACE_TYPES = Union[
        Literal["UNKNOWN"],
        Literal["PHYSICAL"],
        Literal["WIRELESS"],
        Literal["TUN/TAP"],
        Literal["BRIDGE"]
    ]

    def __init__(self, name: str):
        self.name = name
        self.path = Path(f"/sys/class/net/{self.name}")
        self.type = self.get_type(self.path)

    @staticmethod
    def get_type(path: Path) -> "Interface.INTERFACE_TYPES":
        """Get the type of interface based on its path."""
        if path.joinpath("bridge").is_dir():
            return "BRIDGE"
        elif path.joinpath("tun_flags").is_file():
            return "TUN/TAP"
        elif path.joinpath("device").is_dir():
            if path.joinpath("wireless").is_dir():
                return "WIRELESS"
            else:
                return "PHYSICAL"
        else:
            return "UNKNOWN"

    def is_up(self) -> bool:
        """Check if the interface is UP."""
        flags_text = self.path.joinpath("flags").read_text().replace("\n", "")
        flags = int(flags_text, 16)
        return bool(flags & 1)

    def __repr__(self) -> str:
        return f"<Interface(name={self.name}, type={self.type}, UP={self.is_up()})>"

    @classmethod
    def get_interfaces(cls, skip_loopback: bool = True) -> list["Interface"]:
        interfaces = []
        for index, interface_name in socket.if_nameindex():
            if interface_name == "lo" and skip_loopback:
                continue

            interfaces.append(cls(interface_name))
        return interfaces


def check_connection(host: str = "https://ping.archlinux.org") -> bool:
    """Check if system is connected to the internet."""
    try:
        urllib.request.urlopen(host)
    except urllib.error.URLError:
        return False
    else:
        return True


def unblock_rfkill():
    """Check if any of the interfaces are blocked with RF-KILL, if so, unblock them."""
    proc = commands.run_root_cmd("rfkill --json", capture_out=True)
    rfkill_out = json.loads(proc.stdout.decode())

    for device_list in rfkill_out.values():
        for device in device_list:
            device_name = device["device"]
            device_type = device["type"]
            if device["soft"] == "blocked":
                print(
                    f"{constants.INFO_COLOR}Device {device_name} (type={device_type}) is soft-blocked with RF-KILL.\n"
                    "This can sometimes happen with live ISOs, unblocking..."
                )
                commands.run_root_cmd(f"rfkill unblock {device_type}")
            if device["hard"] == "blocked":
                print(
                    f"{constants.WARN_COLOR} Device {device_name} (type={device_type}) is hard-blocked with RF-KILL.\n"
                    "This usually implies a hardware switch toggle or something similar, can't unblock. "
                    "This may or may not cause further issues, depending on the device."
                )


def connect_ethernet(wait_time: int = 20, iteration_time: int = 2) -> bool:
    """Attempt to connect to the internet using Ethernet."""
    print(f"{constants.NOTE_COLOR}Please plug in the Ethernet cable, waiting {wait_time}s...")
    time_elapsed = 0
    while not check_connection() and time_elapsed < wait_time:
        time.sleep(iteration_time)
        time_elapsed += iteration_time

    if not check_connection():
        # The ethernet cable wasn't plugged in within the time limit
        while True:
            choice = inquirer.shortcuts.list_input(
                "Internet connection still isn't available, how do you want to continue?",
                choices=[
                    "Drop to shell and connect manually",
                    "Try to connect Ethernet again",
                    "Give up on internet connection"
                ]
            )
            if choice == "Drop to shell and connect manually":
                commands.drop_to_shell()
                if check_connection():
                    return True
                else:
                    continue
            elif choice == "Try to connect Ethernet again":
                return connect_ethernet(wait_time * 2, iteration_time)
            elif choice == "Give up on internet connection":
                return False
    return True


def _ensure_active_interface(interface_type: Union[Literal["WIRELESS"], Literal["PHYSICAL"]]) -> bool:
    """
    Ensure there is at least one active interface of given `interface_type`.

    If there is no available interface of given type, end with `False`,
    otherwise ask user which interface(s) of given type to bring up.

    Only return `True` when there is at least one interface of given type that's UP,
    if this wasn't achieved, return `False`.
    """
    # Make sure we have at least one interface of requested type on this device
    interfaces = [interface for interface in Interface.get_interfaces() if interface.type == interface_type]
    if len(interfaces) == 0:
        print(f"{constants.ERROR_COLOR}Couldn't find any interface of {interface_type} type!")
        choice = inquirer.shortcuts.list_input(
            "How do you wish to proceed?",
            choices=["Drop to shell and correct this", f"Give up on {interface_type} type"]
        )
        if choice == "Drop to shell and correct this":
            commands.drop_to_shell()
            return _ensure_active_interface(interface_type)
        else:
            return False

    # Make sure that at least one interface of given type is UP
    while not any(interface.is_up() for interface in interfaces):
        print(f"{constants.ERROR_COLOR}All {interface_type} interfaces are DOWN.")
        bring_up = inquirer.shortcuts.checkbox(
            "Choose which interfaces to bring UP (spacebar to select, enter to confirm):",
            choices=[interface.name for interface in interfaces]
        )
        # User didn't pick any interfaces to bring up
        if len(bring_up) == 0:
            print(f"{constants.ERROR_COLOR}You didn't choose any interface(s) to bring up!")
            choice = inquirer.shortcuts.list_input(
                "How do you wish to continue?",
                choices=["Choose again", f"Give up on {interface_type} type"]
            )
            if choice == "Choose again":
                continue
            else:
                return False

        # Try to bring up all selected interfaces
        for interface_name in bring_up:
            interface = Interface(interface_name)
            commands.run_root_cmd(f"ip link set {interface.name} up")
            while not interface.is_up():
                print(f"{constants.ERROR_COLOR}Failed to bring interface {interface.name} UP!")
                choice = inquirer.shortcuts.list_input(
                    "How do you wish to continue?",
                    choices=[
                        f"Drop to shell and bring the interface {interface.name} UP manually",
                        f"Give up on interface {interface.name}"
                    ]
                )
                if choice == f"Drop to shell and bring the interface {interface.name} UP manually":
                    commands.drop_to_shell()
                    continue
                else:
                    break

    # The only way to get here is to pass the while loop condition (some interface is UP)
    return True


def _pick_wireless_interface() -> Union[Interface, Literal[False]]:
    """
    Get an active wireless interface for wireless connection, if available.
    If we can't get any active wireless interface, end with False (proceed with ethernet).
    """
    wireless_interfaces = [interface for interface in Interface.get_interfaces() if interface.type == "WIRELESS"]
    active_interfaces = [interface for interface in wireless_interfaces if interface.is_up()]

    if len(active_interfaces) == 0:
        print(F"{constants.ERROR_COLOR}There are no found active wireless interfaces!")
        choice = inquirer.shortcuts.list_input(
            "How do you want to continue?",
            choices=[
                "Try to fix the issue",
                "Drop to shell and fix the issue",
                "Proceed with Ethernet",
            ]
        )
        if choice == "Try to fix the issue":
            if not _ensure_active_interface("WIRELESS"):
                print(f"{constants.ERROR_COLOR}Failed to bring any wireless interfaces UP! Can't pick an interface.")
            # Run this even if we fail, so that we get the inquirer prompt again
            return _pick_wireless_interface()
        elif choice == "Drop to shell and fix the issue":
            commands.drop_to_shell()
            return _pick_wireless_interface()
        else:
            return False
    elif len(active_interfaces) == 1:
        return wireless_interfaces[0]
    else:
        choice = inquirer.shortcuts.list_input(
            "There are multiple wireless interfaces which are UP, "
            "choose which interface should be use to make the connection.",
            choices=[interface.name for interface in active_interfaces]
        )
        return Interface(choice)


def _iwctl_connect(interface: Interface) -> bool:
    """Try to connect to WiFi automatically using iwctl."""
    # Attempt to find some networks
    print(f"{constants.NOTE_COLOR}Scanning for networks with {interface.name}, waiting 5s...")
    commands.run_cmd(f"iwctl station {interface.name} scan")
    time.sleep(5)
    proc = commands.run_cmd(f"iwctl station {interface.name} get-networks rssi-dbms", capture_out=True)
    proc_out = proc.stdout.decode()
    network_lines = [textwrap.dedent(line) for line in proc_out.splitlines()[4:] if len(line) != 0]

    # If we didn't found any networks, fail
    if len(network_lines) == 0:
        print(f"{constants.ERROR_COLOR}No networks found. Unable to connect to Wi-Fi with iwctl automatically!")
        return False

    # Print out all found networks and store them
    print(f"{constants.INFO_COLOR}Found these networks:")
    networks = []
    for line in network_lines:
        print(line)
        # use rsplit twice since SSIDs can contain spaces
        networks.append(line.rsplit(maxsplit=2))

    # Let user pick the network to connect to (from SSIDs)
    ssid = inquirer.shortcuts.list_input(
        "Which network do you wish to connect to (you'll be prompted for the password, if it has one)",
        choices=[network[0] for network in networks]
    )

    # Try to connect (will fail on wrong password)
    print(f"{constants.NOTE_COLOR}Connecting...")
    commands.run_cmd(f"iwctl station {interface.name} connect '{ssid}'")
    time.sleep(5)

    if not check_connection():
        print(f"{constants.ERROR_COLOR}iwctl connection failed! (Most likely due to wrong network password).")
        return False

    return True


def connect_wifi() -> bool:
    """Try to connect to the internet using wifi with fallback to ethernet."""
    if not _ensure_active_interface("WIRELESS"):
        # We gave up wireless connection due to inavailable network interface, use ethernet instead
        return connect_ethernet()

    # Use TUI from NetworkManager if available, it is relatively easy to connect with this interface for the user.
    if commands.command_exists("nmtui"):
        commands.run_cmd("nmtui")
        while not check_connection():
            print(f"{constants.ERROR_COLOR}Internet connection still isn't available")
            opt = inquirer.shortcuts.list_input(
                "How do you wish to proceed?",
                choices=[
                    "Retry with nmtui",
                    "Try with iwctl",
                    "Drop to shell and connect manually",
                    "Use Ethernet instead"
                ]
            )
            if opt == "Retry with nmtui":
                commands.run_cmd("nmtui")
                continue
            elif opt == "Try with iwctl":
                break
            elif opt == "Drop to shell and connect manually":
                commands.drop_to_shell()
                continue
            elif opt == "Use Ethernet instead":
                return connect_ethernet()
        else:
            # If we didn't break (to continue with iwctl), we have connected successfully
            return True

    # If nmtui failed, try with iwctl
    if commands.command_exists("iwctl"):
        print(
            f"{constants.WARN_COLOR}Failed to run nmtui. (NetworkManager likely isn't installed, "
            "this is to be expected if running from live ISO. Using iwctl instead."
        )

        active_interface = _pick_wireless_interface()
        if active_interface is False:
            # We gave up wireless connection due to inavailable network interface, use ethernet instead
            return connect_ethernet()

        _iwctl_connect(active_interface)
        while not connect_ethernet():
            print(f"{constants.ERROR_COLOR}Internet connection still not available!")
            choice = inquirer.shortcuts.list_input(
                "How do you wish to continue?",
                choices=[
                    "Drop to shell and connect manually",
                    "Proceed with Ethernet",
                    "Retry iwctl autoconnection",
                    "Drop to interactive iwctl"
                ]
                )
            if choice == "Drop to shell and connect manually":
                commands.drop_to_shell()
                continue
            elif choice == "Proceed with Ethernet":
                return connect_ethernet()
            elif choice == "Retry iwctl autoconnection":
                _iwctl_connect(active_interface)
                continue
            else:  # interactive iwctl
                print(
                    f"{constants.INFO_COLOR}After you're done, use {constants.CMD_COLOR}exit "
                    f"{constants.INFO_COLOR}to go back, to display iwctl help, use {constants.CMD_COLOR}help"
                )
                commands.run_cmd("iwctl")
                continue

        # The only way to get here is when the while condition passes (we are connected)
        return True

    # We will only get here if nmtui wasn't installed/failed and iwctl wasn't installed
    print(f"{constants.ERROR_COLOR}Neither nmtui nor iwctl commands are available. Can't handle wifi connection!")
    while True:
        choice = inquirer.shortcuts.list_input(
            "How do you wish to continue?",
            choices=["Drop to shell and connect manually", "Proceed with Ethernet"]
        )
        if choice == "Drop to shell and connect manually":
            commands.drop_to_shell()
            if check_connection():
                return True
            else:
                print(f"{constants.ERROR_COLOR}Internet connection still isn't available!")
        elif choice == "Proceed with Ethernet":
            return connect_ethernet()


def connect_internet() -> bool:
    if not check_connection():
        print(f"{constants.WARN_COLOR}Device is currently not connected to the internet, connecting!")

        # wireless adapters are often soft-blocked with RF-KILL, unblock everything first
        unblock_rfkill()

        connect_opt = inquirer.shortcuts.list_input(
            "How do you wish to connect to internet?",
            choices=["Wi-Fi", "Ethernet"]
        )
        if connect_opt == "Wi-Fi":
            result = connect_wifi()
        else:
            result = connect_ethernet()
    else:
        print(f"{constants.NOTE_COLOR}Internet connection already set up.")
        return True

    if result is True:
        print(f"{constants.INFO_COLOR}Internet connection successful!")
        return True
    else:
        print(f"{constants.ERROR_COLOR}Internet connection wasn't established!")
        return False
