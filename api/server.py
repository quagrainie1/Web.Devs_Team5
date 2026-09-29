"""
api/server.py

Task 2: API Implementation (CRUD Endpoints)
Task 3: Authentication & Security

A REST API for MoMo SMS transaction data, built with Python's built-in
http.server (no Flask/FastAPI), as required by the assignment.

Endpoints:
    GET    /transactions       -> list all transactions
    GET    /transactions/{id}  -> view one transaction
    POST   /transactions       -> create a new transaction
    PUT    /transactions/{id}  -> update an existing transaction
    DELETE /transactions/{id}  -> delete a transaction

Every endpoint requires HTTP Basic Authentication (see api/auth.py).
A missing or invalid Authorization header gets a 401 Unauthorized response.

Run:
    python3 api/server.py [port]

Defaults to port 8000: http://localhost:8000/transactions
"""

import json
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from auth import is_authenticated
import storage

TRANSACTIONS_PATH = re.compile(r"^/transactions/?$")
TRANSACTION_BY_ID_PATH = re.compile(r"^/transactions/(\d+)/?$")


class MomoAPIHandler(BaseHTTPRequestHandler):
    # ---- Shared helpers ----------------------------------------------

    def _send_json(self, status: int, payload: dict | list) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error_json(self, status: int, message: str) -> None:
        self._send_json(status, {"error": message, "status": status})

    def _require_auth(self) -> bool:
        """Check Basic Auth. If it fails, writes a 401 response and
        returns False so the caller can stop processing the request."""
        header = self.headers.get("Authorization")
        if not is_authenticated(header):
            body = json.dumps({
                "error": "Unauthorized",
                "status": 401,
                "message": "Valid Basic Auth credentials are required.",
            }, indent=2).encode("utf-8")
            self.send_response(401)
            # This header is what makes browsers/Postman show a login prompt
            self.send_header("WWW-Authenticate", 'Basic realm="MoMo Transactions API"')
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return False
        return True

    def _read_json_body(self) -> dict | None:
        """Read and parse the request body as JSON. Returns None (and
        sends a 400 response) if the body is missing or invalid."""
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            self._send_error_json(400, "Request body is required.")
            return None
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            self._send_error_json(400, "Request body must be valid JSON.")
            return None

    # ---- Routing -------------------------------------------------------

    def do_GET(self):
        if not self._require_auth():
            return

        path = urlparse(self.path).path

        if TRANSACTIONS_PATH.match(path):
            self._send_json(200, storage.list_all())
            return

        match = TRANSACTION_BY_ID_PATH.match(path)
        if match:
            transaction_id = int(match.group(1))
            record = storage.get(transaction_id)
            if record is None:
                self._send_error_json(404, f"Transaction {transaction_id} not found.")
            else:
                self._send_json(200, record)
            return

        self._send_error_json(404, "Not found.")

    def do_POST(self):
        if not self._require_auth():
            return

        path = urlparse(self.path).path
        if not TRANSACTIONS_PATH.match(path):
            self._send_error_json(404, "Not found.")
            return

        data = self._read_json_body()
        if data is None:
            return  # error already sent

        if "amount" not in data or "transaction_type" not in data:
            self._send_error_json(
                400, "Request body must include at least 'transaction_type' and 'amount'."
            )
            return

        created = storage.create(data)
        self._send_json(201, created)

    def do_PUT(self):
        if not self._require_auth():
            return

        path = urlparse(self.path).path
        match = TRANSACTION_BY_ID_PATH.match(path)
        if not match:
            self._send_error_json(404, "Not found. Use PUT /transactions/{id}.")
            return

        transaction_id = int(match.group(1))
        data = self._read_json_body()
        if data is None:
            return

        updated = storage.update(transaction_id, data)
        if updated is None:
            self._send_error_json(404, f"Transaction {transaction_id} not found.")
        else:
            self._send_json(200, updated)

    def do_DELETE(self):
        if not self._require_auth():
            return

        path = urlparse(self.path).path
        match = TRANSACTION_BY_ID_PATH.match(path)
        if not match:
            self._send_error_json(404, "Not found. Use DELETE /transactions/{id}.")
            return

        transaction_id = int(match.group(1))
        deleted = storage.delete(transaction_id)
        if deleted:
            self._send_json(200, {"message": f"Transaction {transaction_id} deleted."})
        else:
            self._send_error_json(404, f"Transaction {transaction_id} not found.")

    # Quieter default logging (still prints method/path/status per request)
    def log_message(self, format, *args):
        print(f"{self.address_string()} - {format % args}")


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

    storage.load()
    print(f"Loaded {storage.count()} transactions from {storage.DATA_FILE}")

    server = ThreadingHTTPServer(("0.0.0.0", port), MomoAPIHandler)
    print(f"MoMo Transactions API running on http://localhost:{port}")
    print("Endpoints (all require Basic Auth):")
    print("  GET    /transactions")
    print("  GET    /transactions/{id}")
    print("  POST   /transactions")
    print("  PUT    /transactions/{id}")
    print("  DELETE /transactions/{id}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
