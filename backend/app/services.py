"""Business logic + validation. Mirrors contactService.js 1:1."""
import re

from . import models
from .errors import AppError
from .repositories import ContactRepository

INT_PREFIX_RE = re.compile(r"^\s*([+-]?\d+)")


def _parse_int_prefix(value, default: int) -> int:
    match = INT_PREFIX_RE.match(str(value) if value is not None else "")
    if not match:
        return default
    try:
        return int(match.group(1))
    except ValueError:
        return default


class ContactService:
    def __init__(self, repository: ContactRepository | None = None):
        self.repository = repository or ContactRepository()

    def get_paged(self, page_number, page_size, search_term="", sort_by=None, sort_order=None) -> dict:
        page, size = models.normalize_paging(page_number, page_size)
        column, order = models.normalize_sort(sort_by, sort_order)
        result = self.repository.get_paged(page, size, search_term or "", column, order)
        return models.to_paged(result["items"], result["totalCount"], page, size)

    def get_suggestions(self, term, limit) -> list:
        clean = (str(term) if term is not None else "").strip()[:255]
        count = min(20, max(1, _parse_int_prefix(limit, 8)))
        if not clean:
            return []
        return self.repository.get_suggestions(clean, count)

    def export_contacts(self) -> list:
        return self.repository.get_all()

    def import_contacts(self, items) -> dict:
        if not isinstance(items, list):
            raise AppError(400, "Import body must be a JSON array of contacts.")
        if len(items) > 5000:
            raise AppError(400, "Import is limited to 5000 contacts at a time.")
        existing_phones = self.repository.get_phone_set()
        imported = 0
        skipped = 0
        errors = []
        for index, raw in enumerate(items):
            if not isinstance(raw, dict):
                errors.append(f"Row {index + 1}: must be a JSON object.")
                if len(errors) > 50:
                    break
                continue
            check_errors, value = models.validate_contact(raw)
            if check_errors:
                errors.append(f"Row {index + 1}: {' '.join(check_errors)}")
                if len(errors) > 50:
                    break
                continue
            if value["phoneNumber"] in existing_phones:
                skipped += 1  # PhoneNumber is UNIQUE: never duplicate it
                continue
            try:
                self.repository.create(value)
                existing_phones.add(value["phoneNumber"])
                imported += 1
            except AppError as exc:
                if exc.status_code == 409:
                    skipped += 1
                else:
                    errors.append(f"Row {index + 1}: {exc.message}")
                    if len(errors) > 50:
                        break
        return {"imported": imported, "skipped": skipped, "errors": errors}

    def get_by_id(self, contact_id) -> dict | None:
        parsed = models.validate_id(contact_id)
        if not parsed:
            raise AppError(400, "Invalid contact id.")
        return self.repository.get_by_id(parsed)

    def create(self, data: dict) -> dict:
        errors, value = models.validate_contact(data or {})
        if errors:
            raise AppError(400, " ".join(errors))
        return self.repository.create(value)

    def update(self, contact_id, data: dict) -> dict | None:
        parsed = models.validate_id(contact_id)
        if not parsed:
            raise AppError(400, "Invalid contact id.")
        errors, value = models.validate_contact(data or {})
        if errors:
            raise AppError(400, " ".join(errors))
        existing = self.repository.get_by_id(parsed)
        if not existing:
            return None
        return self.repository.update(parsed, value)

    def remove(self, contact_id) -> bool:
        parsed = models.validate_id(contact_id)
        if not parsed:
            raise AppError(400, "Invalid contact id.")
        existing = self.repository.get_by_id(parsed)
        if not existing:
            return False
        self.repository.remove(parsed)
        return True
