from pathlib import Path

import pytest

import liminal.external as b
from liminal.base.base_operation import BaseOperation
from liminal.migrate.revision import Revision


@pytest.mark.parametrize(
    "operation",
    [
        b.CreateDropdownOption("Primer End", "5' UTR", 0),
        b.UpdateDropdownName("Donor's Sex", "Donor Sex"),
        b.CreateDropdown("Owner's Team", ["O'Brien Lab", 'Size 10"']),
    ],
)
def test_revision_file_string_round_trips_quotes(operation: BaseOperation) -> None:
    back = eval(operation.revision_file_string(), {"b": b})
    assert repr(back) == repr(operation)


def test_revision_file_with_apostrophes_parses_back(tmp_path: Path) -> None:
    operations: list[BaseOperation] = [
        b.CreateDropdown("Primer End", ["5' UTR", "3' UTR"]),
        b.CreateDropdownOption("Primer End", "5' ITR", 2),
    ]
    revision = Revision(
        id=Revision.new_id(),
        description="apostrophes in dropdown names",
        down_revision_id=None,
        upgrade_operations=operations,
        downgrade_operations=[],
    )
    path = revision.write_revision_file(tmp_path)
    parsed = Revision.parse_from_file(path)
    assert [repr(o) for o in parsed.upgrade_operations] == [repr(o) for o in operations]
