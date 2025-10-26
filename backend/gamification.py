"""
Sistema de Gamificação
Gerencia pontos, rankings e recompensas
"""

from typing import Dict, List
from datetime import datetime, timedelta


class GamificationSystem:
    """Sistema de pontos e gamificação"""
    
    # Pontos base por tipo de material
    MATERIAL_POINTS = {
        "plastic": 10,
        "plastico": 10,
        "metal": 15,
        "paper": 8,
        "papel": 8,
        "glass": 12,
        "vidro": 12,
        "organic": 5,
        "organico": 5,
        "electronic": 20,
        "eletronico": 20,
        "unknown": 3
    }
    
    # Bônus por peso (gramas)
    WEIGHT_BONUS_TIERS = [
        (500, 10),   # 500g+ = +10 pontos
        (300, 5),    # 300g+ = +5 pontos
        (100, 2),    # 100g+ = +2 pontos
    ]
    
    # Multiplicadores especiais
    STREAK_MULTIPLIER = {
        3: 1.1,   # 3 descartes seguidos = 10% bonus
        5: 1.2,   # 5 descartes = 20% bonus
        10: 1.5,  # 10 descartes = 50% bonus
    }
    
    def __init__(self):
        self.user_streaks = {}  # Track de sequências por usuário
    
    def calculate_points(
        self, 
        material: str, 
        weight: float = 0,
        user_id: str = None,
        streak: int = 0
    ) -> Dict:
        """
        Calcula pontos para um descarte
        
        Args:
            material: Tipo de material
            weight: Peso em gramas
            user_id: ID do usuário
            streak: Sequência de descartes
        
        Returns:
            Dict com pontos totais e breakdown
        """
        # Pontos base do material
        base_points = self.MATERIAL_POINTS.get(material.lower(), 3)
        
        # Bônus por peso
        weight_bonus = 0
        for min_weight, bonus in self.WEIGHT_BONUS_TIERS:
            if weight >= min_weight:
                weight_bonus = bonus
                break
        
        # Multiplicador de streak
        multiplier = 1.0
        for streak_count, mult in self.STREAK_MULTIPLIER.items():
            if streak >= streak_count:
                multiplier = mult
        
        # Calcula total
        subtotal = base_points + weight_bonus
        total_points = int(subtotal * multiplier)
        
        return {
            "base_points": base_points,
            "weight_bonus": weight_bonus,
            "streak_multiplier": multiplier,
            "total_points": total_points,
            "breakdown": {
                "material": f"+{base_points}",
                "weight": f"+{weight_bonus}" if weight_bonus > 0 else "0",
                "streak": f"x{multiplier}" if multiplier > 1 else "x1"
            }
        }
    
    def get_bin_color(self, material: str) -> str:
        """
        Retorna a cor da lixeira correta para o material
        """
        color_mapping = {
            "plastic": "Vermelho 🔴",
            "plastico": "Vermelho 🔴",
            "metal": "Amarelo 🟡",
            "paper": "Azul 🔵",
            "papel": "Azul 🔵",
            "glass": "Verde 🟢",
            "vidro": "Verde 🟢",
            "organic": "Marrom 🟤",
            "organico": "Marrom 🟤",
            "electronic": "Laranja 🟠",
            "eletronico": "Laranja 🟠",
            "unknown": "Cinza ⚪"
        }
        
        return color_mapping.get(material.lower(), "Cinza ⚪")
    
    def get_encouragement_message(self, points: int, material: str) -> str:
        """
        Retorna mensagem motivacional baseada nos pontos
        """
        if points >= 30:
            messages = [
                "🌟 Incrível! Você é um campeão da reciclagem!",
                "🏆 Fantástico! Continue assim!",
                "⭐ Excelente trabalho! O planeta agradece!"
            ]
        elif points >= 20:
            messages = [
                "👏 Muito bem! Continue reciclando!",
                "🎉 Ótimo trabalho!",
                "💚 Parabéns! Cada descarte conta!"
            ]
        elif points >= 10:
            messages = [
                "✅ Bom trabalho!",
                "♻️ Reciclando corretamente!",
                "🌱 Ajudando o meio ambiente!"
            ]
        else:
            messages = [
                "👍 Todo descarte ajuda!",
                "♻️ Obrigado por reciclar!",
                "🌍 Fazendo a diferença!"
            ]
        
        import random
        return random.choice(messages)
    
    def generate_qr_code_data(self, user_id: str, disposal_id: int = None) -> str:
        """
        Gera dados para QR code com link para ranking
        """
        base_url = "https://totem-reciclagem.app/ranking"
        return f"{base_url}?user={user_id}"
    
    def calculate_rank(self, user_points: int, all_users_points: List[int]) -> int:
        """
        Calcula a posição no ranking
        """
        sorted_points = sorted(all_users_points, reverse=True)
        try:
            return sorted_points.index(user_points) + 1
        except ValueError:
            return len(sorted_points) + 1
    
    def get_achievement_badges(self, total_disposals: int, total_points: int) -> List[str]:
        """
        Retorna badges/conquistas desbloqueadas
        """
        badges = []
        
        # Badges por número de descartes
        if total_disposals >= 100:
            badges.append("🏆 Reciclador Expert")
        elif total_disposals >= 50:
            badges.append("🥇 Reciclador Avançado")
        elif total_disposals >= 10:
            badges.append("🥈 Reciclador Iniciante")
        elif total_disposals >= 1:
            badges.append("🌱 Primeira Reciclagem")
        
        # Badges por pontos
        if total_points >= 1000:
            badges.append("⭐ Mestre da Sustentabilidade")
        elif total_points >= 500:
            badges.append("💚 Guardião da Natureza")
        elif total_points >= 100:
            badges.append("🌿 Amigo do Planeta")
        
        return badges
    
    def get_next_milestone(self, total_points: int) -> Dict:
        """
        Retorna próximo marco/objetivo
        """
        milestones = [
            (1000, "Mestre da Sustentabilidade"),
            (500, "Guardião da Natureza"),
            (250, "Eco Warrior"),
            (100, "Amigo do Planeta"),
            (50, "Reciclador Dedicado"),
            (10, "Primeiros Passos")
        ]
        
        for points, title in milestones:
            if total_points < points:
                return {
                    "target_points": points,
                    "title": title,
                    "points_needed": points - total_points,
                    "progress_percent": (total_points / points) * 100
                }
        
        return {
            "target_points": total_points,
            "title": "Máximo Alcançado!",
            "points_needed": 0,
            "progress_percent": 100
        }
