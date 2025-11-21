-- SQL Script para criar tabela de depósitos
-- Execute no SQLite: sqlite3 totem_data.db < create_deposits_table.sql

CREATE TABLE IF NOT EXISTS deposits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    ml_confidence REAL,
    presence_detected BOOLEAN,
    weight_value INTEGER,
    weight_ok BOOLEAN,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_deposits_timestamp ON deposits(timestamp);
