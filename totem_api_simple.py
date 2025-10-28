#!/usr/bin/env python3
"""
API REST Simplificada para Totem de Reciclagem de Tampinhas Plásticas
Versão sem complexidades de ciclo de vida
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pathlib import Path
import logging
import tempfile
import json
from datetime import datetime
from typing import List, Dict, Optional

from evaluate_eligibility import CapEligibilityEvaluator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

# Inicializa FastAPI
app = FastAPI(
    title="♻️ Totem de Reciclagem - API",
    description="Classificação inteligente de tampinhas plásticas para reciclagem",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Modelo global
evaluator = None

class ClassificationResult(BaseModel):
    eligible: bool
    confidence: float
    color: str
    message: str
    reason: str
    probabilities: Dict[str, float]

class SystemStatus(BaseModel):
    model_loaded: bool
    model_info: str
    total_classifications: int
    last_classification: Optional[str]

# Status global
app.state.total_classifications = 0
app.state.last_classification = None

@app.get("/", tags=["System"])
async def root():
    """Endpoint raiz - Health check"""
    return {
        "status": "✅ Sistema Online",
        "name": "♻️ Totem de Reciclagem",
        "version": "1.0.0",
        "docs": "http://localhost:8000/docs"
    }

@app.get("/status", tags=["System"])
async def get_status():
    """Status do sistema"""
    global evaluator
    if evaluator is None:
        try:
            logger.info("⏳ Carregando modelo...")
            evaluator = CapEligibilityEvaluator()
            logger.info("✅ Modelo pronto!")
        except Exception as e:
            logger.error(f"❌ Erro: {e}")
            return {"status": "error", "message": str(e)}
    
    return {
        "model_loaded": evaluator is not None,
        "model_info": "Random Forest - 100 estimators, 36 features, 12 classes",
        "total_classifications": app.state.total_classifications,
        "last_classification": app.state.last_classification
    }

@app.post("/classify", tags=["Classification"])
async def classify_image(file: UploadFile = File(...)):
    """Classifica uma imagem de tampinha"""
    global evaluator
    
    # Carrega modelo se necessário
    if evaluator is None:
        try:
            logger.info("🔄 Carregando modelo para classificação...")
            evaluator = CapEligibilityEvaluator()
            logger.info("✅ Modelo carregado!")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao carregar modelo: {str(e)}")
    
    try:
        # Salva arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Classifica
        result = evaluator.classify_image(tmp_path)
        
        # Atualiza status
        app.state.total_classifications += 1
        app.state.last_classification = datetime.now().isoformat()
        
        # Limpa arquivo
        Path(tmp_path).unlink()
        
        logger.info(f"✅ {result['color']}: {result['confidence']:.1%} - {'ELEGÍVEL' if result['eligible'] else 'REJEITADA'}")
        
        return ClassificationResult(**result)
        
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/batch", tags=["Classification"])
async def batch_classify(files: List[UploadFile] = File(...)):
    """Classifica múltiplas imagens"""
    global evaluator
    
    if not files:
        raise HTTPException(status_code=400, detail="Envie pelo menos uma imagem")
    
    # Carrega modelo
    if evaluator is None:
        try:
            logger.info("🔄 Carregando modelo...")
            evaluator = CapEligibilityEvaluator()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    try:
        results = []
        eligible_count = 0
        
        for file in files:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                content = await file.read()
                tmp.write(content)
                tmp_path = tmp.name
            
            result = evaluator.classify_image(tmp_path)
            results.append(ClassificationResult(**result))
            
            if result['eligible']:
                eligible_count += 1
            
            Path(tmp_path).unlink()
        
        # Atualiza status
        app.state.total_classifications += len(files)
        app.state.last_classification = datetime.now().isoformat()
        
        eligibility_rate = (eligible_count / len(results) * 100) if results else 0
        
        logger.info(f"✅ Lote: {len(results)} imagens, {eligible_count} elegíveis ({eligibility_rate:.1f}%)")
        
        return {
            "total": len(results),
            "eligible": eligible_count,
            "ineligible": len(results) - eligible_count,
            "rate": eligibility_rate / 100,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/esp32/check", tags=["ESP32"])
async def esp32_check(file: UploadFile = File(...)):
    """Endpoint otimizado para ESP32 - retorna apenas dados essenciais"""
    global evaluator
    
    if evaluator is None:
        try:
            evaluator = CapEligibilityEvaluator()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        result = evaluator.classify_image(tmp_path)
        
        response = {
            "accept": result['eligible'],
            "color": result['color'],
            "confidence": float(result['confidence']),
            "action": "ACCEPT" if result['eligible'] else "REJECT"
        }
        
        Path(tmp_path).unlink()
        
        logger.info(f"🎯 ESP32: {response['action']} ({result['color']})")
        
        return response
        
    except Exception as e:
        logger.error(f"❌ ESP32 Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info("="*70)
    logger.info("🚀 Iniciando API do Totem de Reciclagem")
    logger.info(f"📍 http://localhost:8000")
    logger.info(f"📚 Docs: http://localhost:8000/docs")
    logger.info("="*70)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
