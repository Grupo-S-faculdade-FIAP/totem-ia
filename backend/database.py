"""
Banco de Dados do sistema
Usa SQLite com SQLAlchemy para persistência
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import List, Dict, Optional

Base = declarative_base()


class Disposal(Base):
    """Tabela de descartes de resíduos"""
    __tablename__ = "disposals"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)
    material = Column(String, nullable=False)
    weight = Column(Float, default=0)
    points = Column(Integer, default=0)
    confidence = Column(Float, default=0)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "material": self.material,
            "weight": self.weight,
            "points": self.points,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat()
        }


class User(Base):
    """Tabela de usuários/totems"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, unique=True, nullable=False, index=True)
    total_disposals = Column(Integer, default=0)
    total_points = Column(Integer, default=0)
    total_weight = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.now)
    last_disposal = Column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "total_disposals": self.total_disposals,
            "total_points": self.total_points,
            "total_weight": self.total_weight,
            "created_at": self.created_at.isoformat(),
            "last_disposal": self.last_disposal.isoformat() if self.last_disposal else None
        }


class Database:
    """Gerenciador do banco de dados"""
    
    def __init__(self, db_url: str = "sqlite:///recycling_totem.db"):
        """Inicializa conexão com banco"""
        self.engine = create_engine(db_url, echo=False)
        Base.metadata.create_all(self.engine)
        
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        print(f"✅ Banco de dados inicializado: {db_url}")
    
    def add_disposal(
        self, 
        user_id: str, 
        material: str, 
        weight: float, 
        points: int,
        confidence: float = 0
    ) -> Disposal:
        """Registra um novo descarte"""
        
        # Cria registro de descarte
        disposal = Disposal(
            user_id=user_id,
            material=material,
            weight=weight,
            points=points,
            confidence=confidence,
            timestamp=datetime.now()
        )
        
        self.session.add(disposal)
        
        # Atualiza estatísticas do usuário
        user = self.session.query(User).filter_by(user_id=user_id).first()
        
        if user:
            user.total_disposals += 1
            user.total_points += points
            user.total_weight += weight
            user.last_disposal = datetime.now()
        else:
            # Cria novo usuário
            user = User(
                user_id=user_id,
                total_disposals=1,
                total_points=points,
                total_weight=weight,
                last_disposal=datetime.now()
            )
            self.session.add(user)
        
        self.session.commit()
        
        print(f"✅ Descarte registrado: {material} ({weight}g) = {points} pts")
        
        return disposal
    
    def get_user_stats(self, user_id: str) -> Optional[Dict]:
        """Retorna estatísticas de um usuário"""
        user = self.session.query(User).filter_by(user_id=user_id).first()
        
        if not user:
            return None
        
        # Conta materiais
        disposals = self.session.query(Disposal).filter_by(user_id=user_id).all()
        materials_count = {}
        
        for disposal in disposals:
            material = disposal.material
            materials_count[material] = materials_count.get(material, 0) + 1
        
        return {
            "user_id": user.user_id,
            "total_disposals": user.total_disposals,
            "total_points": user.total_points,
            "total_weight": user.total_weight,
            "materials_count": materials_count,
            "last_disposal": user.last_disposal,
            "created_at": user.created_at
        }
    
    def get_ranking(self, limit: int = 10) -> List[Dict]:
        """Retorna ranking de usuários por pontos"""
        users = self.session.query(User).order_by(
            User.total_points.desc()
        ).limit(limit).all()
        
        ranking = []
        for idx, user in enumerate(users, 1):
            ranking.append({
                "rank": idx,
                "user_id": user.user_id,
                "total_points": user.total_points,
                "total_disposals": user.total_disposals,
                "total_weight": user.total_weight
            })
        
        return ranking
    
    def get_system_stats(self) -> Dict:
        """Retorna estatísticas gerais do sistema"""
        
        # Total de usuários
        total_users = self.session.query(User).count()
        
        # Soma de todos os descartes
        from sqlalchemy import func
        
        totals = self.session.query(
            func.count(Disposal.id),
            func.sum(Disposal.points),
            func.sum(Disposal.weight)
        ).first()
        
        total_disposals = totals[0] or 0
        total_points = totals[1] or 0
        total_weight = totals[2] or 0
        
        # Breakdown por material
        materials = self.session.query(
            Disposal.material,
            func.count(Disposal.id)
        ).group_by(Disposal.material).all()
        
        materials_breakdown = {}
        if total_disposals > 0:
            for material, count in materials:
                percentage = (count / total_disposals) * 100
                materials_breakdown[material] = round(percentage, 1)
        
        return {
            "total_disposals": total_disposals,
            "total_points": int(total_points),
            "total_weight_kg": round(total_weight / 1000, 2),
            "total_users": total_users,
            "materials_breakdown": materials_breakdown,
            "last_updated": datetime.now()
        }
    
    def get_recent_disposals(self, limit: int = 20) -> List[Dict]:
        """Retorna descartes recentes"""
        disposals = self.session.query(Disposal).order_by(
            Disposal.timestamp.desc()
        ).limit(limit).all()
        
        return [d.to_dict() for d in disposals]
    
    def get_user_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Retorna histórico de descartes de um usuário"""
        disposals = self.session.query(Disposal).filter_by(
            user_id=user_id
        ).order_by(
            Disposal.timestamp.desc()
        ).limit(limit).all()
        
        return [d.to_dict() for d in disposals]
    
    def clear_all_data(self):
        """Limpa todos os dados (use com cuidado!)"""
        self.session.query(Disposal).delete()
        self.session.query(User).delete()
        self.session.commit()
        print("⚠️  Todos os dados foram apagados!")
    
    def close(self):
        """Fecha conexão com banco"""
        self.session.close()
        print("✅ Conexão com banco fechada")
