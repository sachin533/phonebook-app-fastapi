# Database initializer: runs the existing sql/phonebook.sql with sqlcmd.
# Reuses the SQL Server image itself, which already ships sqlcmd at
# /opt/mssql-tools18/bin/sqlcmd — no extra image pull, always compatible.
FROM mcr.microsoft.com/mssql/server:2022-latest

WORKDIR /sql

COPY sql/phonebook.sql /sql/phonebook.sql

COPY docker/sql/init-db.sh /init-db.sh

# Be robust to Windows CRLF checkouts inside the Linux container.
# NOTE: this image runs as USER mssql, so root is needed for the conversion.
USER root
RUN sed -i 's/\r$//' /init-db.sh && chmod +x /init-db.sh
USER mssql

ENTRYPOINT ["/init-db.sh"]
