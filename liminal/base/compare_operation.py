from pydantic import BaseModel, ConfigDict

from liminal.base.base_operation import BaseOperation


class CompareOperation(BaseModel):
    op: BaseOperation
    reverse_op: BaseOperation
    # Overrides op.order when an operation must run at a different point than its type's default.
    order: int | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def sort_order(self) -> int:
        return self.op.order if self.order is None else self.order

    def __lt__(self, other: "CompareOperation") -> bool:
        return self.sort_order < other.sort_order
