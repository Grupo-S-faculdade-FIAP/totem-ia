"""
API Principal do Sistema de Reciclagem Inteligente
FastAPI backend com classificação de IA e gamificação
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from datetime import datetime
from typing import Optional, List
import qrcode
import io
import base64

# Módulos locais
from models import (
    ClassificationRequest,
    ClassificationResponse,
    DisposalRecord,
    UserStats,
    RankingResponse,
    SystemStats
)
from gamification import GamificationSystem
from database import Database, User
from image_analyzer import ImageAnalyzer
from waste_image_generator import WasteImageGenerator, AugmentedImageGenerator
from ai_models import HuggingFaceClassifier, OpenAIClassifier, HybridClassifier, GenerativeClassifier

# Inicializa FastAPI
app = FastAPI(
    title="Totem de Reciclagem IA",
    description="API para classificação de resíduos com gamificação",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS para permitir requisições do ESP32
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializa componentes
print("\n" + "="*60)
print("🚀 INICIALIZANDO SISTEMA DE RECICLAGEM INTELIGENTE")
print("="*60 + "\n")

# Configuração de modo de IA
import os
from dotenv import load_dotenv

load_dotenv()

ai_mode = os.getenv("AI_MODE", "simulation").lower()
ai_strategy = os.getenv("AI_STRATEGY", "ensemble").lower()

print(f"📊 Modo de IA: {ai_mode}")
print(f"🔄 Estratégia: {ai_strategy}\n")

# Inicializa classificadores
if ai_mode == "hybrid":
    print("🔗 Inicializando Classificador Híbrido (HF + OpenAI)...")
    classifier = HybridClassifier(use_hf=True, use_openai=True)
    ai_classifier_type = "hybrid"
elif ai_mode == "openai":
    print("🤖 Inicializando Classificador OpenAI (GPT-4V)...")
    classifier = OpenAIClassifier()
    ai_classifier_type = "openai"
elif ai_mode == "huggingface":
    print("🤗 Inicializando Classificador Hugging Face (CLIP)...")
    classifier = HuggingFaceClassifier(model_type="clip")
    ai_classifier_type = "huggingface"
else:
    print("🎯 Utilizando modo Simulação")
    classifier = AIClassifier(model_type="simulation")
    ai_classifier_type = "simulation"

# Inicializa outros componentes
gamification = GamificationSystem()
database = Database()
image_analyzer = ImageAnalyzer()
image_generator = WasteImageGenerator()
generative = GenerativeClassifier()

print("\n✅ Sistema inicializado com sucesso!\n")


@app.get("/")
async def root():
    """Endpoint raiz com informações da API"""
    return {
        "message": "🌱 Totem de Reciclagem Inteligente - API",
        "version": "1.0.0",
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "classify": "/classify",
            "register_disposal": "/register-disposal",
            "ranking": "/ranking",
            "stats": "/stats",
            "user_stats": "/user/{user_id}",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check para monitoramento"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected",
        "ai_model": classifier.model_type
    }


@app.post("/classify", response_model=ClassificationResponse)
async def classify_waste(request: ClassificationRequest):
    """
    Classifica um resíduo e retorna tipo, lixeira e pontos
    
    - **user_id**: ID do usuário/totem
    - **weight**: Peso em gramas
    - **simulation**: Modo simulação
    - **material_hint**: Dica de material (apenas simulação)
    """
    try:
        print(f"\n📥 Requisição de classificação recebida:")
        print(f"   User: {request.user_id}")
        print(f"   Peso: {request.weight}g")
        print(f"   Simulação: {request.simulation}")
        
        # Classifica o material
        result = classifier.classify_image(
            image_data=None,
            material_hint=request.material_hint
        )
        
        material = result["material"]
        material_pt = result["material_pt"]
        confidence = result["confidence"]
        
        print(f"\n🤖 Classificação IA:")
        print(f"   Material: {material_pt}")
        print(f"   Confiança: {confidence}%")
        
        # Calcula pontos
        points_data = gamification.calculate_points(
            material=material,
            weight=request.weight,
            user_id=request.user_id
        )
        
        total_points = points_data["total_points"]
        weight_bonus = points_data["weight_bonus"]
        
        print(f"\n🎮 Pontuação:")
        print(f"   Pontos base: {points_data['base_points']}")
        print(f"   Bônus peso: {weight_bonus}")
        print(f"   Total: {total_points}")
        
        # Cor da lixeira
        bin_color = gamification.get_bin_color(material)
        
        # Mensagem motivacional
        message = gamification.get_encouragement_message(total_points, material)
        
        # Registra no banco de dados
        disposal = database.add_disposal(
            user_id=request.user_id,
            material=material,
            weight=request.weight,
            points=total_points,
            confidence=confidence
        )
        
        print(f"\n✅ Descarte #{disposal.id} registrado com sucesso!")
        
        return ClassificationResponse(
            material=material_pt,
            bin_color=bin_color,
            points=total_points,
            confidence=confidence,
            message=message,
            weight_bonus=weight_bonus
        )
        
    except Exception as e:
        print(f"\n❌ Erro na classificação: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-image")
async def analyze_waste_image(
    file: UploadFile = File(...),
    user_id: str = Query(...)
):
    """
    Analisa uma imagem de resíduo com visão computacional
    Detecta: material, peso aproximado, elegibilidade
    
    Retorna análise completa com scores de confiança
    """
    try:
        # Lê bytes da imagem
        image_bytes = await file.read()
        
        print(f"\n📸 Analisando imagem:")
        print(f"   Arquivo: {file.filename}")
        print(f"   Tamanho: {len(image_bytes)} bytes")
        print(f"   User: {user_id}")
        
        # Analisa a imagem com visão computacional
        analysis = image_analyzer.analyze(image_bytes)
        
        if not analysis["success"]:
            raise Exception(analysis.get("error", "Erro ao analisar imagem"))
        
        material = analysis["material"]["material"]
        weight = analysis["estimated_weight_g"]
        recyclable = analysis["recyclable"]
        
        print(f"\n🔬 Análise Visual:")
        print(f"   Material: {material}")
        print(f"   Peso estimado: {weight}g")
        print(f"   Elegível: {'✅ Sim' if recyclable else '❌ Não'}")
        print(f"   Confiança: {analysis['confidence_score']}%")
        
        # Se elegível, calcula pontos e registra
        if recyclable:
            # Classifica com IA
            ai_result = classifier.classify_image(
                image_data=None,
                material_hint=material
            )
            
            # Calcula pontos
            points_data = gamification.calculate_points(
                material=material,
                weight=weight,
                user_id=user_id
            )
            
            # Registra no banco
            disposal = database.add_disposal(
                user_id=user_id,
                material=material,
                weight=weight,
                points=points_data["total_points"],
                confidence=analysis["confidence_score"]
            )
            
            print(f"\n✅ Descarte #{disposal.id} registrado!")
            print(f"   Pontos: {points_data['total_points']}")
            
            return {
                "success": True,
                "material": material,
                "material_pt": {
                    "plastic": "Plástico",
                    "metal": "Metal",
                    "paper": "Papel",
                    "glass": "Vidro",
                    "organic": "Orgânico"
                }.get(material, material),
                "weight_g": weight,
                "bin_color": gamification.get_bin_color(material),
                "points": points_data["total_points"],
                "recyclable": True,
                "analysis": {
                    "confidence": analysis["confidence_score"],
                    "size_category": analysis["size"]["size_category"],
                    "quality_score": analysis["quality"]["overall_quality"],
                    "estimated_size_cm": analysis["size"]["estimated_size_cm"]
                },
                "message": gamification.get_encouragement_message(
                    points_data["total_points"],
                    material
                )
            }
        else:
            # Não elegível
            print(f"\n⚠️  Item não elegível: {analysis['eligibility_reason']}")
            
            return {
                "success": True,
                "material": material,
                "weight_g": weight,
                "recyclable": False,
                "reason": analysis["eligibility_reason"],
                "analysis": {
                    "confidence": analysis["confidence_score"],
                    "size_category": analysis["size"]["size_category"],
                    "quality_score": analysis["quality"]["overall_quality"]
                },
                "message": f"❌ {analysis['eligibility_reason']}. Por favor, escolha outro item para descartar.",
                "points": 0
            }
        
    except Exception as e:
        print(f"❌ Erro na análise: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/classify-image")
async def classify_image_upload(
    file: UploadFile = File(...),
    user_id: str = Query(...),
    weight: float = Query(0)
):
    """
    Classifica uma imagem enviada via upload
    Para uso com câmera real do ESP32-S3
    """
    try:
        # Lê bytes da imagem
        image_bytes = await file.read()
        
        print(f"\n📸 Imagem recebida:")
        print(f"   Arquivo: {file.filename}")
        print(f"   Tamanho: {len(image_bytes)} bytes")
        print(f"   User: {user_id}")
        
        # Classifica
        result = classifier.classify_image(image_data=image_bytes)
        
        material = result["material"]
        confidence = result["confidence"]
        
        # Calcula pontos
        points_data = gamification.calculate_points(
            material=material,
            weight=weight,
            user_id=user_id
        )
        
        # Registra
        database.add_disposal(
            user_id=user_id,
            material=material,
            weight=weight,
            points=points_data["total_points"],
            confidence=confidence
        )
        
        return {
            "material": result["material_pt"],
            "bin_color": gamification.get_bin_color(material),
            "points": points_data["total_points"],
            "confidence": confidence,
            "message": gamification.get_encouragement_message(
                points_data["total_points"], 
                material
            )
        }
        
    except Exception as e:
        print(f"❌ Erro no upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ranking", response_model=RankingResponse)
async def get_ranking(limit: int = Query(10, ge=1, le=100)):
    """
    Retorna ranking de usuários por pontuação
    
    - **limit**: Número de usuários no ranking (1-100)
    """
    try:
        ranking = database.get_ranking(limit=limit)
        total_users = len(ranking)
        
        return RankingResponse(
            ranking=ranking,
            total_users=total_users,
            updated_at=datetime.now()
        )
        
    except Exception as e:
        print(f"❌ Erro ao buscar ranking: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", response_model=SystemStats)
async def get_system_stats():
    """Retorna estatísticas gerais do sistema"""
    try:
        stats = database.get_system_stats()
        return stats
        
    except Exception as e:
        print(f"❌ Erro ao buscar estatísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user/{user_id}", response_model=UserStats)
async def get_user_stats(user_id: str):
    """
    Retorna estatísticas de um usuário específico
    
    - **user_id**: ID do usuário/totem
    """
    try:
        stats = database.get_user_stats(user_id)
        
        if not stats:
            raise HTTPException(
                status_code=404, 
                detail=f"Usuário {user_id} não encontrado"
            )
        
        # Calcula rank
        all_users = database.session.query(User).all()
        all_points = [u.total_points for u in all_users]
        rank = gamification.calculate_rank(stats["total_points"], all_points)
        
        return UserStats(
            user_id=stats["user_id"],
            total_disposals=stats["total_disposals"],
            total_points=stats["total_points"],
            total_weight=stats["total_weight"],
            materials_count=stats["materials_count"],
            last_disposal=stats["last_disposal"],
            rank=rank
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erro ao buscar usuário: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user/{user_id}/history")
async def get_user_history(
    user_id: str,
    limit: int = Query(50, ge=1, le=200)
):
    """Retorna histórico de descartes de um usuário"""
    try:
        history = database.get_user_history(user_id, limit=limit)
        return {
            "user_id": user_id,
            "total_records": len(history),
            "history": history
        }
        
    except Exception as e:
        print(f"❌ Erro ao buscar histórico: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user/{user_id}/qrcode")
async def get_user_qrcode(user_id: str):
    """
    Gera QR Code para o perfil do usuário
    Retorna imagem em base64
    """
    try:
        # Gera dados do QR code
        qr_data = gamification.generate_qr_code_data(user_id)
        
        # Cria QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Converte para base64
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            "user_id": user_id,
            "qr_data": qr_data,
            "qr_image_base64": img_base64
        }
        
    except Exception as e:
        print(f"❌ Erro ao gerar QR code: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user/{user_id}/badges")
async def get_user_badges(user_id: str):
    """Retorna badges/conquistas do usuário"""
    try:
        stats = database.get_user_stats(user_id)
        
        if not stats:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        badges = gamification.get_achievement_badges(
            total_disposals=stats["total_disposals"],
            total_points=stats["total_points"]
        )
        
        next_milestone = gamification.get_next_milestone(stats["total_points"])
        
        return {
            "user_id": user_id,
            "badges": badges,
            "next_milestone": next_milestone
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erro ao buscar badges: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/recent")
async def get_recent_disposals(limit: int = Query(20, ge=1, le=100)):
    """Retorna descartes recentes do sistema"""
    try:
        recent = database.get_recent_disposals(limit=limit)
        return {
            "total": len(recent),
            "disposals": recent
        }
        
    except Exception as e:
        print(f"❌ Erro ao buscar descartes recentes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/admin/clear-data")
async def clear_all_data(confirm: str = Query(...)):
    """
    ⚠️ ADMIN: Limpa todos os dados do banco
    Requer confirmação
    """
    if confirm != "YES_DELETE_ALL":
        raise HTTPException(
            status_code=400,
            detail="Confirmação necessária: confirm=YES_DELETE_ALL"
        )
    
    try:
        database.clear_all_data()
        return {"message": "⚠️ Todos os dados foram apagados!"}
        
    except Exception as e:
        print(f"❌ Erro ao limpar dados: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test-image")
async def get_test_image(material: str = Query("plastic")):
    """
    Gera uma imagem de teste de resíduo
    
    Materiais disponíveis: plastic, metal, paper, glass, organic
    """
    materials = ["plastic", "metal", "paper", "glass", "organic"]
    
    if material not in materials:
        raise HTTPException(
            status_code=400,
            detail=f"Material inválido. Escolha entre: {', '.join(materials)}"
        )
    
    try:
        print(f"\n🎨 Gerando imagem de teste: {material}")
        
        # Gera imagem
        image = image_generator.generate_waste_image(material, style="realistic")
        
        # Converte para bytes
        image_bytes = image_generator.to_bytes(image, format="jpg")
        
        from fastapi.responses import StreamingResponse
        return StreamingResponse(
            iter([image_bytes]),
            media_type="image/jpeg",
            headers={"Content-Disposition": f"inline; filename=test_{material}.jpg"}
        )
    
    except Exception as e:
        print(f"❌ Erro ao gerar imagem: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/demo/analyze-test-image")
async def demo_analyze_image(
    material: str = Query("plastic"),
    user_id: str = Query("demo_user"),
    style: str = Query("realistic")
):
    """
    DEMO: Analisa uma imagem de teste gerada automaticamente
    
    Útil para testar o sistema sem câmera real
    
    Materiais: plastic, metal, paper, glass, organic
    Estilos: realistic, textured, simple
    """
    materials = ["plastic", "metal", "paper", "glass", "organic"]
    styles = ["realistic", "textured", "simple"]
    
    if material not in materials:
        raise HTTPException(status_code=400, detail=f"Material inválido")
    if style not in styles:
        raise HTTPException(status_code=400, detail=f"Estilo inválido")
    
    try:
        print(f"\n🎨 DEMO: Gerando imagem ({material}, {style})")
        
        # Gera imagem de teste
        test_image = image_generator.generate_waste_image(material, style=style)
        image_bytes = image_generator.to_bytes(test_image, format="jpg")
        
        # Analisa
        print(f"🔬 Analisando imagem...")
        analysis = image_analyzer.analyze(image_bytes)
        
        if not analysis["success"]:
            raise Exception(analysis.get("error", "Erro na análise"))
        
        detected_material = analysis["material"]["material"]
        weight = analysis["estimated_weight_g"]
        recyclable = analysis["recyclable"]
        
        print(f"\n✅ Análise concluída:")
        print(f"   Material esperado: {material}")
        print(f"   Material detectado: {detected_material}")
        print(f"   Peso estimado: {weight}g")
        print(f"   Elegível: {'✅' if recyclable else '❌'}")
        
        # Se elegível, calcula pontos
        if recyclable:
            points_data = gamification.calculate_points(
                material=detected_material,
                weight=weight,
                user_id=user_id
            )
            
            database.add_disposal(
                user_id=user_id,
                material=detected_material,
                weight=weight,
                points=points_data["total_points"],
                confidence=analysis["confidence_score"]
            )
            
            return {
                "status": "success",
                "original_material": material,
                "detected_material": detected_material,
                "weight_g": weight,
                "recyclable": True,
                "points": points_data["total_points"],
                "bin_color": gamification.get_bin_color(detected_material),
                "accuracy": f"{analysis['confidence_score']}%",
                "analysis": {
                    "confidence": analysis["confidence_score"],
                    "size_category": analysis["size"]["size_category"],
                    "quality_score": analysis["quality"]["overall_quality"],
                    "texture": analysis["material"]["texture_profile"]
                }
            }
        else:
            return {
                "status": "not_recyclable",
                "detected_material": detected_material,
                "weight_g": weight,
                "reason": analysis["eligibility_reason"],
                "accuracy": f"{analysis['confidence_score']}%"
            }
    
    except Exception as e:
        print(f"❌ Erro na DEMO: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/generate-dataset")
async def generate_dataset(
    count: int = Query(5, ge=1, le=50),
    save_path: str = Query("./dataset/test_images")
):
    """
    Gera dataset de imagens de teste
    
    Cria lote de imagens para validação do sistema
    """
    try:
        print(f"\n📦 Gerando dataset com {count} imagens...")
        
        import os
        os.makedirs(save_path, exist_ok=True)
        
        materials = ["plastic", "metal", "paper", "glass", "organic"]
        generated = []
        
        for i in range(count):
            material = materials[i % len(materials)]
            style = ["realistic", "textured", "simple"][i % 3]
            
            image = image_generator.generate_waste_image(material, style=style)
            filename = f"{save_path}/{material}_{i}_{style}.jpg"
            image_generator.save_image(image, filename)
            
            generated.append({
                "filename": filename,
                "material": material,
                "style": style
            })
            
            print(f"   ✅ {i+1}/{count} - {material} ({style})")
        
        return {
            "status": "success",
            "count": count,
            "path": save_path,
            "images": generated,
            "message": f"✅ Dataset gerado com sucesso em {save_path}"
        }
    
    except Exception as e:
        print(f"❌ Erro ao gerar dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/classify-with-ai")
async def classify_with_ai_mode(
    file: UploadFile = File(...),
    user_id: str = Query(...),
    ai_mode: str = Query("auto")
):
    """
    Classifica imagem com modo de IA específico
    
    Modos disponíveis:
    - auto: Usa configuração padrão (tipicamente hybrid)
    - hybrid: HuggingFace + OpenAI ensemble
    - openai: GPT-4V apenas
    - huggingface: CLIP apenas
    - vision: Análise visual com image_analyzer
    """
    try:
        image_bytes = await file.read()
        
        print(f"\n🤖 Classificação com IA Mode: {ai_mode}")
        print(f"   Arquivo: {file.filename}")
        print(f"   Tamanho: {len(image_bytes)} bytes\n")
        
        result = None
        method_used = ""
        
        # Seleciona modo
        if ai_mode == "openai" and isinstance(classifier, (OpenAIClassifier, HybridClassifier)):
            if isinstance(classifier, HybridClassifier):
                openai_clf = classifier.openai_classifier
                result = openai_clf.classify_image(image_bytes) if openai_clf else None
            else:
                result = classifier.classify_image(image_bytes)
            method_used = "OpenAI GPT-4V"
        
        elif ai_mode == "huggingface" and isinstance(classifier, (HuggingFaceClassifier, HybridClassifier)):
            if isinstance(classifier, HybridClassifier):
                hf_clf = classifier.hf_classifier
                result = hf_clf.classify_image(image_bytes) if hf_clf else None
            else:
                result = classifier.classify_image(image_bytes)
            method_used = "HuggingFace CLIP"
        
        elif ai_mode == "hybrid" and isinstance(classifier, HybridClassifier):
            result = classifier.classify_image(image_bytes, strategy="ensemble")
            method_used = "Hybrid (Ensemble)"
        
        elif ai_mode == "vision":
            result = image_analyzer.analyze(image_bytes)
            if result["success"]:
                # Converte para formato padrão
                result = {
                    "material": result["material"]["material"],
                    "confidence": result["confidence_score"],
                    "method": "vision_analysis",
                    "weight_estimate": result["estimated_weight_g"],
                    "recyclable": result["recyclable"]
                }
            method_used = "Vision Analysis (CV)"
        
        else:
            # Auto ou fallback
            if isinstance(classifier, HybridClassifier):
                result = classifier.classify_image(image_bytes, strategy="ensemble")
                method_used = "Hybrid (Auto)"
            else:
                result = classifier.classify_image(image_bytes) if hasattr(classifier, 'classify_image') else None
                method_used = ai_classifier_type
        
        if not result or not result.get("success", False):
            raise HTTPException(status_code=400, detail=f"Erro na classificação: {result}")
        
        # Extrai material e calcula pontos
        material = result.get("material", "unknown")
        confidence = result.get("confidence", 50)
        
        # Estima peso (usa OpenAI se disponível)
        weight = result.get("estimated_weight", result.get("weight_estimate", 100))
        
        print(f"✅ Classificação: {material} ({confidence}%)")
        print(f"📊 Método: {method_used}")
        
        # Calcula pontos
        points_data = gamification.calculate_points(
            material=material,
            weight=weight,
            user_id=user_id
        )
        
        # Registra
        database.add_disposal(
            user_id=user_id,
            material=material,
            weight=weight,
            points=points_data["total_points"],
            confidence=confidence
        )
        
        # Gera mensagem
        message = generative.generate_encouragement(
            material,
            weight,
            points_data["total_points"]
        )
        
        return {
            "success": True,
            "material": material,
            "bin_color": gamification.get_bin_color(material),
            "confidence": confidence,
            "points": points_data["total_points"],
            "weight_g": weight,
            "method": method_used,
            "message": message,
            "recyclable": result.get("recyclable", True)
        }
    
    except Exception as e:
        print(f"❌ Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ai-status")
async def get_ai_status():
    """Retorna status dos classificadores de IA disponíveis"""
    status = {
        "mode": ai_mode,
        "strategy": ai_strategy,
        "classifiers": {
            "simulation": True,
            "openai": isinstance(classifier, (OpenAIClassifier, HybridClassifier)) and (
                classifier.openai_classifier if isinstance(classifier, HybridClassifier) else classifier
            ).available,
            "huggingface": isinstance(classifier, (HuggingFaceClassifier, HybridClassifier)) and bool(
                classifier.hf_classifier if isinstance(classifier, HybridClassifier) else classifier.api_key
            ),
            "hybrid": isinstance(classifier, HybridClassifier)
        },
        "timestamp": datetime.now().isoformat()
    }
    
    return {
        "status": "online",
        "ai_system": status,
        "available_endpoints": [
            "/classify",
            "/classify-with-ai",
            "/analyze-image",
            "/demo/analyze-test-image"
        ]
    }


@app.delete("/admin/clear-data")
async def clear_data():
    """
    Limpa todos os dados do sistema
    
    Remove todos os registros de usuários, itens e estatísticas
    """
    try:
        print("\n🧹 Limpando dados do sistema...")
        
        # Limpa tabelas
        database.clear_all_data()
        
        print("✅ Dados limpos com sucesso")
        return {
            "status": "success",
            "message": "Todos os dados foram removidos do sistema"
        }
    
    except Exception as e:
        print(f"❌ Erro ao limpar dados: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# Eventos de startup/shutdown
@app.on_event("startup")
async def startup_event():
    """Executado ao iniciar a aplicação"""
    print("\n" + "="*60)
    print("✅ API INICIADA COM SUCESSO")
    print("="*60)
    print(f"📝 Documentação: http://localhost:8080/docs")
    print(f"🔄 Redoc: http://localhost:8080/redoc")
    print("="*60 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """Executado ao desligar a aplicação"""
    print("\n🛑 Encerrando aplicação...")
    database.close()
    print("✅ Aplicação encerrada com sucesso\n")


# Execução direta
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 INICIANDO SERVIDOR FASTAPI")
    print("="*60 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        reload=False,  # Sem reload para evitar problemas em background
        log_level="info"
    )
