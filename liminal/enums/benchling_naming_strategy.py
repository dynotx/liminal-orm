from __future__ import annotations

from liminal.base.str_enum import StrEnum


class BenchlingNamingStrategy(StrEnum):
    NEW_IDS = "NEW_IDS"  # Generate new registry IDs
    IDS_FROM_NAMES = "IDS_FROM_NAMES"  # Generate registry IDs based on entity names
    REPLACE_NAME_WITH_ID = (
        "DELETE_NAMES"  # Generate new registry IDs and replace name with registry ID
    )
    RENAME_WITH_TEMPLATE_WITH_ALIAS = "SET_FROM_NAME_PARTS"  # Generate new registry IDs, rename according to name template, and keep old name as alias
    REPLACE_NAMES_WITH_TEMPLATE = "REPLACE_NAMES_FROM_PARTS"  # Generate new registry IDs, and replace name according to name template

    @classmethod
    def is_template_based(cls, strategy: BenchlingNamingStrategy) -> bool:
        return strategy in [
            cls.RENAME_WITH_TEMPLATE_WITH_ALIAS,
            cls.REPLACE_NAMES_WITH_TEMPLATE,
        ]

    @classmethod
    def is_valid_set(
        cls, strategies: set[BenchlingNamingStrategy], name_template: bool
    ) -> bool:
        if (
            any(cls.is_template_based(strategy) for strategy in strategies)
            and not name_template
        ):
            return False
        return True
