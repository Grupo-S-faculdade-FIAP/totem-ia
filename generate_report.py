#!/usr/bin/env python3
"""
Gera relatório de comparação entre ML e ViT
Avalia ambos os modelos e cria COMPARISON_REPORT.txt
"""

import os
import json
import logging
import pickle
import numpy as np
from pathlib import Path
from datetime import datetime

import torch
from transformers import ViTImageProcessor, ViTForImageClassification
from PIL import Image
import cv2
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def load_dataset(split='test'):
    """Carrega imagens de teste"""
    base_path = Path(f'datasets/color-cap/{split}')
    images = []
    labels = []
    classes = sorted([d.name for d in base_path.iterdir() if d.is_dir()])
    class_to_idx = {cls_name: idx for idx, cls_name in enumerate(classes)}
    
    logger.info(f"📂 Carregando {len(classes)} classes de {split}")
    
    for class_name in classes:
        class_path = base_path / class_name
        for img_file in class_path.glob('*.jpg'):
            images.append(str(img_file))
            labels.append(class_to_idx[class_name])
    
    return images, labels, classes

def extract_features(image_path):
    """Extrai 36 features (RGB + HSV + histogramas)"""
    img = cv2.imread(image_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # RGB features
    rgb_mean = np.mean(img_rgb, axis=(0, 1))
    rgb_std = np.std(img_rgb, axis=(0, 1))
    
    # HSV features
    hsv_mean = np.mean(img_hsv, axis=(0, 1))
    hsv_std = np.std(img_hsv, axis=(0, 1))
    
    # Histogramas RGB (8 bins cada)
    hist_features = []
    for i in range(3):
        hist = cv2.calcHist([img_rgb], [i], None, [8], [0, 256])
        hist_features.extend(hist.flatten() / 256)
    
    return np.concatenate([rgb_mean, rgb_std, hsv_mean, hsv_std, hist_features])

def evaluate_ml_model(test_images, test_labels):
    """Avalia modelo Random Forest"""
    logger.info("🤖 Avaliando Random Forest...")
    
    with open('models/ml-cap-classifier/classifier.pkl', 'rb') as f:
        model = pickle.load(f)
    
    with open('models/ml-cap-classifier/scaler.pkl', 'rb') as f:
        scaler = pickle.load(f)
    
    # Extrai features
    features = []
    for img_path in test_images:
        features.append(extract_features(img_path))
    
    features = np.array(features)
    features = scaler.transform(features)  # Normaliza com o scaler
    predictions = model.predict(features)
    
    accuracy = accuracy_score(test_labels, predictions)
    precision = precision_score(test_labels, predictions, average='weighted', zero_division=0)
    recall = recall_score(test_labels, predictions, average='weighted', zero_division=0)
    f1 = f1_score(test_labels, predictions, average='weighted', zero_division=0)
    
    # Calcula tamanho total do modelo
    model_size = os.path.getsize('models/ml-cap-classifier/classifier.pkl') + \
                 os.path.getsize('models/ml-cap-classifier/scaler.pkl')
    
    return {
        'accuracy': float(accuracy),
        'precision': float(precision),
        'recall': float(recall),
        'f1': float(f1),
        'model_size_mb': model_size / (1024*1024)
    }

def evaluate_vit_model(test_images, test_labels, classes):
    """Avalia modelo ViT"""
    logger.info("🏛️  Avaliando ViT...")
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    processor = ViTImageProcessor.from_pretrained('models/vit-cap-finetuned')
    model = ViTForImageClassification.from_pretrained('models/vit-cap-finetuned')
    model = model.to(device)
    model.eval()
    
    predictions = []
    
    with torch.no_grad():
        for img_path in test_images:
            image = Image.open(img_path).convert('RGB')
            inputs = processor(images=image, return_tensors='pt').to(device)
            outputs = model(**inputs)
            pred = outputs.logits.argmax(-1).item()
            predictions.append(pred)
    
    predictions = np.array(predictions)
    
    accuracy = accuracy_score(test_labels, predictions)
    precision = precision_score(test_labels, predictions, average='weighted', zero_division=0)
    recall = recall_score(test_labels, predictions, average='weighted', zero_division=0)
    f1 = f1_score(test_labels, predictions, average='weighted', zero_division=0)
    
    # Tamanho do modelo
    model_size_mb = os.path.getsize('models/vit-cap-finetuned/model.safetensors') / (1024*1024)
    
    return {
        'accuracy': float(accuracy),
        'precision': float(precision),
        'recall': float(recall),
        'f1': float(f1),
        'model_size_mb': model_size_mb
    }

def generate_report(ml_metrics, vit_metrics):
    """Gera relatório de comparação"""
    
    report = f"""
╔══════════════════════════════════════════════════════════════╗
║         🏆 RELATÓRIO DE COMPARAÇÃO: ML vs ViT               ║
║              Classificação de Tampinhas Plásticas            ║
╚══════════════════════════════════════════════════════════════╝

Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

═══════════════════════════════════════════════════════════════

📊 RESULTADOS QUANTITATIVOS
═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│                    RANDOM FOREST (ML)                       │
├─────────────────────────────────────────────────────────────┤
│  Acurácia:         {ml_metrics['accuracy']:.4f} ({ml_metrics['accuracy']*100:.2f}%)
│  Precisão:         {ml_metrics['precision']:.4f} ({ml_metrics['precision']*100:.2f}%)
│  Recall:           {ml_metrics['recall']:.4f} ({ml_metrics['recall']*100:.2f}%)
│  F1-Score:         {ml_metrics['f1']:.4f}
│  Tamanho Modelo:   {ml_metrics['model_size_mb']:.2f} MB
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│           VISION TRANSFORMER (ViT)                          │
├─────────────────────────────────────────────────────────────┤
│  Acurácia:         {vit_metrics['accuracy']:.4f} ({vit_metrics['accuracy']*100:.2f}%)
│  Precisão:         {vit_metrics['precision']:.4f} ({vit_metrics['precision']*100:.2f}%)
│  Recall:           {vit_metrics['recall']:.4f} ({vit_metrics['recall']*100:.2f}%)
│  F1-Score:         {vit_metrics['f1']:.4f}
│  Tamanho Modelo:   {vit_metrics['model_size_mb']:.2f} MB
└─────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════

🎯 ANÁLISE COMPARATIVA
═══════════════════════════════════════════════════════════════

"""
    
    # Diferenças
    acc_diff = ml_metrics['accuracy'] - vit_metrics['accuracy']
    prec_diff = ml_metrics['precision'] - vit_metrics['precision']
    recall_diff = ml_metrics['recall'] - vit_metrics['recall']
    f1_diff = ml_metrics['f1'] - vit_metrics['f1']
    size_ratio = vit_metrics['model_size_mb'] / ml_metrics['model_size_mb']
    
    report += f"""
Diferenças de Performance (ML - ViT):
  ├─ Acurácia:    {acc_diff:+.4f} ({acc_diff*100:+.2f}%)
  ├─ Precisão:    {prec_diff:+.4f} ({prec_diff*100:+.2f}%)
  ├─ Recall:      {recall_diff:+.4f} ({recall_diff*100:+.2f}%)
  └─ F1-Score:    {f1_diff:+.4f}

Comparação de Tamanho:
  └─ ViT é {size_ratio:.1f}x MAIOR que ML

"""
    
    # Vencedor
    report += "═══════════════════════════════════════════════════════════════\n\n"
    report += "🏆 VENCEDOR:\n\n"
    
    if acc_diff > 0.01:
        report += f"""
✅ RANDOM FOREST (ML) VENCE!

Razões:
  • Acurácia superior: {ml_metrics['accuracy']*100:.2f}% vs {vit_metrics['accuracy']*100:.2f}%
  • Modelo {size_ratio:.1f}x MENOR ({ml_metrics['model_size_mb']:.2f}MB vs {vit_metrics['model_size_mb']:.2f}MB)
  • Inferência mais rápida
  • Excelente generalização nos dados de teste

Recomendação: Use RANDOM FOREST para produção
  └─ Melhor custo-benefício (velocidade vs acurácia)
  └─ Menor consumo de memória
  └─ Mais simples de fazer deploy

"""
    elif acc_diff < -0.01:
        report += f"""
✅ VISION TRANSFORMER (ViT) VENCE!

Razões:
  • Acurácia superior: {vit_metrics['accuracy']*100:.2f}% vs {ml_metrics['accuracy']*100:.2f}%
  • Melhor captura de features visuais complexas
  • Maior recall: {vit_metrics['recall']*100:.2f}% vs {ml_metrics['recall']*100:.2f}%

Observação: Modelo muito grande ({vit_metrics['model_size_mb']:.2f}MB)
  └─ Considere usar em GPU/servidor com bom hardware
  └─ Trade-off: acurácia vs tamanho/velocidade

"""
    else:
        report += f"""
⚖️  EMPATE TÉCNICO!

Ambos os modelos têm performance similar:
  • Acurácia praticamente idêntica
  • Escolha baseada em constraints de deployment

Decisão:
  ├─ Se memória é crítica: RANDOM FOREST ({ml_metrics['model_size_mb']:.2f}MB)
  └─ Se quer máxima acurácia: ViT ({vit_metrics['accuracy']*100:.2f}%)

"""
    
    report += """
═══════════════════════════════════════════════════════════════

📋 RESUMO TÉCNICO
═══════════════════════════════════════════════════════════════

RANDOM FOREST:
  • Algoritmo: Ensemble de árvores de decisão
  • Features: 36 (RGB + HSV + histogramas)
  • Vantagens: Rápido, pequeno, interpretável
  • Desvantagens: Features manuais, menos flexível

VISION TRANSFORMER (ViT):
  • Arquitetura: Transformer baseado em patches
  • Features: Aprendidas automaticamente (self-attention)
  • Vantagens: Capture features complexas, state-of-the-art
  • Desvantagens: Lento, grande, precisa GPU

═══════════════════════════════════════════════════════════════

✅ Análise completa disponível em: COMPARISON_REPORT.txt
"""
    
    return report

def main():
    logger.info("🏆 Gerando Relatório de Comparação")
    logger.info("="*60)
    
    # Carrega dataset de teste
    test_images, test_labels, classes = load_dataset('test')
    logger.info(f"✓ {len(test_images)} imagens de teste carregadas")
    
    # Avalia ambos os modelos
    ml_metrics = evaluate_ml_model(test_images, test_labels)
    vit_metrics = evaluate_vit_model(test_images, test_labels, classes)
    
    # Gera relatório
    report = generate_report(ml_metrics, vit_metrics)
    
    # Salva relatório
    with open('COMPARISON_REPORT.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    
    # Exibe relatório
    print(report)
    
    logger.info("✅ Relatório salvo em: COMPARISON_REPORT.txt")

if __name__ == '__main__':
    main()
