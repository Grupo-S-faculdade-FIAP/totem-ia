#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLASSIFICADOR INTELIGENTE v2 - TWO-STAGE PIPELINE
Usa DOIS modelos em sequência:
  1. MODELO BINARIO: É tampinha plástica? SIM / NAO
  2. MODELO DE CORES: Se SIM, qual é a cor?
"""

import os
import json
import pickle
import logging
from pathlib import Path
import numpy as np
import cv2
from PIL import Image

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

class CapClassifierV2:
    """Classificador de tampinhas em dois estágios"""
    
    RECYCLABLE_COLORS = {
        'Vermelho': True, 'Azul': True, 'Verde': True, 'Amarelo': True,
        'Branco': True, 'Preto': True, 'Laranja': True, 'Rosa': True,
        'Roxo': True, 'Marrom': True, 'Cinza': True, 'Transparente': True
    }
    
    MIN_CONFIDENCE = 0.70
    
    def __init__(self):
        """Inicializa AMBOS os modelos"""
        self.binary_classifier = None
        self.binary_scaler = None
        self.color_classifier = None
        self.color_scaler = None
        self.color_names = None
        
        self._load_models()
    
    def _load_models(self):
        """Carrega os dois modelos"""
        logger.info("Carregando modelos...")
        
        # Carrega modelo binário HÍBRIDO (mais preciso com fotos reais)
        try:
            with open("models/binary-cap-detector-hybrid/binary_classifier_hybrid.pkl", 'rb') as f:
                self.binary_classifier = pickle.load(f)
            with open("models/binary-cap-detector-hybrid/binary_scaler_hybrid.pkl", 'rb') as f:
                self.binary_scaler = pickle.load(f)
            logger.info("OK - Modelo binário HÍBRIDO carregado")
        except FileNotFoundError as e:
            logger.error(f"Erro ao carregar modelo binário: {e}")
            raise
        
        # Carrega modelo de cores
        try:
            with open("models/ml-cap-classifier/classifier.pkl", 'rb') as f:
                self.color_classifier = pickle.load(f)
            with open("models/ml-cap-classifier/scaler.pkl", 'rb') as f:
                self.color_scaler = pickle.load(f)
            with open("models/ml-cap-classifier/classes.json", 'r') as f:
                class_mapping = json.load(f)
                sorted_items = sorted(class_mapping.items(), key=lambda x: int(x[0]))
                self.color_names = [name for _, name in sorted_items]
            logger.info("OK - Modelo de cores carregado")
        except FileNotFoundError as e:
            logger.error(f"Erro ao carregar modelo de cores: {e}")
            raise
    
    def extract_features(self, image_path):
        """Extrai 36 features da imagem"""
        img = cv2.imread(str(image_path))
        if img is None:
            logger.error(f"Nao foi possivel carregar imagem: {image_path}")
            return None
        
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        rgb_mean = np.mean(img_rgb, axis=(0, 1))
        rgb_std = np.std(img_rgb, axis=(0, 1))
        
        hsv_mean = np.mean(img_hsv, axis=(0, 1))
        hsv_std = np.std(img_hsv, axis=(0, 1))
        
        hist_features = []
        for i in range(3):
            hist = cv2.calcHist([img_rgb], [i], None, [8], [0, 256])
            hist_features.extend(hist.flatten() / 256)
        
        features = np.concatenate([rgb_mean, rgb_std, hsv_mean, hsv_std, hist_features])
        return features
    
    def classify_image(self, image_path):
        """
        PIPELINE DE DOIS ESTAGIOS:
        1. É tampinha?
        2. Se SIM, qual é a cor?
        """
        
        logger.info(f"Processando: {image_path}")
        
        features = self.extract_features(image_path)
        if features is None:
            return {
                'stage1_is_cap': False,
                'stage1_confidence': 0.0,
                'stage2_color': 'DESCONHECIDO',
                'stage2_confidence': 0.0,
                'eligible': False,
                'message': 'Erro ao processar imagem',
                'reason': 'INVALID_IMAGE'
            }
        
        # ====================================================================
        # ESTAGIO 1: É TAMPINHA?
        # ====================================================================
        
        features_scaled = self.binary_scaler.transform([features])
        binary_pred = self.binary_classifier.predict(features_scaled)[0]
        binary_proba = self.binary_classifier.predict_proba(features_scaled)[0]
        
        is_cap_confidence = binary_proba[int(binary_pred)]
        is_cap = binary_pred == 1
        
        logger.info(f"  Estágio 1: {'É tampinha' if is_cap else 'Não é tampinha'} ({is_cap_confidence:.1%})")
        
        if not is_cap:
            return {
                'stage1_is_cap': False,
                'stage1_confidence': float(is_cap_confidence),
                'stage2_color': 'N/A',
                'stage2_confidence': 0.0,
                'eligible': False,
                'message': 'NÃO É UMA TAMPINHA - Rejeitada',
                'reason': 'NOT_A_CAP',
                'action': 'REJECT'
            }
        
        # ====================================================================
        # ESTAGIO 2: QUAL É A COR?
        # ====================================================================
        
        features_scaled = self.color_scaler.transform([features])
        color_pred = self.color_classifier.predict(features_scaled)[0]
        color_proba = self.color_classifier.predict_proba(features_scaled)[0]
        
        color_confidence = np.max(color_proba)
        color = self.color_names[color_pred]
        
        logger.info(f"  Estágio 2: Cor '{color}' ({color_confidence:.1%})")
        
        # Validação
        is_recyclable = color in self.RECYCLABLE_COLORS
        is_confident = color_confidence >= self.MIN_CONFIDENCE
        eligible = is_recyclable and is_confident
        
        logger.info(f"  Elegível: {eligible}")
        
        if not is_confident:
            message = f"Tampinha detectada mas confiança baixa ({color_confidence:.1%})"
            reason = 'LOW_CONFIDENCE'
            action = 'REJECT'
        elif not is_recyclable:
            message = f"Cor não reciclável: {color}"
            reason = 'NON_RECYCLABLE_COLOR'
            action = 'REJECT'
        else:
            message = f"ELEGÍVEL - Tampinha {color} para reciclagem"
            reason = 'ELIGIBLE'
            action = 'ACCEPT'
        
        return {
            'stage1_is_cap': True,
            'stage1_confidence': float(is_cap_confidence),
            'stage2_color': color,
            'stage2_confidence': float(color_confidence),
            'eligible': eligible,
            'message': message,
            'reason': reason,
            'action': action,
            'probabilities': {
                self.color_names[i]: float(color_proba[i])
                for i in range(len(color_proba))
            }
        }

# ============================================================================
# TESTE
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("TESTANDO CLASSIFICADOR v2 - TWO-STAGE PIPELINE")
    print("="*70 + "\n")
    
    try:
        classifier = CapClassifierV2()
        
        # Testar com imagens da pasta
        from pathlib import Path
        test_dir = Path("images")
        if test_dir.exists():
            print("Testando com imagens reais:\n")
            for img_path in list(test_dir.glob("*.jpg"))[:3]:
                result = classifier.classify_image(str(img_path))
                
                print(f"  Imagem: {img_path.name}")
                print(f"    Estágio 1 (É tampinha?): {'SIM' if result['stage1_is_cap'] else 'NAO'} ({result['stage1_confidence']:.1%})")
                
                if result['stage1_is_cap']:
                    print(f"    Estágio 2 (Qual cor?): {result['stage2_color']} ({result['stage2_confidence']:.1%})")
                    print(f"    Elegível: {'SIM' if result['eligible'] else 'NAO'}")
                    print(f"    Ação: {result['action']}\n")
                else:
                    print(f"    Ação: {result['action']}\n")
        
        print("="*70)
        print("OK - TESTE CONCLUIDO!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        traceback.print_exc()
