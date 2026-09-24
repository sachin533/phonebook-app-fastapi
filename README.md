# Phonebook Application

Classic CRUD phonebook (add, view, update, delete) with search-as-you-type
suggestions, server-side pagination and sorting.

## Technology Stack

- Vue.js + Vite (frontend SPA)
- Python + FastAPI + Uvicorn (backend JSON API)
- SQL Server 2022 Express (database, T-SQL stored procedures, no ORM)
- Nginx (reverse proxy, single public URL)
- Docker + Docker Compose (local run on any OS)

> This repository is a backend port of the Node.js/Express version. The Vue
> frontend is unchanged and the same SQL Server database/procedures are used.

## Prerequisites

Install:

- Docker Desktop (running, Linux containers)
- Git

No need to manually install Python, Node.js, SQL Server or Nginx when
using Docker.

## Clone Repository

```bash
git clone <your-new-repo-url>
cd phonebook-app-fastapi
```

## Environment Configuration

Copy the example file and adjust only if needed:

```bash
cp .env.example .env
```

`.env` holds the container SA password (`MSSQL_SA_PASSWORD`, dev-only default
`Phonebook@12345`) and the admin login. **Never commit `.env`** — it is in
`.gitignore`. `.env.example` contains only placeholder values.

`docker-compose.yml` reads `MSSQL_SA_PASSWORD` / `ADMIN_USER` /
`ADMIN_PASSWORD` from the environment (with safe dev defaults), so the same
password is used by SQL Server, database-init and the FastAPI backend
without committing secrets.

## Run Application

```bash
docker compose up --build
```

What each service does:

| Service       | Role                                                        |
|---------------|-------------------------------------------------------------|
| `sqlserver`   | SQL Server 2022 Express on internal port 1433, named volume |
| `database-init` | Waits for SQL Server, runs `sql/phonebook.sql` via sqlcmd, exits |
| `backend`     | FastAPI on port 8000 (`DB_SERVER=sqlserver`), pyodbc + stored procedures |
| `frontend`    | Vite dev server on port 5173 (code unchanged)               |
| `nginx`       | Single entrypoint: `/` → frontend, `/api/` → backend        |

First boot takes a few minutes (image pulls + SQL Server startup + build).

## Access Application

Frontend:

```text
http://localhost:8080
```

API:

```text
http://localhost:8080/api/
http://localhost:8080/api/contacts?pageNumber=1&pageSize=10
```

Login with `admin` / `admin` (or your `ADMIN_USER` / `ADMIN_PASSWORD`).

## Stop Application

```bash
docker compose down
```

Data in the `sqlserver_data` volume is preserved.

## Reset Database

```bash
docker compose down -v
```

This deletes the `sqlserver_data` volume. Then:

```bash
docker compose up --build
```

The `database-init` service recreates the database, tables, indexes and
stored procedures from `sql/phonebook.sql` (safe to re-run).

## Check Containers

```bash
docker compose ps
```

## View Logs

```bash
docker compose logs
docker compose logs backend
docker compose logs database-init
docker compose logs sqlserver
docker compose logs nginx
docker compose logs frontend
```

## Rebuild

```bash
docker compose build --no-cache
```

## Troubleshooting

- **Port 8080 already in use** — another app/proxy occupies it. Stop it or
  change the `nginx` ports mapping to `"8081:80"` and open
  `http://localhost:8081`.
- **Port 1433 already in use** — a local SQL Server is running. Either stop
  it or override the mapping for local validation, e.g.
  `docker compose -f docker-compose.yml -f <override-with-"1434:1433"> up`.
  Container-to-container traffic (`sqlserver:1433`) is unaffected.
- **SQL Server startup delay** — first start can take 30–60s; `database-init`
  retries for ~2 minutes (`docker compose logs database-init`).
- **Database initialization failure** — check `database-init` logs; common
  cause is SQL Server still starting (just rerun `docker compose up`).
- **Backend database connection failure** — backend must see
  `DB_SERVER=sqlserver` and the same SA password; check
  `docker compose logs backend`.
- **Nginx 502 error** — backend or frontend container is not ready yet; wait
  and refresh, then check their logs.
- **Docker Desktop not running** — start Docker Desktop and wait until it
  reports healthy before `docker compose up`.

## Import / Export (JSON)

The Search screen has **Export JSON** (downloads all contacts as
`contacts.json`) and **Import JSON** (uploads a `.json` file) buttons.

```text
POST /api/contacts/import   [{name, phoneNumber, email?, address?}, ...]
GET  /api/contacts/export   -> [{id, name, phoneNumber, email, address, createdAt}, ...]
```

- Import validates every row with the same rules as Add Contact and reports
  `{imported, skipped, errors}`; `PhoneNumber` is unique so existing phones
  (and in-file duplicates) are skipped, never duplicated. Non-array bodies
  get 400, batches are capped at 5000 rows.
- Export streams the full ordered list from `sp_GetAllContacts` with an
  attachment download header.

## Project layout

```text
├── backend/            # FastAPI (config, database, models, routers, services)
├── client/             # Vue 3 SPA (unchanged)
├── sql/phonebook.sql   # database, tables, indexes, stored procedures
├── docker/sql/         # database-init image + init-db.sh
├── deploy/nginx-docker.conf  # / -> frontend:5173, /api/ -> backend:8000
├── docker-compose.yml
└── README.md
```
