"""
Sistema de Recompensas TAMPS - Totem Ambiental de Mobilização e Pontuação Sustentável
"""

import json
import os
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class RewardsSystem:
    """Gerencia pontos TAMPS e recompensas"""
    
    def __init__(self, data_dir="data/rewards"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.users_file = self.data_dir / "users.json"
        self.transactions_file = self.data_dir / "transactions.json"
        self.partners_file = self.data_dir / "partners.json"
        
        # Carregar ou criar arquivos
        self._ensure_files()
        self._load_partners()
    
    def _ensure_files(self):
        """Garante que os arquivos de dados existem"""
        if not self.users_file.exists():
            self.users_file.write_text(json.dumps({}, indent=2))
        
        if not self.transactions_file.exists():
            self.transactions_file.write_text(json.dumps([], indent=2))
        
        if not self.partners_file.exists():
            self._create_default_partners()
    
    def _create_default_partners(self):
        """Cria parceiros padrão"""
        partners = {
            "partners": [
                {
                    "id": "starbucks",
                    "name": "Starbucks",
                    "description": "Café grátis",
                    "points_required": 100,
                    "icon": "☕",
                    "color": "#00704A"
                },
                {
                    "id": "subway",
                    "name": "Subway",
                    "description": "Sanduíche grátis",
                    "points_required": 150,
                    "icon": "🥪",
                    "color": "#FFD100"
                },
                {
                    "id": "netflix",
                    "name": "Netflix",
                    "description": "1 mês grátis",
                    "points_required": 500,
                    "icon": "🎬",
                    "color": "#E50914"
                },
                {
                    "id": "spotify",
                    "name": "Spotify",
                    "description": "3 meses premium",
                    "points_required": 400,
                    "icon": "🎵",
                    "color": "#1DB954"
                },
                {
                    "id": "uber_eats",
                    "name": "Uber Eats",
                    "description": "R$50 em créditos",
                    "points_required": 120,
                    "icon": "🍕",
                    "color": "#000000"
                },
                {
                    "id": "amazon",
                    "name": "Amazon",
                    "description": "R$100 em créditos",
                    "points_required": 250,
                    "icon": "📦",
                    "color": "#FF9900"
                }
            ]
        }
        self.partners_file.write_text(json.dumps(partners, indent=2))
    
    def _load_partners(self):
        """Carrega parceiros do arquivo"""
        try:
            data = json.loads(self.partners_file.read_text())
            self.partners = data.get("partners", [])
        except Exception as e:
            logger.error(f"Erro ao carregar parceiros: {e}")
            self.partners = []
    
    def _load_users(self):
        """Carrega dados dos usuários"""
        try:
            return json.loads(self.users_file.read_text())
        except Exception as e:
            logger.error(f"Erro ao carregar usuários: {e}")
            return {}
    
    def _save_users(self, users):
        """Salva dados dos usuários"""
        try:
            self.users_file.write_text(json.dumps(users, indent=2))
        except Exception as e:
            logger.error(f"Erro ao salvar usuários: {e}")
    
    def _load_transactions(self):
        """Carrega transações"""
        try:
            return json.loads(self.transactions_file.read_text())
        except Exception as e:
            logger.error(f"Erro ao carregar transações: {e}")
            return []
    
    def _save_transactions(self, transactions):
        """Salva transações"""
        try:
            self.transactions_file.write_text(json.dumps(transactions, indent=2))
        except Exception as e:
            logger.error(f"Erro ao salvar transações: {e}")
    
    def add_cap(self, user_id, points=10, cap_type="plastic"):
        """Adiciona tampinha e concede pontos"""
        users = self._load_users()
        transactions = self._load_transactions()
        
        if user_id not in users:
            users[user_id] = {
                "total_points": 0,
                "caps_deposited": 0,
                "created_at": datetime.now().isoformat()
            }
        
        users[user_id]["total_points"] += points
        users[user_id]["caps_deposited"] += 1
        
        # Registrar transação
        transaction = {
            "user_id": user_id,
            "type": "deposit",
            "points": points,
            "cap_type": cap_type,
            "timestamp": datetime.now().isoformat()
        }
        transactions.append(transaction)
        
        self._save_users(users)
        self._save_transactions(transactions)
        
        logger.info(f"✅ Tampinha adicionada para {user_id}. Pontos: +{points}")
        return users[user_id]
    
    def redeem_reward(self, user_id, partner_id):
        """Resgata uma recompensa"""
        users = self._load_users()
        transactions = self._load_transactions()
        
        if user_id not in users:
            return {"error": "Usuário não encontrado"}
        
        partner = next((p for p in self.partners if p["id"] == partner_id), None)
        if not partner:
            return {"error": "Parceiro não encontrado"}
        
        if users[user_id]["total_points"] < partner["points_required"]:
            return {"error": f"Pontos insuficientes. Necessário: {partner['points_required']}, você tem: {users[user_id]['total_points']}"}
        
        users[user_id]["total_points"] -= partner["points_required"]
        
        # Registrar transação
        transaction = {
            "user_id": user_id,
            "type": "redeem",
            "points": -partner["points_required"],
            "partner_id": partner_id,
            "reward": partner["name"],
            "timestamp": datetime.now().isoformat()
        }
        transactions.append(transaction)
        
        self._save_users(users)
        self._save_transactions(transactions)
        
        logger.info(f"✅ Recompensa resgatada: {partner['name']} para {user_id}")
        return {
            "success": True,
            "reward": partner["name"],
            "remaining_points": users[user_id]["total_points"]
        }
    
    def get_user_data(self, user_id):
        """Obtém dados do usuário"""
        users = self._load_users()
        
        if user_id not in users:
            return None
        
        user = users[user_id].copy()
        user["id"] = user_id
        return user
    
    def get_leaderboard(self, limit=10):
        """Retorna top usuários por pontos"""
        users = self._load_users()
        
        leaderboard = sorted(
            [{"id": uid, **data} for uid, data in users.items()],
            key=lambda x: x["total_points"],
            reverse=True
        )[:limit]
        
        return leaderboard
    
    def get_partners(self):
        """Retorna lista de parceiros"""
        return self.partners


# Instância global
_rewards_system = None

def get_rewards_system():
    """Obtém instância do sistema de recompensas"""
    global _rewards_system
    if _rewards_system is None:
        _rewards_system = RewardsSystem()
    return _rewards_system
