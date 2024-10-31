## Dropdown Schema: [class](https://github.com/dynotx/liminal-orm/blob/main/liminal/base/base_dropdown.py)

Below is an example of a dropdown schema defined in code. The `__benchling_name__` property is used to define the name of the dropdown in Benchling, while the `__allowed_values__` property is used to define the values of the dropdown.

```python
# Example dropdown definition
from liminal.base.base_dropdown import BaseDropdown


class Toppings(BaseDropdown):
    __benchling_name__ = "Toppings"
    __allowed_values__ = ["Pepperoni", "Mushroom", "Onion", "Sausage", "Bacon"]
```

### Parameters

**benchling_name: str**

> The name of the dropdown in Benchling. There can be no duplicate dropdown names in Benchling.

**allowed_values: list[str]**

> The list of values for the dropdown. Order matters and reflects the order of the dropdown in Benchling. Values must be unique.
