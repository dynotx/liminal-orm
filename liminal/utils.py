import json
import random
import re
import string
from typing import Any
from urllib.parse import quote

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    stop_after_delay,
    wait_fixed,
)

from liminal.connection.benchling_service import BenchlingService

EARLY_ACCESS_HEADER = {"EARLY-ACCESS": "true"}

MAX_PAGE_SIZE = 100

# Larger bursts of parallel requests get rate limited by Benchling and stall on retry backoff.
MAX_CONCURRENT_REQUESTS = 8

TASK_POLL_INTERVAL_SECONDS = 1
TASK_TIMEOUT_SECONDS = 300
TASK_FAILED_STATUSES = {"FAILED", "FAILURE", "CANCELLED"}


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


def list_all_items_v3(
    benchling_service: BenchlingService,
    url: str,
    include_archived: bool = False,
    page_size: int | None = MAX_PAGE_SIZE,
) -> list[dict[str, Any]]:
    """Fetch every item from a v3 list endpoint, following nextToken pagination."""
    query_params = [f"archived.anyOf={'true,false' if include_archived else 'false'}"]
    if page_size:
        query_params.append(f"pageSize={page_size}")
    base_url = f"{url}?{'&'.join(query_params)}"
    items: list[dict[str, Any]] = []
    next_token: str | None = None
    while True:
        page_url = base_url
        if next_token:
            page_url += f"&nextToken={quote(next_token)}"
        response = benchling_service.api.get_response(
            url=page_url,
            additional_headers=EARLY_ACCESS_HEADER,
        )
        parsed_response = response.parsed
        if parsed_response is None:
            raise ValueError(f"No response body returned for {url}.")
        if isinstance(parsed_response, list):
            return items + parsed_response
        items.extend(parsed_response.get("items", []))
        next_token = parsed_response.get("nextToken")
        if not next_token:
            return items


class TaskNotFinishedError(Exception):
    """Raised while a v3 async task is still running, so tenacity polls it again."""


@retry(
    stop=stop_after_delay(TASK_TIMEOUT_SECONDS),
    retry=retry_if_exception_type(TaskNotFinishedError),
    reraise=True,
    wait=wait_fixed(TASK_POLL_INTERVAL_SECONDS),
)
def await_task_v3(
    benchling_service: BenchlingService, polling_uri: str
) -> dict[str, Any]:
    """Poll a v3 async task until it completes, and return the final task response.
    Each poll is a request against the rate limit, so the timeout bounds how many are made."""
    response = benchling_service.api.get_response(
        url=polling_uri.split(".benchling.com/", 1)[-1],
        additional_headers=EARLY_ACCESS_HEADER,
    )
    if not (200 <= response.status_code < 300):
        raise Exception(f"Failed to poll task {polling_uri}:", response.content)
    task = json.loads(response.content)
    status = task.get("status")
    if status == "COMPLETED":
        return task
    if status in TASK_FAILED_STATUSES:
        raise Exception(f"Task {polling_uri} failed:", task)
    raise TaskNotFinishedError(
        f"Task {polling_uri} did not complete within {TASK_TIMEOUT_SECONDS} seconds. Last response: {task}"
    )
