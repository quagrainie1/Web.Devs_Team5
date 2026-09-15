-- =====================================================================
-- MoMo SMS Data Processing System — Database Setup Script
-- Team: Web.Devs_Team5
-- Author: Otuagomah Samuel — SQL Database Implementation (Week 2)
-- =====================================================================
-- This script creates the full relational schema for storing, querying,
-- and analyzing MoMo (Mobile Money) SMS transaction data. It implements:
--   1. Users            — sender/receiver account holders
--   2. Transaction_Categories — lookup table of transaction types
--   3. Transactions      — core transaction records
--   4. Transaction_Category_Map — junction table (M:N resolution)
--   5. System_Logs       — ETL/processing audit trail
-- =====================================================================

DROP DATABASE IF EXISTS momo_sms_db;
CREATE DATABASE momo_sms_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE momo_sms_db;

-- ---------------------------------------------------------------------
-- 1. USERS
-- Stores account holders who can act as senders or receivers of
-- transactions. One user can send many transactions and receive many
-- transactions (two separate 1:M relationships onto Transactions).
-- ---------------------------------------------------------------------
CREATE TABLE Users (
    user_id            INT AUTO_INCREMENT PRIMARY KEY
                        COMMENT 'Surrogate primary key for a user/account holder',
    phone_number       VARCHAR(15) NOT NULL UNIQUE
                        COMMENT 'MoMo-registered phone number, international format e.g. 250788123456',
    first_name         VARCHAR(50) NOT NULL
                        COMMENT 'User first name',
    last_name          VARCHAR(50) NOT NULL
                        COMMENT 'User last name',
    national_id        VARCHAR(20) UNIQUE
                        COMMENT 'National ID number, unique when present; NULL allowed for unregistered/agent wallets',
    account_type       ENUM('personal', 'business', 'agent') NOT NULL DEFAULT 'personal'
                        COMMENT 'Type of MoMo account held by this user',
    registration_date  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                        COMMENT 'Timestamp the account was registered/first seen in the data',

    CONSTRAINT chk_phone_format CHECK (phone_number REGEXP '^[0-9]{9,15}$')
) ENGINE=InnoDB
  COMMENT='Account holders who send or receive MoMo transactions';

CREATE INDEX idx_users_phone ON Users(phone_number);
CREATE INDEX idx_users_national_id ON Users(national_id);


-- ---------------------------------------------------------------------
-- 2. TRANSACTION_CATEGORIES
-- Lookup table of transaction types (deposit, withdrawal, transfer,
-- payment, airtime, fee, etc.). Referenced by the junction table.
-- ---------------------------------------------------------------------
CREATE TABLE Transaction_Categories (
    category_id    INT AUTO_INCREMENT PRIMARY KEY
                   COMMENT 'Surrogate primary key for a transaction category',
    category_name  VARCHAR(50) NOT NULL UNIQUE
                   COMMENT 'Human-readable category name, e.g. Deposit, Airtime Purchase',
    category_type  VARCHAR(30) NOT NULL
                   COMMENT 'Broad classification, e.g. credit, debit, fee',
    description    VARCHAR(255)
                   COMMENT 'Longer description of what qualifies for this category',

    CONSTRAINT chk_category_type CHECK (category_type IN ('credit', 'debit', 'fee', 'transfer'))
) ENGINE=InnoDB
  COMMENT='Lookup table of MoMo transaction category types';


