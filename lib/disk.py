from pathlib import Path
from typing import Optional

from lib import constants, commands, questions


class Partition:
    def __init__(self, path: Path, mountpoint: Optional[Path] = None, is_swap: bool = False, is_efi: bool = False):
        self.path = path
        self.mountpoint = mountpoint
        self.is_swap = is_swap
        self.is_efi = is_efi

        if self.mountpoint is not None and self.is_swap:
            raise ValueError("Swap partitions can't have a hard-coded mountpoint")
        if self.mountpoint == "/" and self.is_efi:
            raise ValueError("EFI partition can't have a mountpoint of '/' (root)")

    def as_tuple(self) -> tuple:
        """Get the partition in a form of a tuple."""
        if self.mountpoint == "/":
            return (self.path, "ROOT (/)")
        elif self.is_efi:
            return (self.path, f"EFI ({self.mountpoint})")
        elif self.is_swap:
            return (self.path, "SWAP (-)")
        else:
            return (self.path, self.mountpoint)

    def __str__(self) -> str:
        part_tuple = self.as_tuple()
        return f"{part_tuple[0]}: {part_tuple[1]}"

    def __repr__(self) -> str:
        return f"<Partition {str(self)}>"

    @staticmethod
    def print_partition_table(partitions: list["Partition"], indent: int = 0):
        """Nicely print a table of multiple partitions and their details."""
        table_lines = [str(partition) for partition in partitions]
        for line in table_lines:
            print(" " * indent + line)


def get_partition_scheme() -> list[Partition]:
    """
    Obtain all mountpoints with partitions.
    Output will be stored in a dictionary
    """
    if questions.confirm("Do you wish to drop to shell before configuring partition scheme?"):
        commands.drop_to_shell()

    part_scheme = []
    root_partition = questions.path(
        f"Enter {constants.CMD_COLOR}/{constants.RESET_COLOR} partition path (usually /dev/sdXY)",
    )
    part_scheme.append(Partition(root_partition, mountpoint=Path("/")))

    if constants.IS_EFI:
        efi_partition = questions.path("Enter the partition path for the EFI partition (usually /dev/sdXY)")
        efi_mountpoint = questions.choice(
            "Which mountpoint do you want to use for the EFI partition?",
            choices=[Path("/boot"), Path("/efi"), "Other"]
        )
        if efi_mountpoint == "Other":
            efi_mountpoint = questions.path("Enter the EFI mountpoint path: ", exists=False)
        part_scheme.append(Partition(efi_partition, mountpoint=efi_mountpoint))

    if questions.confirm("Do you want swap partition?"):
        swap_partition = questions.path("Enter swap partition path (usually /dev/sdXY): ")
        part_scheme.append(Partition(swap_partition, is_swap=True))

    while True:
        if questions.confirm("Do you want to define some other mountpoint?"):
            partition = questions.path("Enter the partition path (usually /dev/sdXY): ")
            mountpoint = questions.path("Enter the mountpoint (on new machine): ", exists=False)

            for existing_partition in part_scheme:
                if existing_partition.path == partition:
                    print(
                        f"{constants.WARN_COLOR}Redefining old mountpotint"
                        f"(previously: {existing_partition.mountpoint})"
                    )
                    existing_partition.mountpoint = mountpoint
                    break
            else:
                part_scheme.append(Partition(partition, mountpoint=mountpoint))
        else:
            break

    print(f"{constants.INFO_COLOR}Your current partition table scheme:")
    Partition.print_partition_table(part_scheme, indent=4)

    if questions.confirm("Does this look correct?"):
        return part_scheme
    else:
        print(f"{constants.INFO_COLOR}Re-running mountpoint obtainer")
        return get_partition_scheme()


def partition_disk():
    """Make the necessary partitions """
    # TODO: Automate partitioning
    print(f"{constants.INFO_COLOR}Please partition the disks manually")
    commands.drop_to_shell()


def format_partitions(partitions: list[Partition]):
    """Properly format given partitions accordingly to their mountpoint."""
    print(
        f"{constants.INFO_COLOR}Running automated partition formatter. "
        "This will apply EXT4 formatting to each partition apart from SWAP "
        "and EFI (which will be FAT32)."
    )
    print(f"{constants.WARN_COLOR}If you want to use a different formatting "
          "or if your partitions are already pre-formatted, do not proceed with the "
          "automated partition formatter!"
          )

    if questions.confirm(
        "Do you wish to drop to shell and format your partitions manually? (will skip automated formatter)"
    ):
        commands.drop_to_shell()


def mount_partitions(mountpoint: Path, partitions: list[Partition]):
    pass
