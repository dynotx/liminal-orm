import random
import re
import string
from typing import Any

import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from liminal.connection.benchling_service import BenchlingService


def generate_random_id(length: int = 8) -> str:
    """Generate a pseudo-random ID with only lowercase letters."""
    return "".join(random.choices(string.ascii_lowercase, k=length))


def to_pascal_case(input_string: str) -> str:
    """
    Convert a string to PascalCase. Filters out any non-alphanumeric characters.
    """
    words = re.split(r"[ /_\-]", input_string)
    # Then remove any non-alphanumeric characters and capitalize each word
    return "".join(re.sub(r"[^a-zA-Z0-9]", "", word).capitalize() for word in words)


def to_snake_case(input_string: str) -> str:
    """
    Convert a string to snake_case. Filters out any non-alphanumeric characters.
    """
    words = re.split(r"[ /_\-]", input_string)
    words = [word for word in words if word]
    return "_".join(re.sub(r"[^a-zA-Z0-9]", "", word).lower() for word in words)


def to_string_val(input_val: Any) -> str:
    """
    Convert a value to a string.
    """
    if isinstance(input_val, list) or isinstance(input_val, set):
        return f'[{", ".join(input_val)}]'
    return str(input_val)


def is_valid_wh_name(wh_name: str) -> bool:
    """
    This checks if the given warehouse name is valid for a field or entity schema.
    It must be all lowercase, and have alphanumeric characters or underscores.
    """
    valid = all(c.islower() or c.isdigit() or c == "_" for c in wh_name)
    if not valid:
        raise ValueError(
            f"Invalid warehouse name '{wh_name}'. It should only contain lowercase letters, digits, or underscores."
        )
    return valid


def is_valid_prefix(prefix: str) -> bool:
    """
    This checks if the given prefix is valid for an entity schema.
    It must be contain only alphanumeric characters and underscores, be less than 33 characters, and end with an alphabetic character.
    """
    valid = (
        all(c.isalnum() or c == "_" or c == "-" for c in prefix)
        and len(prefix) <= 32
        and not prefix[-1].isdigit()
        and " " not in prefix
    )
    if not valid:
        raise ValueError(
            f"Invalid prefix '{prefix}'. The prefix should only contain alphabetic characters or underscores, not end end in a digit, and not contain whitespace."
        )
    return valid


@retry(
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(ValueError),
    reraise=True,
    wait=wait_fixed(2),
)
def await_queued_response(
    status_url: str, benchling_sdk: BenchlingService
) -> dict[str, Any]:
    with requests.Session() as session:
        response = session.get(
            f"https://{benchling_sdk.benchling_tenant}.benchling.com{status_url}",
            headers=benchling_sdk.custom_post_headers,
            cookies=benchling_sdk.custom_post_cookies,
        )
    response_json = response.json()
    if not response.ok:
        raise ValueError("Failed request: ", response_json)
    if response_json["status"] == "SUCCESS":
        return response_json
    else:
        raise ValueError("Failed request: ", response_json)