-- ---------------------------------------------------------------------
-- 3. TRANSACTIONS
-- Core transaction records. sender_id and receiver_id both reference
-- Users(user_id) — this models the "Sends" and "Receives" relationships
-- from the ERD as two separate foreign keys on the same table.
-- ---------------------------------------------------------------------
CREATE TABLE Transactions (
    transaction_id         INT AUTO_INCREMENT PRIMARY KEY
                           COMMENT 'Surrogate primary key for a transaction',
    transaction_reference  VARCHAR(50) NOT NULL UNIQUE
                           COMMENT 'Reference/confirmation code from the original SMS',
    sender_id              INT NULL
                           COMMENT 'FK to Users — who sent/initiated the transaction (NULL for system-originated credits)',
    receiver_id             INT NOT NULL
                           COMMENT 'FK to Users — who received the funds',
    amount                 DECIMAL(12,2) NOT NULL
                           COMMENT 'Transaction amount in the specified currency',
    currency               VARCHAR(3) NOT NULL DEFAULT 'RWF'
                           COMMENT 'ISO 4217 currency code',
    transaction_date       DATETIME NOT NULL
                           COMMENT 'Date/time the transaction occurred, parsed from the SMS',
    balance_after           DECIMAL(12,2)
                           COMMENT 'Reported account balance after the transaction, if present in the SMS',
    status                  ENUM('pending', 'completed', 'failed', 'reversed') NOT NULL DEFAULT 'completed'
                           COMMENT 'Processing status of the transaction',

    CONSTRAINT chk_amount_positive CHECK (amount > 0),

    CONSTRAINT fk_transactions_sender
        FOREIGN KEY (sender_id) REFERENCES Users(user_id)
        ON UPDATE CASCADE ON DELETE SET NULL,

    CONSTRAINT fk_transactions_receiver
        FOREIGN KEY (receiver_id) REFERENCES Users(user_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB
  COMMENT='Core MoMo transaction records';

CREATE INDEX idx_transactions_sender ON Transactions(sender_id);
CREATE INDEX idx_transactions_receiver ON Transactions(receiver_id);
CREATE INDEX idx_transactions_date ON Transactions(transaction_date);
CREATE INDEX idx_transactions_status ON Transactions(status);


-- ---------------------------------------------------------------------
-- 4. TRANSACTION_CATEGORY_MAP (junction table)
-- Resolves the many-to-many relationship between Transactions and
-- Transaction_Categories: one transaction can be tagged with more than
-- one category (e.g. "Transfer" + "Cross-border"), and one category
-- applies to many transactions.
-- ---------------------------------------------------------------------
CREATE TABLE Transaction_Category_Map (
    map_id          INT AUTO_INCREMENT PRIMARY KEY
                    COMMENT 'Surrogate primary key for the junction row',
    transaction_id  INT NOT NULL
                    COMMENT 'FK to Transactions',
    category_id     INT NOT NULL
                    COMMENT 'FK to Transaction_Categories',

    CONSTRAINT fk_map_transaction
        FOREIGN KEY (transaction_id) REFERENCES Transactions(transaction_id)
        ON UPDATE CASCADE ON DELETE CASCADE,

    CONSTRAINT fk_map_category
        FOREIGN KEY (category_id) REFERENCES Transaction_Categories(category_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,

    CONSTRAINT uq_transaction_category UNIQUE (transaction_id, category_id)
) ENGINE=InnoDB
  COMMENT='Junction table resolving the M:N relationship between transactions and categories';

CREATE INDEX idx_map_transaction ON Transaction_Category_Map(transaction_id);
CREATE INDEX idx_map_category ON Transaction_Category_Map(category_id);


-- ---------------------------------------------------------------------
-- 5. SYSTEM_LOGS
-- Audit trail for the ETL pipeline: records each processing stage a
-- transaction passed through (parsed, cleaned, categorized, loaded)
-- and whether it succeeded.
-- ---------------------------------------------------------------------
CREATE TABLE System_Logs (
    log_id          INT AUTO_INCREMENT PRIMARY KEY
                    COMMENT 'Surrogate primary key for a log entry',
    transaction_id  INT NULL
                    COMMENT 'FK to Transactions — NULL allowed for logs about records that failed before a transaction row was created',
    log_timestamp   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                    COMMENT 'When this log entry was generated',
    process_stage   VARCHAR(50) NOT NULL
                    COMMENT 'ETL stage, e.g. parsed, cleaned, categorized, loaded',
    status          ENUM('success', 'warning', 'error') NOT NULL
                    COMMENT 'Outcome of this processing stage',
    message         VARCHAR(255)
                    COMMENT 'Human-readable detail, e.g. error message or validation note',

    CONSTRAINT fk_logs_transaction
        FOREIGN KEY (transaction_id) REFERENCES Transactions(transaction_id)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB
  COMMENT='ETL processing audit trail for transactions';

CREATE INDEX idx_logs_transaction ON System_Logs(transaction_id);
CREATE INDEX idx_logs_stage_status ON System_Logs(process_stage, status);


-- =====================================================================
-- SAMPLE DATA (DML) — at least 5 records per main table
-- =====================================================================

-- ---------------------------------------------------------------------
-- Users (7 sample users)
-- ---------------------------------------------------------------------
INSERT INTO Users (phone_number, first_name, last_name, national_id, account_type, registration_date) VALUES
('250788123456', 'Alice',   'chukwe',  '1198012345678901', 'personal', '2024-01-15 09:00:00'),
('250788234567', 'Eric',    'Habimana', '1198023456789012', 'personal', '2024-01-20 10:30:00'),
('250788345678', 'Sami',    'otuagomah','1198034567890123', 'personal', '2024-02-01 08:15:00'),
('250788456789', 'Michelle','Odusanwo', '1198045678901234', 'personal', '2024-02-05 14:45:00'),
('250788567890', 'Quick Mart Ltd', 'Agent', NULL, 'business', '2024-01-10 07:00:00'),
('250788678901', 'MoMo',    'Agent01',  NULL, 'agent',    '2024-01-05 06:30:00'),
('250788789012', 'Grace',   'Mukamana', '1198056789012345', 'personal', '2024-03-01 11:00:00');

-- ---------------------------------------------------------------------
-- Transaction_Categories (6 sample categories)
-- ---------------------------------------------------------------------
INSERT INTO Transaction_Categories (category_name, category_type, description) VALUES
('Deposit',          'credit',   'Cash deposited into a MoMo account via an agent'),
('Withdrawal',       'debit',    'Cash withdrawn from a MoMo account via an agent'),
('Peer Transfer',    'transfer', 'Funds sent directly from one user to another'),
('Merchant Payment', 'debit',    'Payment made to a registered merchant/business'),
('Airtime Purchase', 'debit',    'Airtime or data bundle purchased using MoMo balance'),
('Transaction Fee',  'fee',      'Fee charged by the provider for a transaction');

-- ---------------------------------------------------------------------
-- Transactions (8 sample transactions)
-- ---------------------------------------------------------------------
INSERT INTO Transactions (transaction_reference, sender_id, receiver_id, amount, currency, transaction_date, balance_after, status) VALUES
('TXN0001', NULL, 1, 50000.00, 'RWF', '2024-03-01 09:05:00', 50000.00, 'completed'),  -- deposit, no sender
('TXN0002', 1,    2, 15000.00, 'RWF', '2024-03-02 10:15:00', 35000.00, 'completed'),
('TXN0003', 2,    3,  5000.00, 'RWF', '2024-03-02 11:00:00', 30000.00, 'completed'),
('TXN0004', 3,    5, 12000.00, 'RWF', '2024-03-03 12:30:00', 18000.00, 'completed'),
('TXN0005', 4, 6, 2000.00, 'RWF', '2024-03-04 08:00:00', 16000.00, 'completed'),
('TXN0006', 1,    5,  8000.00, 'RWF', '2024-03-05 09:45:00', 27000.00, 'completed'),
('TXN0007', 7,    2, 20000.00, 'RWF', '2024-03-06 13:20:00', 20000.00, 'pending'),
('TXN0008', 2,    7,  1500.00, 'RWF', '2024-03-06 13:25:00', 18500.00, 'failed');

-- ---------------------------------------------------------------------
-- Transaction_Category_Map (linking transactions to categories,
-- including one transaction tagged with two categories to demonstrate
-- the M:N relationship)
-- ---------------------------------------------------------------------
INSERT INTO Transaction_Category_Map (transaction_id, category_id) VALUES
(1, 1),          -- TXN0001 -> Deposit
(2, 3),          -- TXN0002 -> Peer Transfer
(3, 3),          -- TXN0003 -> Peer Transfer
(4, 4),          -- TXN0004 -> Merchant Payment
(5, 5),          -- TXN0005 -> Airtime Purchase
(6, 4),          -- TXN0006 -> Merchant Payment
(6, 6),          -- TXN0006 ALSO -> Transaction Fee (demonstrates M:N)
(7, 3),          -- TXN0007 -> Peer Transfer
(8, 3);          -- TXN0008 -> Peer Transfer

-- ---------------------------------------------------------------------
-- System_Logs (10 sample log entries across the ETL pipeline)
-- ---------------------------------------------------------------------
INSERT INTO System_Logs (transaction_id, log_timestamp, process_stage, status, message) VALUES
(1, '2024-03-01 09:05:05', 'parsed',      'success', 'XML record parsed successfully'),
(1, '2024-03-01 09:05:06', 'categorized', 'success', 'Matched keyword "deposit"'),
(1, '2024-03-01 09:05:07', 'loaded',      'success', 'Inserted into Transactions table'),
(2, '2024-03-02 10:15:05', 'parsed',      'success', 'XML record parsed successfully'),
(2, '2024-03-02 10:15:06', 'categorized', 'success', 'Matched keyword "sent to"'),
(2, '2024-03-02 10:15:07', 'loaded',      'success', 'Inserted into Transactions table'),
(7, '2024-03-06 13:20:10', 'parsed',      'warning', 'Ambiguous date format, used fallback parser'),
(7, '2024-03-06 13:20:12', 'loaded',      'success', 'Inserted into Transactions table with status pending'),
(8, '2024-03-06 13:25:10', 'parsed',      'success', 'XML record parsed successfully'),
(8, '2024-03-06 13:25:15', 'loaded',      'error',   'Insufficient balance flag detected, marked as failed');