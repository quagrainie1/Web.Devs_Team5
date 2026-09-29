# Web.Devs_Team5

## Project: MoMo SMS Data Analysis Dashboard

An enterprise-level fullstack application that processes MoMo (Mobile Money) SMS data
in XML format, cleans and categorizes transactions, stores them in a relational
database, and provides a frontend dashboard for analysis and visualization.

### Overview
This project implements an ETL (Extract, Transform, Load) pipeline that:
Parses raw MoMo SMS XML data
Cleans and normalizes transaction fields (amounts, dates, phone numbers)
Categorizes transactions by type
Loads processed data into a SQLite database
Exposes aggregated data to a static frontend dashboard for visualization

### Team Members
1. Eric Quagrainie
2. Samuel Otuagomah
3. Odusanwo Michelle

### Architecture
<img width="512" height="749" alt="Architectural Diagram" src="https://github.com/user-attachments/assets/8153b5f6-5051-40be-adb6-743e1e539de2" />

### Scrum Board
[MoMo Dashboard - Scrum Board](https://github.com/users/quagrainie1/projects/1/views/1)

## Database Design & Data modelling
The Entity Relationship Diagram and design justification for the MoMo SMS database are available in `docs/erd/`.

ERD (Task 1): docs/erd/ — Eric Quagrainie
SQL implementation (Task 2): database_setup.sql — Sami Otuagomah
JSON data modeling (Task 3): Json-model/ and docs/json_mapping.md — Michelle Odusanwo

Continuation from the 3rd Project

## MoMo Transactions REST API (Week 3)

### Overview
This API exposes the parsed MoMo SMS transaction data over HTTP, with full CRUD support and HTTP Basic Authentication. It's built entirely with Python's built-in `http.server` — no external web framework.

### Prerequisites
- Python 3.10+
- No external packages required (standard library only)

### Setup & Running the Parser

The API reads from `data/transactions.json`, which is generated from the raw SMS export. If that file doesn't exist yet (or you want to regenerate it):

```bash
python3 dsa/parse_xml.py
```

This reads `data/modified_sms_v2.xml` and writes `data/transactions.json`.

### Running the API Server

```bash
python3 api/server.py
```

The server starts on port 8000 by default: `http://localhost:8000`

To use a different port:
```bash
python3 api/server.py 9000
```

### Authentication

All endpoints require HTTP Basic Authentication.

| Username | Password |
|---|---|
| `admin` | `momo2026` |
| `teamlead` | `webdevs5` |

> Update these credentials in `api/auth.py` before any real deployment — they're hardcoded for this assignment only.

### Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/transactions` | List all transactions |
| GET | `/transactions/{id}` | Get a single transaction |
| POST | `/transactions` | Create a new transaction |
| PUT | `/transactions/{id}` | Update an existing transaction |
| DELETE | `/transactions/{id}` | Delete a transaction |

Full request/response examples and error codes are documented in [`docs/api_docs.md`](docs/api_docs.md).

### Quick Test

```bash
# List all transactions
curl -u admin:momo2026 http://localhost:8000/transactions

# Get one transaction
curl -u admin:momo2026 http://localhost:8000/transactions/1

# Create a transaction
curl -u admin:momo2026 -X POST http://localhost:8000/transactions \
  -H "Content-Type: application/json" \
  -d '{"transaction_type":"payment","amount":5000,"receiver":"Test Vendor"}'
```

Test screenshots covering successful and unauthorized requests are in [`screenshots/`](screenshots/).

### Project Structure (Week 3 additions)

```
├── api/
│   ├── server.py       # REST API (CRUD endpoints + routing)
│   ├── storage.py       # In-memory data store
│   └── auth.py           # Basic Auth logic
├── dsa/
│   ├── parse_xml.py       # XML -> JSON parser
│   └── search.py           # Linear search vs. dictionary lookup comparison
├── docs/
│   └── api_docs.md         # Full endpoint documentation
├── screenshots/            # CRUD + auth test screenshots
└── data/
    ├── modified_sms_v2.xml # Raw SMS export
    └── transactions.json    # Parsed transaction data (generated)
```
