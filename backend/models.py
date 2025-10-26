from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class ClassificationRequest(BaseModel):
    user_id: str
    material: str
    weight_g: float
    recyclable: bool = True

class ClassificationResponse(BaseModel):
    success: bool
    material: str
    confidence: float
    points: int
    recyclable: bool
    message: str
    user_id: str
    timestamp: datetime

class DisposalRecord(BaseModel):
    id: int
    user_id: str
    material: str
    weight_g: float
    points: int
    recyclable: bool
    timestamp: datetime
    image_path: Optional[str] = None

class UserStats(BaseModel):
    user_id: str
    total_points: int
    total_items: int
    recyclable_items: int
    materials_count: Dict[str, int]
    last_activity: Optional[datetime] = None
    badges: List[str] = []

class RankingResponse(BaseModel):
    ranking: List[Dict[str, Any]]
    total_users: int
    updated_at: datetime

class SystemStats(BaseModel):
    total_users: int
    total_items: int
    total_points: int
    recyclable_percentage: float
    materials_distribution: Dict[str, int]
    top_materials: List[Dict[str, Any]]
    last_updated: datetime
