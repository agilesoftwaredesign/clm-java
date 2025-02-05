import re
from abc import ABC, abstractmethod
from pathlib import Path

NOTEBOOK_REGEX = re.compile(
    r"^(nb|lecture|topic|ws|workshop|project)_(.*)\.(py|cpp|ru|md)$"
)

# Constant for commonly used file kinds.
IGNORED_LABEL = "Ignored"
DATA_FILE_LABEL = "DataFile"
FOLDER_LABEL = "Folder"
NOTEBOOK_LABEL = "Notebook"
EXAMPLE_SOLUTION_LABEL = "ExampleSolution"
EXAMPLE_STARTER_KIT_LABEL = "ExampleStarterKit"


class DirectoryKind(ABC):
    """A classifier for files and directories.

    Assigns a content label to files in this directory. The label is used
    to determine which document type to instantiate for this file."""

    def __repr__(self):
        # return f'{self.__class__.__name__}({self.path})'
        return f"{self.__class__.__name__}()"

    def __eq__(self, other):
        # Check actual types, not subclasses.
        # pylint: disable=unidiomatic-typecheck
        return type(other) is type(self)

    @abstractmethod
    def label_for(self, file_or_dir: Path) -> str:
        """Classify a file or directory."""
        ...


class IgnoredDirectory(DirectoryKind):
    """A directory that is ignored.

    Both files and subdirectories in this directory are ignored.
    """

    def label_for(self, file_or_dir: Path) -> str:
        return IGNORED_LABEL


class GeneralDirectory(DirectoryKind):
    """A directory that has no special properties.

    Files in this directory are copied to the output directory without any
    processing.

    Subdirectories are processed recursively to discover more course materials.
    """

    def label_for(self, file_or_dir: Path) -> str:
        if file_or_dir.is_file():
            return DATA_FILE_LABEL
        else:
            return IGNORED_LABEL
