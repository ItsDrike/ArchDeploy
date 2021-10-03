#!/usr/bin/env python3
from pathlib import Path

from lib import constants, internet, commands, disk, questions


def main():
    commands.run_cmd("clear", enable_debug=False)
    internet.connect_internet()
    commands.run_root_cmd("timedatectl set-ntp true")

    disk.partition_disk()
    partition_scheme = disk.get_partition_scheme()
    disk.format_partitions(partition_scheme)
    disk.mount_partitions(Path("/mnt"), partition_scheme)

    print(f"{constants.NOTE_COLOR}Running pacstrap...")
    commands.run_root_cmd("pacstrap /mnt base linux linux-firmware python")
    print(f"{constants.NOTE_COLOR}Generating fstab...")
    commands.run_root_cmd("genfstab -U /mnt >> /mnt/etc/fstab")

    if questions.confirm("Do you wish to drop to shell before chrooting?"):
        commands.drop_to_shell()

    cwd = Path.cwd()
    commands.run_root_cmd(f"cp -r '{str(cwd)}' /mnt/opt/ArchDeploy")
    commands.run_root_cmd("arch-chroot /mnt /opt/ArchDeploy/post-chroot.py")


if __name__ == "__main__":
    main()
