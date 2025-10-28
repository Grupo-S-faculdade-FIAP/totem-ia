#!/usr/bin/env python3
"""
API REST para Totem de Reciclagem de Tampinhas Plásticas
Integração com ESP32 para controle de esteira e feedback

Endpoints:
  POST /classify - Classifica uma imagem
  GET  /status   - Status do sistema
  POST /batch    - Classifica múltiplas imagens
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import logging
import tempfile
import json
from datetime import datetime
from typing import List, Dict, Optional

from evaluate_eligibility import CapEligibilityEvaluator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializa FastAPI
app = FastAPI(
    title="♻️ Totem de Reciclagem - API de Classificação",
    description="API para classificação de tampinhas plásticas com ML",
    version="1.0.0"
)

# Inicializa avaliador (carrega modelo uma única vez)
evaluator = None

class ClassificationResult(BaseModel):
    """Resultado de classificação de uma imagem"""
    eligible: bool
    confidence: float
    color: str
    message: str
    reason: str
    probabilities: Dict[str, float]

class BatchResult(BaseModel):
    """Resultado de lote de imagens"""
    total: int
    eligible: int
    ineligible: int
    eligibility_rate: float
    details: List[ClassificationResult]

class SystemStatus(BaseModel):
    """Status do sistema"""
    model_loaded: bool
    model_info: str
    total_classifications: int
    last_classification: Optional[str]

# Variáveis globais de status
status = {
    "total_classifications": 0,
    "last_classification": None
}

# Carrega o modelo uma única vez
def load_model():
    """Carrega o modelo na inicialização"""
    global evaluator
    if evaluator is None:
        logger.info("🔄 Iniciando API de Classificação...")
        logger.info("🔄 Carregando modelo Random Forest...")
        try:
            evaluator = CapEligibilityEvaluator()
            logger.info("✅ Modelo carregado com sucesso!")
            logger.info(f"   Classes: {', '.join(evaluator.class_names)}")
        except Exception as e:
            logger.error(f"❌ Erro ao carregar modelo: {e}")
            raise
    return evaluator

@app.on_event("startup")
async def startup_event():
    """Carrega o modelo na inicialização"""
    try:
        load_model()
    except Exception as e:
        logger.error(f"❌ Erro crítico no startup: {e}")

@app.get("/", tags=["Health"])
async def root():
    """Endpoint raiz - Health check"""
    return {
        "status": "✅ Sistema Online",
        "name": "♻️ Totem de Reciclagem - API",
        "version": "1.0.0",
        "endpoints": [
            "POST /classify - Classifica uma imagem",
            "GET  /status - Status do sistema",
            "POST /batch - Classifica múltiplas imagens"
        ]
    }

@app.get("/status", tags=["System"], response_model=SystemStatus)
async def get_status():
    """Retorna status do sistema"""
    try:
        load_model()  # Garante que o modelo está carregado
    except:
        pass
    
    return SystemStatus(
        model_loaded=evaluator is not None,
        model_info="Random Forest - 100 árvores, 36 features",
        total_classifications=status["total_classifications"],
        last_classification=status["last_classification"]
    )

@app.post("/classify", tags=["Classification"])
async def classify_image(file: UploadFile = File(...)):
    """
    Classifica uma imagem de tampinha
    
    Args:
        file: Arquivo de imagem (JPG, PNG, etc)
    
    Returns:
        Resultado de classificação com elegibilidade
    """
    try:
        load_model()  # Garante que o modelo está carregado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao carregar modelo: {e}")
    
    if evaluator is None:
        raise HTTPException(status_code=500, detail="Modelo não carregado")
    
    try:
        # Salva arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Classifica
        result = evaluator.classify_image(tmp_path)
        
        # Atualiza status
        status["total_classifications"] += 1
        status["last_classification"] = datetime.now().isoformat()
        
        # Remove arquivo temporário
        Path(tmp_path).unlink()
        
        logger.info(f"✅ Classificação: {result['color']} (confiança: {result['confidence']:.1%})")
        
        return ClassificationResult(**result)
    
    except Exception as e:
        logger.error(f"❌ Erro ao classificar: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/batch", tags=["Classification"])
async def batch_classify(files: List[UploadFile] = File(...)):
    """
    Classifica múltiplas imagens em um lote
    
    Args:
        files: Lista de arquivos de imagem
    
    Returns:
        Resultado agregado do lote com estatísticas
    """
    try:
        load_model()  # Garante que o modelo está carregado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao carregar modelo: {e}")
    
    if evaluator is None:
        raise HTTPException(status_code=500, detail="Modelo não carregado")
    
    if not files:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado")
    
    try:
        results = []
        eligible_count = 0
        
        for file in files:
            # Salva arquivo temporário
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                content = await file.read()
                tmp.write(content)
                tmp_path = tmp.name
            
            # Classifica
            result = evaluator.classify_image(tmp_path)
            results.append(ClassificationResult(**result))
            
            if result['eligible']:
                eligible_count += 1
            
            # Remove arquivo temporário
            Path(tmp_path).unlink()
        
        # Calcula estatísticas
        total = len(files)
        eligibility_rate = eligible_count / total if total > 0 else 0
        
        # Atualiza status
        status["total_classifications"] += total
        status["last_classification"] = datetime.now().isoformat()
        
        logger.info(f"📦 Lote processado: {total} imagens, {eligible_count} elegíveis ({eligibility_rate:.1%})")
        
        return BatchResult(
            total=total,
            eligible=eligible_count,
            ineligible=total - eligible_count,
            eligibility_rate=eligibility_rate,
            details=results
        )
    
    except Exception as e:
        logger.error(f"❌ Erro ao processar lote: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/esp32/check", tags=["ESP32"])
async def esp32_check(file: UploadFile = File(...)):
    """
    Endpoint otimizado para ESP32
    Retorna apenas as informações essenciais para o controle da esteira
    
    Resposta:
        {
          "accept": true/false,           # Aceitar ou rejeitar tampinha
          "color": "Vermelho",            # Cor detectada
          "confidence": 0.95,             # Confiança (0-1)
          "action": "ACCEPT/REJECT"       # Ação para esteira
        }
    """
    if evaluator is None:
        raise HTTPException(status_code=500, detail="Modelo não carregado")
    
    try:
        load_model()  # Garante que o modelo está carregado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao carregar modelo: {e}")
    
    try:
        # Salva arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Classifica
        result = evaluator.classify_image(tmp_path)
        
        # Resposta otimizada para ESP32
        response = {
            "accept": result['eligible'],
            "color": result['color'],
            "confidence": result['confidence'],
            "action": "ACCEPT" if result['eligible'] else "REJECT",
            "reason": result['reason']
        }
        
        # Remove arquivo temporário
        Path(tmp_path).unlink()
        
        logger.info(f"ESP32 -> {response['action']} ({result['color']})")
        
        return response
    
    except Exception as e:
        logger.error(f"❌ Erro ESP32: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/validate-batch", tags=["Validation"])
async def validate_batch_json(batch_data: dict):
    """
    Valida um lote pré-processado em JSON
    Útil para reprocessar resultados
    
    Args:
        batch_data: JSON com dados de imagens
    
    Returns:
        Validação dos dados
    """
    try:
        required_fields = ['total_images', 'results']
        
        for field in required_fields:
            if field not in batch_data:
                raise ValueError(f"Campo obrigatório ausente: {field}")
        
        return {
            "valid": True,
            "message": f"Lote com {batch_data['total_images']} imagens validado",
            "total": batch_data['total_images']
        }
    
    except Exception as e:
        logger.error(f"❌ Erro validação: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# Tratamento de erros global
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

if __name__ == "__main__":
    import uvicorn
    
    logger.info("=" * 70)
    logger.info("🚀 Iniciando Servidor API - Totem de Reciclagem")
    logger.info("=" * 70)
    logger.info("📍 Acesse: http://localhost:8000")
    logger.info("📚 Docs: http://localhost:8000/docs")
    logger.info("=" * 70)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
