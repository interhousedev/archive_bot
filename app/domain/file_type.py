from enum import Enum


class FileType(str, Enum):
    """Types of files."""

    IMAGE="IMAGE"
    VIDEO="VIDEO"
    FILE="FILE"
