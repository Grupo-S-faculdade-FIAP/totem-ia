#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TREINADOR DE CLASSIFICADOR BINARIO
Treina modelo para detectar: É tampinha plástica? SIM ou NÃO
"""

import numpy as np
import json
import pickle
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from datetime import datetime

print("\n" + "="*70)
print("TREINADOR DE CLASSIFICADOR BINARIO - É TAMPINHA?")
print("="*70 + "\n")

# ============================================================================
# CONFIGURACOES
# ============================================================================

MODELS_DIR = Path("models")
BINARY_MODEL_DIR = MODELS_DIR / "binary-cap-detector"
BINARY_MODEL_DIR.mkdir(parents=True, exist_ok=True)

print("GERANDO DADOS SINTETICOS\n")

# ============================================================================
# PARTE 1: GERAR DADOS SINTETICOS
# ============================================================================

np.random.seed(42)

# POSITIVAS: Imagens que SÃO tampinhas (cores vibrantes)
print("Gerando dados POSITIVOS (tampinhas plásticas)...\n")

positive_features = []

colors_rgb = [
    [255, 0, 0],      # Vermelho
    [0, 0, 255],      # Azul
    [0, 255, 0],      # Verde
    [255, 255, 0],    # Amarelo
    [255, 255, 255],  # Branco
    [0, 0, 0],        # Preto
    [255, 165, 0],    # Laranja
    [255, 192, 203],  # Rosa
    [128, 0, 128],    # Roxo
    [139, 69, 19],    # Marrom
    [128, 128, 128],  # Cinza
    [200, 220, 255],  # Transparente
]

for _ in range(500):
    base_color = np.array(colors_rgb[np.random.randint(0, len(colors_rgb))])
    
    rgb_mean = base_color + np.random.normal(0, 10, 3)
    rgb_std = np.abs(np.random.normal(15, 5, 3))
    
    hsv_mean = np.array([np.random.uniform(0, 180), 
                         np.random.uniform(50, 255),
                         np.random.uniform(50, 255)])
    hsv_std = np.abs(np.random.normal(20, 5, 3))
    
    hist_features = []
    for i in range(3):
        hist = np.random.normal(0.5, 0.1, 8)
        hist = np.clip(hist, 0, 1)
        hist_features.extend(hist)
    
    features = np.concatenate([rgb_mean, rgb_std, hsv_mean, hsv_std, hist_features])
    positive_features.append(features)

positive_features = np.array(positive_features)
print(f"  OK - {len(positive_features)} tampinhas geradas")

# NEGATIVAS: Imagens que NAO SÃO tampinhas
print("\nGerando dados NEGATIVOS (não são tampinhas)...\n")

negative_features = []

for _ in range(500):
    rgb_mean = np.random.uniform(0, 255, 3)
    rgb_std = np.abs(np.random.normal(30, 10, 3))
    
    hsv_mean = np.array([np.random.uniform(0, 180),
                         np.random.uniform(0, 255),
                         np.random.uniform(0, 255)])
    hsv_std = np.abs(np.random.normal(40, 10, 3))
    
    hist_features = []
    for i in range(3):
        hist = np.random.uniform(0, 1, 8)
        hist_features.extend(hist)
    
    features = np.concatenate([rgb_mean, rgb_std, hsv_mean, hsv_std, hist_features])
    negative_features.append(features)

negative_features = np.array(negative_features)
print(f"  OK - {len(negative_features)} não-tampinhas geradas")

# ============================================================================
# PARTE 2: PREPARAR DADOS
# ============================================================================

print("\n" + "-"*70)
print("PREPARANDO DADOS PARA TREINO\n")

X = np.vstack([positive_features, negative_features])
y = np.concatenate([np.ones(len(positive_features)), np.zeros(len(negative_features))])

shuffled_idx = np.random.permutation(len(X))
X = X[shuffled_idx]
y = y[shuffled_idx]

print(f"Total de amostras: {len(X)}")
print(f"  - Positivas (tampinhas): {int(np.sum(y == 1))}")
print(f"  - Negativas (não-tampinhas): {int(np.sum(y == 0))}\n")

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.30, random_state=42, stratify=y)

print(f"Treino: {len(X_train)} amostras")
print(f"Teste: {len(X_test)} amostras\n")

# ============================================================================
# PARTE 3: NORMALIZAR E TREINAR
# ============================================================================

print("NORMALIZANDO E TREINANDO\n")

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

binary_classifier = RandomForestClassifier(
    n_estimators=100,
    max_depth=20,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1
)

binary_classifier.fit(X_train_scaled, y_train)
print("OK - Modelo treinado!\n")

# ============================================================================
# PARTE 4: AVALIACAO
# ============================================================================

print("="*70)
print("AVALIACAO DO MODELO BINARIO")
print("="*70 + "\n")

y_pred_train = binary_classifier.predict(X_train_scaled)
y_pred_test = binary_classifier.predict(X_test_scaled)

train_accuracy = accuracy_score(y_train, y_pred_train)
test_accuracy = accuracy_score(y_test, y_pred_test)

print(f"ACURACIA:")
print(f"  - Treino: {train_accuracy*100:.1f}%")
print(f"  - Teste: {test_accuracy*100:.1f}%\n")

print("RELATORIO DETALHADO (Teste):\n")
print(classification_report(y_test, y_pred_test, 
                          target_names=['Nao é Tampinha', 'É Tampinha']))

cm = confusion_matrix(y_test, y_pred_test)
print(f"\nMATRIZ DE CONFUSAO:")
print(f"                Previsto: Nao   Previsto: Sim")
print(f"Real: Nao              {cm[0,0]:<8} {cm[0,1]:<8}")
print(f"Real: Sim              {cm[1,0]:<8} {cm[1,1]:<8}\n")

cv_scores = cross_val_score(binary_classifier, X_train_scaled, y_train, cv=5)
print(f"VALIDACAO CRUZADA (5-fold):")
print(f"  Media: {cv_scores.mean()*100:.1f}%")
print(f"  Desvio: {cv_scores.std()*100:.1f}%\n")

# ============================================================================
# PARTE 5: SALVAR
# ============================================================================

print("="*70)
print("SALVANDO MODELO")
print("="*70 + "\n")

with open(BINARY_MODEL_DIR / "binary_classifier.pkl", "wb") as f:
    pickle.dump(binary_classifier, f)
print("OK - Classificador binario salvo")

with open(BINARY_MODEL_DIR / "binary_scaler.pkl", "wb") as f:
    pickle.dump(scaler, f)
print("OK - Scaler salvo")

metadata = {
    "model_type": "RandomForest_Binary",
    "purpose": "Detecta se imagem contem tampinha plastica (SIM/NAO)",
    "created": datetime.now().isoformat(),
    "classes": {
        0: "Nao é tampinha",
        1: "É tampinha plastica"
    },
    "training_samples": len(X_train),
    "test_samples": len(X_test),
    "train_accuracy": float(train_accuracy),
    "test_accuracy": float(test_accuracy),
    "cv_mean_accuracy": float(cv_scores.mean()),
    "features": 36
}

with open(BINARY_MODEL_DIR / "binary_metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)
print("OK - Metadados salvos\n")

print(f"Modelo salvo em: {BINARY_MODEL_DIR}\n")

# ============================================================================
# RESUMO
# ============================================================================

print("="*70)
print("RESUMO")
print("="*70 + "\n")

print("MODELO: Random Forest Binario")
print("PROPÓSITO: Classificar se uma imagem é tampinha ou não\n")

print("RESULTADOS:")
print(f"  - Acuracia Treino: {train_accuracy*100:.1f}%")
print(f"  - Acuracia Teste: {test_accuracy*100:.1f}%")
print(f"  - Cross-Val: {cv_scores.mean()*100:.1f}%\n")

print("FLUXO DO TOTEM (NOVO):")
print("  1. Camera capta imagem")
print("  2. Modelo Binario: É tampinha? SIM / NAO")
print("       - SIM: vai para passo 3")
print("       - NAO: rejeita imagem")
print("  3. Modelo de Cores: Qual é a cor?")
print("  4. Validação: Cor é reciclável? SIM / NAO")
print("  5. Motor: Aceita ou rejeita\n")

print("="*70)
print("OK - TREINAMENTO CONCLUIDO!")
print("="*70 + "\n")
