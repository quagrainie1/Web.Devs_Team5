# JSON Mapping

This document aims to show how the tables in the database (database-setup.sql)
are converted to the JSON files in the Json-model/ directory. For each column in the
database I detail the field in the JSON and the type it converts to.

There are two types of JSON in the project:

One JSON file per table (user.json, transaction.json,
transaction_category.json, transaction_category_map.json,
system_logs.json) - these simply display all the rows in the table, i.e. a JSON
representation of that table.

One combined JSON file (complete_transaction_example.json) - this displays what a
single transaction would look like if retrieved from an API including all
associated data (receiver, sender, transaction_category, system_logs) in a
single object rather than across multiple tables.

## Users table → user.json

| SQL Column | SQL Type | JSON Field | JSON Type | Notes |
|---|---|---|---|---|
| user_id | INT (PK) | user_id | number | same |
| phone_number | VARCHAR(15) | phone_number | string | kept as string to avoid loss of leading digits |
| first_name | VARCHAR(50) | first_name | string | same |
| last_name | VARCHAR(50) | last_name | string | same |
| national_id | VARCHAR(20), can be NULL | national_id | string or null | no national ID for agents / businesses so is null |
| account_type | ENUM (personal/business/agent) | account_type | string | converted to string |
| registration_date | DATETIME | registration_date | string | JSON does not support date types so stored as text in format "2024-01-15 09:00:00" |

## Transaction_Categories table → transaction_category.json

| SQL Column | SQL Type | JSON Field | JSON Type | Notes |
|---|---|---|---|---|
| category_id | INT (PK) | category_id | number | same |
| category_name | VARCHAR(50) | category_name | string | same |
| category_type | VARCHAR(30) | category_type | string | same |
| description | VARCHAR(255), can be NULL | description | string or null | same |

## Transactions table → transaction.json

| SQL Column | SQL Type | JSON Field | JSON Type | Notes |
|---|---|---|---|---|
| transaction_id | INT (PK) | transaction_id | number | same |
| transaction_reference | VARCHAR(50) | transaction_reference | string | same |
| sender_id | INT, can be NULL (FK → Users) | sender_id | number or null | no sender if transaction is a deposit |
| receiver_id | INT (FK → Users) | receiver_id | number | same |
| amount | DECIMAL(12,2) | amount | number | note about precision - SQL stores values in exact decimal format while JSON stores numbers as floats |
| currency | VARCHAR(3) | currency | string | same |
| transaction_date | DATETIME | transaction_date | string | same again with issue of storing date as text |
| balance_after | DECIMAL(12,2), can be NULL | balance_after | number or null | same |
| status | ENUM (pending/completed/failed/reversed) | status | string | same |

Note: In the transaction.json file sender_id and receiver_id are simply numbers as
in the database. In the combined example however (see below) these are replaced
with a detail of the sender and receiver rather than just the user id.

## Transaction_Category_Map table → transaction_category_map.json

| SQL Column | SQL Type | JSON Field | JSON Type | Notes |
|---|---|---|---|---|
| map_id | INT (PK) | map_id | number | same |
| transaction_id | INT (FK → Transactions) | transaction_id | number | same |
| category_id | INT (FK → Transaction_Categories) | category_id | number | same |

This is a many to many join table that maps transactions to transaction categories
(there can be more than one category per transaction). The JSON for this table is
simply a representation of the data in the table. However in the combined example
below the transaction_category_map table is not represented directly but instead
the transaction categories it links to are referenced within the transaction.

## System_Logs table → system_logs.json

| SQL Column | SQL Type | JSON Field | JSON Type | Notes |
|---|---|---|---|---|
| log_id | INT (PK) | log_id | number | same |
| transaction_id | INT, can be NULL (FK → Transactions) | transaction_id | number or null | transaction may not yet exist when the log is created |
| log_timestamp | DATETIME | log_timestamp | string | same |
| process_stage | VARCHAR(50) | process_stage | string | values such as "parsed", "categorized", "loaded" |
| status | ENUM (success/warning/error) | status | string | same |
| message | VARCHAR(255), can be NULL | message | string or null | same |

## What's different about the complete example (complete_transaction_example.json)

Here is one example of a transaction in the format that an app will
require when the information is already compiled into one transaction
and not split up into separate calls. Here is how it is different from the raw tables:

- **sender_id and receiver_id** → instead of just the ID number, here is
the full `sender` and `receiver` object (name, phone number, account
type, etc.), taken from the Users table.

- **The category map rows** → instead of the junction table, we simply put
the actual categories as a `categories` array. If a transaction had 2
categories, the array would contain 2 objects.

- **The related logs** → all System_Logs rows related to that transaction
are put into a `processing_logs` array in order.

In other words, this eliminates the need for the application to make 4 different
API calls (to Users, Transactions, Categories, Logs) and manually connect everything
– instead the API gives us 1 object that already contains everything.

---

## Type conversions from SQL to JSON, quick notes

| SQL Type | Is converted to in JSON | Reason |
|---|---|---|
| INT | number | straightforward |
| VARCHAR | string | straightforward |
| DECIMAL(12,2) | number | JSON does not have fixed decimal types, only floats, which means some precision is lost |
| DATETIME | string | JSON has no date type at all |
| ENUM | string | because the enum restriction exists only in SQL |
| NULL | null | direct mapping |

---

## Mapping this to an API (for context purposes only)

| Endpoint | Returns | Which JSON style |
|---|---|---|
| GET /users | flat list | user.json |
| GET /transactions | flat list | transaction.json |
| GET /transactions/:id | nested/combined | complete_transaction_example.json |
| GET /transaction-categories | flat list | transaction_category.json |
| GET /system-logs?transaction_id=X | flat list | system_logs.json |
