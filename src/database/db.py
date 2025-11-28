import sqlite3
import logging
import time 


logger = logging.getLogger(__name__)


class DatabaseConnection:
    def __init__(self, db_path='totem_data.db'):
        self.db_path = db_path
        self.conn = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
            logger.info(f"✅ Conexão com o banco de dados '{self.db_path}' aberta.")
        except Exception as e:
            logger.error(f"❌ Erro ao conectar ao banco: {e}")

    def close(self):
        if self.conn:
            self.conn.close()
            logger.info(f"✅ Conexão com o banco de dados '{self.db_path}' fechada.")
            self.conn = None

    def init_db(self):
        try:
            if not self.conn:
                self.connect()
            
            if not self.conn:
                raise Exception("Conexão com o banco de dados não estabelecida.")

            c = self.conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS deposits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                ml_confidence REAL,
                presence_detected BOOLEAN,
                weight_value INTEGER,
                weight_ok BOOLEAN,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')

            c.execute('''CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deposit_id INTEGER,
                timestamp REAL NOT NULL,
                resultado TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(deposit_id) REFERENCES deposits(id)
            )''')
            self.conn.commit()
            logger.info(f"✅ Tabelas criadas/validadas com sucesso no banco '{self.db_path}'.")
        except Exception as e:
            logger.error(f"❌ Erro ao criar tabelas: {e}")

    def save_deposit_data(self, ml_confidence, presence_detected, weight_ok, weight_value):
        try:
            if not self.conn:
                self.connect()
            if not self.conn:
                raise Exception("Conexão com o banco de dados não estabelecida.")
            c = self.conn.cursor()
            c.execute('''INSERT INTO deposits 
                         (timestamp, ml_confidence, presence_detected, weight_value, weight_ok)
                         VALUES (?, ?, ?, ?, ?)''',
                      (time.time(), ml_confidence, presence_detected, weight_value, weight_ok))
            self.conn.commit()
            logger.info(f"✅ Dados do depósito inseridos no banco '{self.db_path}'.")
        except Exception as e:
            logger.error(f"❌ Erro ao inserir depósito: {e}")
        # Se desejado, retorne o ID do depósito inserido:
        #     return c.lastrowid

    def save_interaction(self, resultado, deposit_id=None):
        try:
            if not self.conn:
                self.connect()

            if not self.conn:
                raise Exception("Conexão com o banco de dados não estabelecida.")

            c = self.conn.cursor()
            c.execute('''INSERT INTO interactions 
                         (deposit_id, timestamp, resultado)
                         VALUES (?, ?, ?)''',
                      (deposit_id, time.time(), resultado))
            self.conn.commit()
            logger.info(f"✅ Interação registrada no banco '{self.db_path}'.")
        except Exception as e:
            logger.error(f"❌ Erro ao registrar interação: {e}")



# def init_db():

#     try:
#         conn = sqlite3.connect('totem_data.db')
#         print(f"✅ Conexão com o banco de dados 'totem_data.db' estabelecida.")
#         c = conn.cursor()
#         print(f"✅ Cursor criado com sucesso.")
        
#         # [*Validate*] Confirmar sucesso da operação no banco?
#         c.execute('''CREATE TABLE IF NOT EXISTS deposits (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             timestamp REAL NOT NULL,
#             ml_confidence REAL,
#             presence_detected BOOLEAN,
#             weight_value INTEGER,
#             weight_ok BOOLEAN,
#             created_at DATETIME DEFAULT CURRENT_TIMESTAMP
#         )''')

#         # Criação da tabela 'interactions' para registrar todas as tentativas (sucesso e falha), evitando duplicidade de dados da tabela 'deposits'
#         c.execute('''CREATE TABLE IF NOT EXISTS interactions (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             deposit_id INTEGER, -- nulo se não houve depósito bem-sucedido
#             timestamp REAL NOT NULL,
#             resultado TEXT NOT NULL, -- 'sucesso', 'erro_classificacao', 'erro_mecanica', 'rejeitado', etc.
#             created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
#             FOREIGN KEY(deposit_id) REFERENCES deposits(id)
#         )''')

