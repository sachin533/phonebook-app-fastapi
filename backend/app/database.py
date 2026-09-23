"""SQL Server access via pyodbc (ODBC Driver 17, same as the Node Tedious path).

One short-lived connection per request; ODBC connection pooling keeps this
cheap. No ORM, no query builder — stored procedures only.
"""
import pyodbc

from .config import settings

pyodbc.pooling = True


def connection_string() -> str:
    server = settings.db_server
    # "host,port" form; keep named instances ("host\\SQLEXPRESS") untouched.
    if settings.db_port and "," not in server and "\\" not in server:
        server = f"{server},{settings.db_port}"
    parts = [
        "DRIVER={ODBC Driver 17 for SQL Server}",
        f"SERVER={server}",
        f"DATABASE={settings.db_database}",
        f"UID={settings.db_user}",
        f"PWD={settings.db_password}",
        "Encrypt=yes" if settings.db_encrypt else "Encrypt=no",
    ]
    if settings.db_trust_server_certificate:
        parts.append("TrustServerCertificate=yes")
    return ";".join(parts) + ";"


def get_connection() -> pyodbc.Connection:
    return pyodbc.connect(connection_string(), timeout=10)
