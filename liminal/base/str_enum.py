from enum import Enum


class StrEnum(str, Enum):
    def __repr__(self) -> str:
        """
        Returns the string representation of the enum. ex: 'StrEnum.VALUE'
        """
        return self.__str__()
