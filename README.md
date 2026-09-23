# Phonebook Application — Python/FastAPI backend port

Backend migration of `phonebook-app` (Node.js/Express) to Python/FastAPI.
The **Vue 3 frontend is copied unchanged**, the **same SQL Server database,
tables, stored procedures and indexes** are reused, and the API keeps the
**same paths, params and response shapes** — only the server language changed.

```
Vue.js SPA (:5173)
        ↓  relative /api/...
FastAPI + Uvicorn (:8000, pyodbc → ODBC Driver 17)
        ↓  stored procedures only, no ORM
SQL Server (PhonebookDb, same machine)
```

## Project structure

```text
phonebook-app-fastapi/
├── client/                  # Vue frontend, byte-identical copy (no changes)
├── sql/phonebook.sql        # unchanged schema + procedures (reference)
├── deploy/nginx.conf        # single URL: / -> :5173, /api/ -> :8000
├── backend/
│   ├── requirements.txt
│   └── app/
│       ├── main.py          # routes, CORS, errors, SPA static, keepalive
│       ├── config.py        # .env-driven settings (no hardcoded secrets)
│       ├── database.py      # pyodbc connection factory (ODBC pooling)
│       ├── errors.py        # AppError(status, message)
│       ├── models.py        # DTOs, validation, sort whitelist (Node parity)
│       ├── repositories.py  # stored-procedure calls only
│       ├── services.py      # business logic (Node service parity)
│       └── routers/
│           ├── contacts.py  # GET/POST/PUT/DELETE /api/contacts + /suggestions
│           └── auth.py      # POST /api/auth/login
├── .env / .env.example
└── README.md
```

## Prerequisites

- Python 3.12+ (per-user install is fine) and ODBC Driver 17 for SQL Server
- Node.js LTS (frontend dev/build only), SQL Server with `PhonebookDb`
- The one-time SQL network setup from the Node project
  (`AUTO_CLOSE OFF`, SQL login) still applies — same database

## 1. Backend setup

```powershell
cd E:\CyberF\phonebook-app-fastapi
Copy-Item .env.example .env   # then fill DB_USER / DB_PASSWORD
C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe -m pip install -r backend\requirements.txt
```

## 2. Run FastAPI (:8000)

```powershell
cd E:\CyberF\phonebook-app-fastapi\backend
C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --proxy-headers
```

## 3. Run frontend (:5173+)

```powershell
cd E:\CyberF\phonebook-app-fastapi\client
npm install
npm run dev -- --host 127.0.0.1 --port 5173   # dev (proxies /api to :8000 only if vite.config points there)
npm run build                                  # production bundle -> client/dist
```

> The copied frontend calls relative `/api/...`, so in production it works
> unchanged behind Nginx. For direct dev access without a proxy, either serve
> both from one origin or set `CORS_ORIGIN` in `.env`.

## 4. Nginx single URL

```powershell
nginx -p <nginx-dir> -c E:\CyberF\phonebook-app-fastapi\deploy\nginx.conf
```

`/ → :5173`, `/api/ → :8000`. SQL Server stays private on loopback.

## API (identical to the Node version)

```text
GET    /api/health
POST   /api/auth/login                 {username, password} -> {token, username}
GET    /api/contacts?pageNumber=1&pageSize=10&searchTerm=&sortBy=Name&sortOrder=ASC
GET    /api/contacts/suggestions?term=sa&limit=8   -> ["name", ...]
GET    /api/contacts/:id
POST   /api/contacts                   -> 201 contact / 400 / 409
PUT    /api/contacts/:id               -> 200 contact / 400 / 404
DELETE /api/contacts/:id               -> 200 {message} / 404
```

Validation messages, status codes, `PagedResult` shape
(`items, totalCount, currentPage, pageSize, totalPages`) and datetime format
(`YYYY-MM-DDTHH:mm:ss.sssZ`) all match Node 1:1. Sort columns are whitelisted
(`Name, PhoneNumber, Email, CreatedAt`); injection attempts fall back to `Name`.

## Notes

- pyodbc cannot bind T-SQL `OUTPUT` params, so `sp_GetContactsPaged`
  (`@TotalCount`) and `sp_InsertContact` (`@NewId`) are wrapped in a batch
  that `SELECT`s the value back — procedures themselves are untouched.
- A 25s background keepalive (same idea as Node) keeps pool/plans warm.
- Keepalive/CORS/timeouts mirror the Node behavior; see `deploy/` and `.env.example`.