#         conn.commit()
#         logger.info(f"✅ Tabela 'deposits' criada com sucesso.")
#     except Exception as e:
#         logger.error(f"❌ Erro ao criar tabela: {e}")
#     finally:
#         conn.close()
#         print(f"✅ Conexão com o banco de dados 'totem_data.db' fechada.")


# def save_deposit_data(ml_confidence, presence_detected, weight_ok, weight_value):
    
#     try:

#         # [*Validate*] Can we create connection in advanced one time only?
#         conn = sqlite3.connect('totem_data.db')
#         c = conn.cursor()
    
#         c.execute('''INSERT INTO deposits 
#                      (timestamp, ml_confidence, presence_detected, weight_value, weight_ok) 
#                      VALUES (?, ?, ?, ?, ?)''',
#                   (time.time(), ml_confidence, presence_detected, weight_value, weight_ok))
        
#         conn.commit()
#         logger.info(f"✅ Depósito salvo no banco de dados")
#     except Exception as e:
#         logger.error(f"❌ Erro ao salvar depósito: {e}")
#     finally:
#         conn.close()
#         print(f"✅ Conexão com o banco de dados 'totem_data.db' fechada.")


# def save_interaction_data(deposit_id, timestamp, resultado):
#     try:

#         # [*Validate*] Can we create connection in advanced one time only?
#         conn = sqlite3.connect('totem_data.db')
#         c = conn.cursor()
#         c.execute('''INSERT INTO interactions (deposit_id, timestamp, resultado) VALUES (?, ?, ?)''', (deposit_id, timestamp, resultado))
#         conn.commit()
#         logger.info(f"✅ Interação salva no banco de dados")
#     except Exception as e:
#         logger.error(f"❌ Erro ao salvar interação: {e}")
#         import traceback
#         logger.error(f"Traceback: {traceback.format_exc()}")
#     finally:
#         conn.close()
#         print(f"✅ Conexão com o banco de dados 'totem_data.db' fechada.")


# def get_total_interacoes():
#     try:
#         conn = sqlite3.connect('totem_data.db')
#         c = conn.cursor()
#         c.execute('''SELECT COUNT(*) FROM interactions''')
#         resultado = c.fetchone()
#         total = resultado[0] if resultado else 0
#         logger.info(f"ℹ️ Total de interações no banco: {total}")
#         return total
#     except Exception as e:
#         logger.error(f"❌ Erro ao buscar total de interações: {e}")
#         import traceback
#         logger.error(f"Traceback: {traceback.format_exc()}")
#         return 0
#     finally:
#         conn.close()
#         print(f"✅ Conexão com o banco de dados 'totem_data.db' fechada.")


# def get_all_deposits():
#     try:
#         conn = sqlite3.connect('totem_data.db')
#         c = conn.cursor()
#         c.execute('''SELECT id, timestamp, ml_confidence, presence_detected, weight_value, weight_ok FROM deposits ORDER BY timestamp DESC''')
#         rows = c.fetchall()
#         deposits = []
#         for row in rows:
#             deposits.append({
#                 'id': row[0],
#                 'timestamp': row[1],
#                 'ml_confidence': row[2],
#                 'presence_detected': row[3],
#                 'weight_value': row[4],
#                 'weight_ok': row[5]
#             })
#         logger.info(f"ℹ️ Recuperados {len(deposits)} depósitos do banco")
#         return deposits
#     except Exception as e:
#         logger.error(f"❌ Erro ao buscar depósitos: {e}")
#         import traceback
#         logger.error(f"Traceback: {traceback.format_exc()}")
#         return []
#     finally:
#         conn.close()
#         print(f"✅ Conexão com o banco de dados 'totem_data.db' fechada.")

