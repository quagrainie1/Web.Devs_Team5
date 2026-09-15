## Design Rationale

The design of this database schema is to store MoMo transactions accurately to support flexible categorization and a clear processing of te audit. Here, the user table distingush between the personal, business, and agents account through the account_type function and it leaves the national_id nullable because every account type is tied to individual ID.

The transaction treats sender_ID and receiver_ID assymmentrically: as the sender_ID is nullable because some transactions, like deposits originate outside the MoMo userbase and doesnt have a sender record, and the receiver_ID is always required. When our sender deletes the field to Null to preserve history, while receiver delections are restriced to prevent remving a user still owing funds on the record.

We also employed the use of DECIMAL(12,2) instead of the FLOAT for all amounts to avoid floating-point rounding errors in financial data, since a transaction that is belonging to a 
more than one category like a payment and its fees, we used many-many relationships with a junction table, Transaction_Category_Map rather than a single category column.
 
 We also CHECK constraints on the phone number format and the type of transaction amount to catch wrong data or bad data in the database layer itself and indexes on the foreign keys and transaction_date supports the filtering that our analytics quries relies on.

