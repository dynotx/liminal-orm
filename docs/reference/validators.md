## Benchling Base Validator: [class](https://github.com/dynotx/liminal-orm/blob/main/liminal/validation/__init__.py)

Below is an example of a Benchling Validator defined in Liminal for validating the cook temp of a pizza.

```python
from liminal.validation import BenchlingValidator, BenchlingValidatorReport, BenchlingReportLevel
from liminal.orm.base_model import BaseModel

class CookTempValidator(BenchlingValidator):
    """Validates that a field value is a valid enum value for a Benchling entity"""

    def validate(self, entity: type[BaseModel]) -> BenchlingValidatorReport:
        valid = True
        message = None
        if entity.cook_time is not None and entity.cook_temp is None:
            valid = False
            message = "Cook temp is required if cook time is set"
        if entity.cook_time is None and entity.cook_temp is not None:
            valid = False
            message = "Cook time is required if cook temp is set"
        return self.create_report(valid, BenchlingReportLevel.MED, entity, message)
```

A `validate(entity)` function is required to be defined in the BenchlingValidator subclass. This function should contain the logic to validate the entity. The function should return a `BenchlingValidatorReport` object, which can be easily created using the `create_report` method.
