"""Data access — stored procedures only. Mirrors contactRepository.js.

pyodbc has no OUTPUT-parameter binding for SQL Server procedures, so procs
with OUTPUT params are wrapped in a batch that SELECTs the value back:
first result set = rows, second = the OUTPUT value (via cursor.nextset()).
"""
import pyodbc

from . import models
from .database import get_connection
from .errors import AppError


def _is_unique_violation(exc: Exception) -> bool:
    args = getattr(exc, "args", []) or []
    state = str(args[0]) if args else ""
    text = str(exc)
    return state == "23000" or "2627" in text or "2601" in text


class ContactRepository:
    def get_paged(self, page: int, size: int, search_term: str = "",
                  sort_by: str = "Name", sort_order: str = "ASC") -> dict:
        term = (search_term or "").strip() or None
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SET NOCOUNT ON;"
                "DECLARE @TotalCount INT;"
                "EXEC dbo.sp_GetContactsPaged"
                " @PageNumber=?, @PageSize=?, @SearchTerm=?,"
                " @SortBy=?, @SortOrder=?, @TotalCount=@TotalCount OUTPUT;"
                "SELECT @TotalCount AS TotalCount;",
                page, size, term, sort_by, sort_order,
            )
            rows = cursor.fetchall()
            total = 0
            if cursor.nextset():
                row = cursor.fetchone()
                if row is not None:
                    total = row[0] or 0
        return {"items": [models.to_contact(r) for r in rows], "totalCount": total}

    def get_suggestions(self, term: str, limit: int = 8) -> list:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "EXEC dbo.sp_GetContactSuggestions @Term=?, @Limit=?;",
                term, limit,
            )
            return [row[0] for row in cursor.fetchall()]

    def get_all(self) -> list:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("EXEC dbo.sp_GetAllContacts;")
            return [models.to_contact(r) for r in cursor.fetchall()]

    def get_phone_set(self) -> set:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT PhoneNumber FROM dbo.Contacts;")
            return {row[0] for row in cursor.fetchall()}

    def get_by_id(self, contact_id: int) -> dict | None:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("EXEC dbo.sp_GetContactById @Id=?;", contact_id)
            row = cursor.fetchone()
            return models.to_contact(row) if row else None

    def create(self, contact: dict) -> dict:
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SET NOCOUNT ON;"
                    "DECLARE @NewId INT;"
                    "EXEC dbo.sp_InsertContact"
                    " @Name=?, @PhoneNumber=?, @Email=?, @Address=?,"
                    " @NewId=@NewId OUTPUT;"
                    "SELECT @NewId AS NewId;",
                    contact["name"], contact["phoneNumber"],
                    contact["email"], contact["address"],
                )
                # The SELECT is the first result set (NOCOUNT suppresses
                # the EXEC's empty set); fall back to later sets just in case.
                row = cursor.fetchone()
                if row is None and cursor.nextset():
                    row = cursor.fetchone()
                new_id = row[0]
                conn.commit()
        except pyodbc.Error as exc:
            if _is_unique_violation(exc):
                raise AppError(409, "Phone number already exists.")
            raise
        return self.get_by_id(new_id)

    def update(self, contact_id: int, contact: dict) -> dict | None:
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "EXEC dbo.sp_UpdateContact"
                    " @Id=?, @Name=?, @PhoneNumber=?, @Email=?, @Address=?;",
                    contact_id, contact["name"], contact["phoneNumber"],
                    contact["email"], contact["address"],
                )
                conn.commit()
        except pyodbc.Error as exc:
            if _is_unique_violation(exc):
                raise AppError(409, "Phone number already exists.")
            raise
        # Procedures use SET NOCOUNT ON, so existence is checked in the
        # service layer; re-read the updated row here.
        return self.get_by_id(contact_id)

    def remove(self, contact_id: int) -> None:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("EXEC dbo.sp_DeleteContact @Id=?;", contact_id)
            conn.commit()
