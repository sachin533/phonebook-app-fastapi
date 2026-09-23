"""Domain model / DTO mapping plus validation. Mirrors server/models/contact.js
and the validation helpers of the Node backend 1:1 (same messages)."""
import math
import re
from datetime import datetime

PHONE_RE = re.compile(r"^[0-9+()\-\s.]+$")
EMAIL_RE = re.compile(r"^\S+@\S+\.\S+$")
INT_PREFIX_RE = re.compile(r"^\s*([+-]?\d+)")

SORT_COLUMNS = {
    "name": "Name",
    "phonenumber": "PhoneNumber",
    "email": "Email",
    "createdat": "CreatedAt",
}


def format_dt(value):
    """DATETIME -> 'YYYY-MM-DDTHH:mm:ss.sssZ', matching the Node JSON shape."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return f"{value.strftime('%Y-%m-%dT%H:%M:%S')}.{value.microsecond // 1000:03d}Z"
    return str(value)


def to_contact(row) -> dict | None:
    if row is None:
        return None
    return {
        "id": row.Id,
        "name": row.Name,
        "phoneNumber": row.PhoneNumber,
        "email": row.Email,
        "address": row.Address,
        "createdAt": format_dt(row.CreatedAt),
    }


def to_paged(items: list, total_count: int, page: int, size: int) -> dict:
    return {
        "items": items,
        "totalCount": total_count,
        "currentPage": page,
        "pageSize": size,
        "totalPages": math.ceil(total_count / size) if size else 0,
    }


def _as_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def validate_contact(data: dict) -> tuple[list, dict]:
    data = data or {}
    name = _as_text(data.get("name"))
    phone_number = _as_text(data.get("phoneNumber"))
    email = _as_text(data.get("email"))
    address = _as_text(data.get("address"))

    errors = []
    if not name:
        errors.append("Name is required.")
    if len(name) > 255:
        errors.append("Name must be 255 characters or fewer.")
    if not phone_number:
        errors.append("Phone number is required.")
    if len(phone_number) > 50:
        errors.append("Phone number must be 50 characters or fewer.")
    if phone_number and not PHONE_RE.match(phone_number):
        errors.append("Phone number contains invalid characters.")
    if email and (len(email) > 255 or not EMAIL_RE.match(email)):
        errors.append("Enter a valid email address.")

    return errors, {
        "name": name,
        "phoneNumber": phone_number,
        "email": email or None,
        "address": address or None,
    }


def validate_id(value) -> int | None:
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError, AttributeError):
        return None
    if not math.isfinite(parsed) or not parsed.is_integer() or parsed <= 0:
        return None
    return int(parsed)


def _parse_int_prefix(value, default: int) -> int:
    match = INT_PREFIX_RE.match(str(value) if value is not None else "")
    if not match:
        return default
    try:
        return int(match.group(1))
    except ValueError:
        return default


def normalize_paging(page_number, page_size) -> tuple[int, int]:
    page = max(1, _parse_int_prefix(page_number, 1))
    size = min(100, max(1, _parse_int_prefix(page_size, 10)))
    return page, size


def normalize_sort(sort_by, sort_order) -> tuple[str, str]:
    column = SORT_COLUMNS.get(_as_text(sort_by).lower(), "Name")
    order = "DESC" if _as_text(sort_order).upper() == "DESC" else "ASC"
    return column, order
