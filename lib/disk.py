from pathlib import Path
from typing import Optional

from lib import constants, commands, questions


class Partition:
    def __init__(self, path: Path, mountpoint: Optional[Path] = None, is_swap: bool = False, is_efi: bool = False):
        self.path = path
        self.mountpoint = mountpoint
        self.is_swap = is_swap
        self.is_efi = is_efi

    def __repr__(self) -> str:
        part_repr = f"<Partition {self.path}: mountpoint={self.mountpoint}"
        if self.is_swap:
            part_repr += " swap=True"
        if self.is_efi:
            part_repr += " EFI=True"
        part_repr += ">"
        return part_repr


def get_partition_scheme() -> list[Partition]:
    """
    Obtain all mountpoints with partitions.
    Output will be stored in a dictionary
    """
    part_scheme = []
    root_partition = questions.path(
        f"Enter {constants.CMD_COLOR}/{constants.RESET_COLOR} partition path (usually /dev/sdXY)",
    )
    part_scheme.append(Partition(root_partition, mountpoint=Path("/")))

    if constants.IS_EFI:
        efi_partition = questions.path("Enter the partition path for the EFI partition.")
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
            mountpoint = questions.path("Enter the mountpoint (on new machine): ", exists=False)
            partition = questions.path("Enter the partition path (usually /dev/sdXY): ")

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

    print(f"{constants.INFO_COLOR}Your current partition table scheme:\n{part_scheme}")
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
