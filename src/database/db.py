from __future__ import annotations

import sqlite3
import logging
import time 

from enum import Enum


logger = logging.getLogger(__name__)



class DatabaseConnection:
    def __init__(self, db_path='totem_data.db'):
        self.db_path = db_path
        self.conn = None

    def __enter__(self):
        self.__connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.__close()

    def __connect(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
            logger.info(f"✅ Conexão com o banco de dados '{self.db_path}' aberta.")
        except Exception as e:
            logger.error(f"❌ Erro ao conectar ao banco: {e}")

    def __close(self):
        if self.conn:
            self.conn.close()
            logger.info(f"✅ Conexão com o banco de dados '{self.db_path}' fechada.")
            self.conn = None
    
    
    def init_db(self):
        try:
            if not self.conn:
                self.__connect()
            
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
                plastico_reciclado_g REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')

            c.execute('''CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deposit_id INTEGER,
                timestamp REAL NOT NULL,
                resultado TEXT NOT NULL, -- 'sucesso', 'erro_classificacao', 'erro_mecanica', 'rejeitado', etc.
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(deposit_id) REFERENCES deposits(id)
            )''')
            self.conn.commit()
            logger.info(f"✅ Tabelas criadas/validadas com sucesso no banco '{self.db_path}'.")
        except Exception as e:
            logger.error(f"❌ Erro ao criar tabelas: {e}")

    
    # deposit_id = db.save_deposit_data(conf, presenca, True, peso_kg, 0)
    def save_deposit_data(self, ml_confidence, presence_detected, weight_ok, weight_value, plastico_reciclado_g) -> int | None:
        try:
            if not self.conn:
                self.__connect()

            if not self.conn:
                raise Exception("Conexão com o banco de dados não estabelecida.")

            c = self.conn.cursor()
            result = c.execute('''INSERT INTO deposits 
                         (timestamp, ml_confidence, presence_detected, weight_value, weight_ok, plastico_reciclado_g)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (time.time(), ml_confidence, presence_detected, weight_value, weight_ok, plastico_reciclado_g))
            self.conn.commit()
            logger.info(f"✅ Dados do depósito inseridos no banco '{self.db_path}'.")
            return result.lastrowid if result else None
        except Exception as e:
            logger.error(f"❌ Erro ao inserir depósito: {e}")
            return None


    class ResultadoInteracao(Enum):
        SUCESSO = 'sucesso'
        ERRO_CLASSIFICACAO = 'erro_classificacao'
        ERRO_MECANICA = 'erro_mecanica'
        REJEITADO = 'rejeitado'
        ERRO_DESCONHECIDO = 'erro_desconhecido'

    def save_interaction(self, resultado: ResultadoInteracao, deposit_id: int | None = None) -> None:
        try:
            if not self.conn:
                self.__connect()

            if not self.conn:
                raise Exception("Conexão com o banco de dados não estabelecida.")

            c = self.conn.cursor()
            c.execute('''INSERT INTO interactions 
                         (deposit_id, timestamp, resultado)
                         VALUES (?, ?, ?)''',
                      (deposit_id, time.time(), resultado.value))
            self.conn.commit()
            logger.info(f"✅ Interação registrada no banco '{self.db_path}'.")
        except Exception as e:
            logger.error(f"❌ Erro ao registrar interação: {e}")
    

    def get_total_interacoes(self) -> int:
        try:
            if not self.conn:
                self.__connect()
            if not self.conn:
                raise Exception("Conexão com o banco de dados não estabelecida.")

            c = self.conn.cursor()
            c.execute('''SELECT COUNT(*) FROM interactions''')
            resultado = c.fetchone()
            total = resultado[0] if resultado else 0
            logger.info(f"ℹ️ Total de interações no banco: {total}")
            return total
        except Exception as e:
            logger.error(f"❌ Erro ao buscar total de interações: {e}", exc_info=True)
            return 0


    def get_all_deposits(self) -> list[dict]:
        try:
            if not self.conn:
                self.__connect()
            if not self.conn:
                raise Exception("Conexão com o banco de dados não estabelecida.")

            c = self.conn.cursor()
            c.execute('''SELECT id, timestamp, ml_confidence, presence_detected, weight_value, weight_ok, plastico_reciclado_g FROM deposits ORDER BY timestamp DESC''')
            rows = c.fetchall()
            deposits = [
                {
                    'id': row[0],
                    'timestamp': row[1],
                    'ml_confidence': row[2],
                    'presence_detected': row[3],
                    'weight_value': row[4],
                    'weight_ok': row[5],
                    'plastico_reciclado_g': row[6]
                }
                for row in rows
            ]
            logger.info(f"ℹ️ Recuperados {len(deposits)} depósitos do banco")
            return deposits
        except Exception as e:
            logger.error(f"❌ Erro ao buscar depósitos: {e}", exc_info=True)
            return []



