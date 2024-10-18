from pydantic import BaseModel, ConfigDict

from liminal.base.base_operation import BaseOperation


class CompareOperation(BaseModel):
    op: BaseOperation
    reverse_op: BaseOperation

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __lt__(self, other: "CompareOperation") -> bool:
        return self.op.order < other.op.order
