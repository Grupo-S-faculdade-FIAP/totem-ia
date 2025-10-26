#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Integração ViT com FastAPI - Novo endpoint /classify-image
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import tempfile
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from vit_classifier import ViTWasteClassifier

# Inicializa FastAPI
app = FastAPI(
    title="Classificador de Resíduos - ViT",
    description="API para classificação de resíduos usando Vision Transformer",
    version="1.0.0"
)

# Inicializa classificador
print("\n⏳ Carregando classificador ViT...")
classifier = ViTWasteClassifier()

if not classifier.has_classifier:
    print("⚠️  Aviso: ViT não disponível. Será usado fallback.")


@app.get("/")
async def root():
    """Info da API"""
    return {
        "name": "Waste Classification API - Vision Transformer",
        "version": "1.0.0",
        "status": "online",
        "model": "google/vit-base-patch16-224",
        "endpoints": {
            "classify": "/classify-image (POST)",
            "health": "/health (GET)"
        }
    }


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "model_loaded": classifier.has_classifier,
        "device": "cpu" if not classifier.has_classifier else "available"
    }


@app.post("/classify-image")
async def classify_image(file: UploadFile = File(...)):
    """
    Classifica uma imagem de resíduo
    
    Retorna:
    - material: Tipo de material (plastic, glass, metal, paper, electronic, organic)
    - confidence: Confiança da classificação (0-1)
    - source: Fonte da classificação (vit-imagenet, features-fallback, hash-fallback)
    - top_labels: Labels ImageNet mais relevantes
    """
    
    try:
        # Salva arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name
        
        # Classifica
        result = classifier.classify_image(tmp_path)
        
        # Remove arquivo temporário
        Path(tmp_path).unlink()
        
        # Formata resposta
        return JSONResponse({
            "success": result.get("success", True),
            "material": result.get("material"),
            "confidence": result.get("confidence", 0),
            "source": result.get("source"),
            "top_labels": result.get("top_labels", []),
            "error": result.get("error")
        })
    
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": str(e)
            }
        )


@app.post("/classify-batch")
async def classify_batch(files: list[UploadFile] = File(...)):
    """
    Classifica múltiplas imagens
    """
    
    results = []
    
    for file in files:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                contents = await file.read()
                tmp.write(contents)
                tmp_path = tmp.name
            
            result = classifier.classify_image(tmp_path)
            Path(tmp_path).unlink()
            
            results.append({
                "filename": file.filename,
                "material": result.get("material"),
                "confidence": result.get("confidence", 0),
                "source": result.get("source")
            })
        
        except Exception as e:
            results.append({
                "filename": file.filename,
                "error": str(e)
            })
    
    return {"results": results, "total": len(results)}


if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*80)
    print("🚀 INICIANDO SERVIDOR DE CLASSIFICAÇÃO COM ViT")
    print("="*80)
    print(f"\n📊 Modelo: Vision Transformer (google/vit-base-patch16-224)")
    print(f"🌐 URL: http://localhost:8000")
    print(f"📚 Docs: http://localhost:8000/docs")
    print(f"🔄 Fallback: Features + Hash")
    print("\n" + "="*80 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
