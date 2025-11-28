import sqlite3
import logging
import time 

logger = logging.getLogger(__name__)


def init_db():

    try:
        conn = sqlite3.connect('totem_data.db')
        print(f"✅ Conexão com o banco de dados 'totem_data.db' estabelecida.")
        c = conn.cursor()
        print(f"✅ Cursor criado com sucesso.")
        
        # [*Validate*] Confirmar sucesso da operação no banco?
        c.execute('''CREATE TABLE IF NOT EXISTS deposits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL,
            ml_confidence REAL,
            presence_detected BOOLEAN,
            weight_value INTEGER,
            weight_ok BOOLEAN,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')

        # Criação da tabela 'interactions' para registrar todas as tentativas (sucesso e falha), evitando duplicidade de dados da tabela 'deposits'
        c.execute('''CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deposit_id INTEGER, -- nulo se não houve depósito bem-sucedido
            timestamp REAL NOT NULL,
            resultado TEXT NOT NULL, -- 'sucesso', 'erro_classificacao', 'erro_mecanica', 'rejeitado', etc.
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(deposit_id) REFERENCES deposits(id)
        )''')

        conn.commit()
        logger.info(f"✅ Tabela 'deposits' criada com sucesso.")
    except Exception as e:
        logger.error(f"❌ Erro ao criar tabela: {e}")
    finally:
        conn.close()
        print(f"✅ Conexão com o banco de dados 'totem_data.db' fechada.")


def save_deposit_data(ml_confidence, presence_detected, weight_ok, weight_value):
    
    try:

        # [*Validate*] Can we create connection in advanced one time only?
        conn = sqlite3.connect('totem_data.db')
        c = conn.cursor()
    
        c.execute('''INSERT INTO deposits 
                     (timestamp, ml_confidence, presence_detected, weight_value, weight_ok) 
                     VALUES (?, ?, ?, ?, ?)''',
                  (time.time(), ml_confidence, presence_detected, weight_value, weight_ok))
        
        conn.commit()
        logger.info(f"✅ Depósito salvo no banco de dados")
    except Exception as e:
        logger.error(f"❌ Erro ao salvar depósito: {e}")
    finally:
        conn.close()
        print(f"✅ Conexão com o banco de dados 'totem_data.db' fechada.")


def save_interaction_data(deposit_id, timestamp, resultado):
    try:

        # [*Validate*] Can we create connection in advanced one time only?
        conn = sqlite3.connect('totem_data.db')
        c = conn.cursor()
        c.execute('''INSERT INTO interactions (deposit_id, timestamp, resultado) VALUES (?, ?, ?)''', (deposit_id, timestamp, resultado))
        conn.commit()
        logger.info(f"✅ Interação salva no banco de dados")
    except Exception as e:
        logger.error(f"❌ Erro ao salvar interação: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        conn.close()
        print(f"✅ Conexão com o banco de dados 'totem_data.db' fechada.")