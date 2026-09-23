"""Contact routes. Same paths, params, shapes and status codes as Express."""
from typing import Optional

from fastapi import APIRouter, Body, Query, Response

from ..services import ContactService

router = APIRouter()
_service = ContactService()


@router.get("", include_in_schema=False)
@router.get("/")
def list_contacts(
    pageNumber: Optional[str] = Query(default=None),
    pageSize: Optional[str] = Query(default=None),
    searchTerm: Optional[str] = Query(default=""),
    sortBy: Optional[str] = Query(default=None),
    sortOrder: Optional[str] = Query(default=None),
):
    return _service.get_paged(pageNumber, pageSize, searchTerm or "", sortBy, sortOrder)


@router.get("/suggestions")
def suggestions(
    term: Optional[str] = Query(default=None),
    limit: Optional[str] = Query(default=None),
):
    return _service.get_suggestions(term, limit)


@router.get("/{contact_id}")
def get_by_id(contact_id: str):
    contact = _service.get_by_id(contact_id)
    if not contact:
        return Response(
            content='{"message":"Contact not found."}',
            status_code=404,
            media_type="application/json",
        )
    return contact


@router.post("", status_code=201, include_in_schema=False)
@router.post("/", status_code=201)
def create_contact(payload: dict | None = Body(default=None)):
    return _service.create(payload or {})


@router.put("/{contact_id}")
def update_contact(contact_id: str, payload: dict | None = Body(default=None)):
    contact = _service.update(contact_id, payload or {})
    if not contact:
        return Response(
            content='{"message":"Contact not found."}',
            status_code=404,
            media_type="application/json",
        )
    return contact


@router.delete("/{contact_id}")
def remove_contact(contact_id: str):
    deleted = _service.remove(contact_id)
    if not deleted:
        return Response(
            content='{"message":"Contact not found."}',
            status_code=404,
            media_type="application/json",
        )
    return {"message": "Contact deleted successfully."}
