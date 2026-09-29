# MoMo Transactions API — Documentation

Base URL (local development): `http://localhost:8000`

## Authentication

Every endpoint requires **HTTP Basic Authentication**. Requests without a valid `Authorization` header, or with incorrect credentials, receive a `401 Unauthorized` response.

**Demo credentials:**

| Username | Password |
|---|---|
| `admin` | `momo2026` |
| `teamlead` | `webdevs5` |

Example using `curl`:
```bash
curl -u admin:momo2026 http://localhost:8000/transactions
```

---

## Endpoints

### 1. `GET /transactions`

Returns a list of all transactions.

**Request:**
```bash
curl -u admin:momo2026 http://localhost:8000/transactions
```

**Response — `200 OK`:**
```json
[
  {
    "id": 1,
    "address": "M-Money",
    "date_raw": "1715351458724",
    "readable_date": "10 May 2024 4:30:58 PM",
    "body": "You have received 2000 RWF from Jane Smith (*********013) on your mobile money account at 2024-05-10 16:30:51. ...",
    "transaction_type": "received",
    "amount": 2000.0,
    "fee": null,
    "new_balance": 2000.0,
    "sender": "Jane Smith",
    "receiver": null,
    "phone_number": null,
    "transaction_id": null,
    "transaction_time": "2024-05-10 16:30:51"
  },
  {
    "id": 2,
    "...": "..."
  }
]
```

---

### 2. `GET /transactions/{id}`

Returns a single transaction by its `id`.

**Request:**
```bash
curl -u admin:momo2026 http://localhost:8000/transactions/1
```

**Response — `200 OK`:**
```json
{
  "id": 1,
  "address": "M-Money",
  "date_raw": "1715351458724",
  "readable_date": "10 May 2024 4:30:58 PM",
  "body": "You have received 2000 RWF from Jane Smith (*********013) on your mobile money account at 2024-05-10 16:30:51. Message from sender: . Your new balance:2000 RWF. Financial Transaction Id: 76662021700.",
  "transaction_type": "received",
  "amount": 2000.0,
  "fee": null,
  "new_balance": 2000.0,
  "sender": "Jane Smith",
  "receiver": null,
  "phone_number": null,
  "transaction_id": null,
  "transaction_time": "2024-05-10 16:30:51"
}
```

**Response — `404 Not Found`** (id does not exist):
```json
{
  "error": "Transaction 99999 not found.",
  "status": 404
}
```

---

### 3. `POST /transactions`

Creates a new transaction. The `id` is auto-assigned by the server.

**Required fields:** `transaction_type`, `amount`

**Request:**
```bash
curl -u admin:momo2026 \
  -X POST http://localhost:8000/transactions \
  -H "Content-Type: application/json" \
  -d '{"transaction_type":"payment","amount":5000,"receiver":"Test Vendor","fee":50,"new_balance":15000}'
```

**Response — `201 Created`:**
```json
{
  "transaction_type": "payment",
  "amount": 5000,
  "receiver": "Test Vendor",
  "fee": 50,
  "new_balance": 15000,
  "id": 1692
}
```

**Response — `400 Bad Request`** (missing required field):
```json
{
  "error": "Request body must include at least 'transaction_type' and 'amount'.",
  "status": 400
}
```

**Response — `400 Bad Request`** (malformed JSON body):
```json
{
  "error": "Request body must be valid JSON.",
  "status": 400
}
```

---

### 4. `PUT /transactions/{id}`

Updates an existing transaction. Only the fields included in the request body are changed; everything else on the record stays as-is. The `id` itself cannot be changed.

**Request:**
```bash
curl -u admin:momo2026 \
  -X PUT http://localhost:8000/transactions/1692 \
  -H "Content-Type: application/json" \
  -d '{"amount":7500,"new_balance":12500}'
```

**Response — `200 OK`:**
```json
{
  "transaction_type": "payment",
  "amount": 7500,
  "receiver": "Test Vendor",
  "fee": 50,
  "new_balance": 12500,
  "id": 1692
}
```

**Response — `404 Not Found`** (id does not exist):
```json
{
  "error": "Transaction 1692 not found.",
  "status": 404
}
```

---

### 5. `DELETE /transactions/{id}`

Deletes a transaction by `id`.

**Request:**
```bash
curl -u admin:momo2026 -X DELETE http://localhost:8000/transactions/1692
```

**Response — `200 OK`:**
```json
{
  "message": "Transaction 1692 deleted."
}
```

**Response — `404 Not Found`** (id does not exist, or already deleted):
```json
{
  "error": "Transaction 1692 not found.",
  "status": 404
}
```

---

## Authentication error responses

### Missing `Authorization` header

**Request:**
```bash
curl http://localhost:8000/transactions/1
```

**Response — `401 Unauthorized`:**
```json
{
  "error": "Unauthorized",
  "status": 401,
  "message": "Valid Basic Auth credentials are required."
}
```
(Also includes a `WWW-Authenticate: Basic realm="MoMo Transactions API"` header.)

### Incorrect credentials

**Request:**
```bash
curl -u wronguser:wrongpass http://localhost:8000/transactions/1
```

**Response — `401 Unauthorized`:** same body as above.

---

## Error Code Summary

| Status Code | Meaning | When it occurs |
|---|---|---|
| `200 OK` | Success | Successful GET, PUT, or DELETE |
| `201 Created` | Resource created | Successful POST |
| `400 Bad Request` | Invalid input | Missing required fields, or malformed JSON body |
| `401 Unauthorized` | Authentication failed | Missing or incorrect Basic Auth credentials |
| `404 Not Found` | Resource missing | Requested transaction `id` doesn't exist, or an unmatched route |

---

## Running the API locally

```bash
python3 api/server.py            # starts on port 8000 by default
python3 api/server.py 9000       # or specify a custom port
```

The server loads all records from `data/transactions.json` into memory at startup. Changes made via POST/PUT/DELETE persist only for the lifetime of the running process (in-memory store, not written back to disk).
