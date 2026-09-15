# Data Dictionary — MoMo SMS Data Processing System


## Table: Users

| Column | Data Type | Constraints | Description |
|---|---|---|---|
| user_id | INT | PK, AUTO_INCREMENT |  Unique ID for the user|
| phone_number | VARCHAR(15) | NOT NULL, UNIQUE, CHECK (format) | phone number for the user|
| first_name | VARCHAR(50) | NOT NULL |User's first name |
| last_name | VARCHAR(50) | NOT NULL | User's last name|
| national_id | VARCHAR(20) | UNIQUE, nullable |nation ID for the user|
| account_type | ENUM('personal','business','agent') | NOT NULL, DEFAULT 'personal' |Type of user's momo account |
| registration_date | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Date of registration of user's account|

---

## Table: Transaction_Categories

| Column | Data Type | Constraints | Description |
|---|---|---|---|
| category_id | INT | PK, AUTO_INCREMENT |Unique ID (Primary key) for category |
| category_name | VARCHAR(50) | NOT NULL, UNIQUE | Name of the Category|
| category_type | VARCHAR(30) | NOT NULL, CHECK (IN credit/debit/fee/transfer) |Type of category |
| description | VARCHAR(255) | nullable | General description|

---

## Table: Transactions

| Column | Data Type | Constraints | Description |
|---|---|---|---|
| transaction_id | INT | PK, AUTO_INCREMENT |Unique identifier for each transaction |
| transaction_reference | VARCHAR(50) | NOT NULL, UNIQUE | Reference of transaction|
| sender_id | INT | FK → Users(user_id), nullable, ON DELETE SET NULL |Unique ID of the Sender |
| receiver_id | INT | FK → Users(user_id), NOT NULL, ON DELETE RESTRICT |Unique ID of the receiver |
| amount | DECIMAL(12,2) | NOT NULL, CHECK (amount > 0) |Amount transacted |
| currency | VARCHAR(3) | NOT NULL, DEFAULT 'RWF' |Type of currency of the transaction |
| transaction_date | DATETIME | NOT NULL | Date the transaction occurred |
| balance_after | DECIMAL(12,2) | nullable |Account balance after transaction |
| status | ENUM('pending','completed','failed','reversed') | NOT NULL, DEFAULT 'completed' | The status of the transaction|

---

## Table: Transaction_Category_Map (junction table)

| Column | Data Type | Constraints | Description |
|---|---|---|---|
| map_id | INT | PK, AUTO_INCREMENT |Unique identifier for each transaction |
| transaction_id | INT | FK → Transactions(transaction_id), NOT NULL, ON DELETE CASCADE |Category of the transaction |
| category_id | INT | FK → Transaction_Categories(category_id), NOT NULL, ON DELETE RESTRICT | Category ID of the transaction|
| (transaction_id, category_id) | — | UNIQUE composite constraint | Prevents the category to be linked twice to one transaction|

---

## Table: System_Logs

| Column | Data Type | Constraints | Description |
|---|---|---|---|
| log_id | INT | PK, AUTO_INCREMENT | Unique ID for each log|
| transaction_id | INT | FK → Transactions(transaction_id), nullable, ON DELETE SET NULL |the transaction the Linked to the log |
| log_timestamp | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP |Time and date the log was created |
| process_stage | VARCHAR(50) | NOT NULL |The process staging of the log |
| status | ENUM('success','warning','error') | NOT NULL |Status code for the process |
| message | VARCHAR(255) | nullable | Message explaining the status|

---

## Relationships Summary

| Relationship | Cardinality | Implementation |
|---|---|---|
| Users → Transactions (as sender) | 1:M | `Transactions.sender_id` FK |
| Users → Transactions (as receiver) | 1:M | `Transactions.receiver_id` FK |
| Transactions → System_Logs | 1:M | `System_Logs.transaction_id` FK |
| Transactions ↔ Transaction_Categories | M:N | Resolved via `Transaction_Category_Map` |
