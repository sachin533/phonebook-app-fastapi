#!/bin/bash
# Applies sql/phonebook.sql (contains GO batch separators, so sqlcmd is required).
set -u

SQLCMD="/opt/mssql-tools18/bin/sqlcmd -S sqlserver,1433 -U sa -P $MSSQL_SA_PASSWORD -C"
READY=0

echo "Waiting for SQL Server..."
for i in $(seq 1 60); do
    if $SQLCMD -Q "SELECT 1" > /dev/null 2>&1; then
        echo "SQL Server is ready."
        READY=1
        break
    fi
    sleep 2
done

if [ "$READY" -ne 1 ]; then
    echo "ERROR: SQL Server did not become ready in time." >&2
    exit 1
fi

echo "Running phonebook.sql..."
$SQLCMD -i /sql/phonebook.sql
echo "Database initialization completed."
