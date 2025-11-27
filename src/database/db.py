import sqlite3
import logging
import time 

logger = logging.getLogger(__name__)


def init_db():
    conn = sqlite3.connect('totem_data.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS deposits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp REAL NOT NULL,
        ml_confidence REAL,
        presence_detected BOOLEAN,
        weight_value INTEGER,
        weight_ok BOOLEAN,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')


def save_deposit_data(ml_confidence, presence_detected, weight_ok, weight_value):
    """Salva dados da interação no banco SQLite"""
    try:

        # [*Validate*] Can we create connection in advanced one time only?
        conn = sqlite3.connect('totem_data.db')
        c = conn.cursor()
        
        # c.execute('''CREATE TABLE IF NOT EXISTS deposits (
        #     id INTEGER PRIMARY KEY AUTOINCREMENT,
        #     timestamp REAL NOT NULL,
        #     ml_confidence REAL,
        #     presence_detected BOOLEAN,
        #     weight_value INTEGER,
        #     weight_ok BOOLEAN,
        #     created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        # )''')
        
        c.execute('''INSERT INTO deposits 
                     (timestamp, ml_confidence, presence_detected, weight_value, weight_ok) 
                     VALUES (?, ?, ?, ?, ?)''',
                  (time.time(), ml_confidence, presence_detected, weight_value, weight_ok))
        
        conn.commit()
        conn.close()
        logger.info(f"✅ Depósito salvo no banco de dados")
    except Exception as e:
        logger.error(f"❌ Erro ao salvar depósito: {e}")