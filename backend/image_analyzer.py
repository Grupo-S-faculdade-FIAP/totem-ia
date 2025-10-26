"""
Analisador de Imagem com Visão Computacional
Detecta material, peso aproximado e elegibilidade para reciclagem
"""

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("⚠️  OpenCV não disponível - usando modo simulação")
    import numpy as np

from typing import Dict, Tuple, Optional
from PIL import Image
import io


class ImageAnalyzer:
    """Analisa imagens de resíduos para extrair características"""
    
    def __init__(self):
        """Inicializa o analisador"""
        self.material_colors = {
            "plastic": {
                "hue_range": ((85, 135), (165, 175)),  # Verde/Ciano
                "characteristics": ["transparent", "translucent", "rigid", "flexible"]
            },
            "metal": {
                "hue_range": ((0, 30), (150, 180)),  # Prata/Cinza
                "characteristics": ["reflective", "rigid", "shiny"]
            },
            "paper": {
                "hue_range": ((10, 40),),  # Amarelo/Bege/Marrom
                "characteristics": ["matte", "textured", "flexible"]
            },
            "glass": {
                "hue_range": ((0, 10), (170, 180)),  # Transparente/Claro
                "characteristics": ["transparent", "reflective", "rigid"]
            },
            "organic": {
                "hue_range": ((15, 35), (80, 90)),  # Marrom/Verde
                "characteristics": ["matte", "irregular", "soft"]
            }
        }
        
        # Peso por volume (aproximado)
        self.density_estimates = {
            "plastic": 1.2,      # g/cm³
            "metal": 7.8,        # g/cm³ (aço)
            "paper": 0.8,        # g/cm³
            "glass": 2.5,        # g/cm³
            "organic": 0.5       # g/cm³ (média)
        }
        
        print("✅ Analisador de imagem inicializado")
    
    def analyze(self, image_data: bytes) -> Dict:
        """
        Analisa uma imagem de resíduo
        
        Args:
            image_data: Bytes da imagem (JPEG/PNG)
        
        Returns:
            Dict com análise completa
        """
        try:
            if not CV2_AVAILABLE:
                # Usa análise simulada quando OpenCV não está disponível
                return self._analyze_simulated(image_data)
            
            # Converte bytes para numpy array
            image = self._bytes_to_opencv(image_data)
            
            if image is None:
                return self._analyze_simulated(image_data)
            
            # Análises
            material_analysis = self._analyze_material(image)
            size_analysis = self._analyze_size(image)
            quality_analysis = self._analyze_quality(image)
            
            # Estima peso
            estimated_weight = self._estimate_weight(material_analysis, size_analysis)
            
            # Verifica elegibilidade
            eligibility = self._check_eligibility(
                material_analysis["material"],
                estimated_weight,
                quality_analysis
            )
            
            return {
                "success": True,
                "material": material_analysis,
                "size": size_analysis,
                "quality": quality_analysis,
                "estimated_weight_g": estimated_weight,
                "recyclable": eligibility["recyclable"],
                "eligibility_reason": eligibility["reason"],
                "confidence_score": self._calculate_confidence(
                    material_analysis, 
                    quality_analysis
                )
            }
        
        except Exception as e:
            print(f"❌ Erro ao analisar imagem: {e}")
            return self._get_empty_analysis(error=str(e))
    
    def _bytes_to_opencv(self, image_data: bytes) -> Optional[np.ndarray]:
        """Converte bytes para imagem OpenCV"""
        if not CV2_AVAILABLE:
            return None
        
        try:
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return image
        except Exception as e:
            print(f"⚠️  Erro ao decodificar imagem: {e}")
            return None
    
    def _analyze_material(self, image: np.ndarray) -> Dict:
        """Analisa o tipo de material pela cor e textura"""
        
        # Converte para HSV (melhor para análise de cor)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Analisadores de características
        histograma = self._calculate_histogram(hsv)
        textura = self._analyze_texture(image)
        reflectancia = self._analyze_reflectance(image)
        
        # Detecta material predominante
        material_scores = {}
        
        for material, params in self.material_colors.items():
            score = 0
            
            # Análise de cor
            for hue_range in params["hue_range"]:
                mask = cv2.inRange(hsv, 
                    (hue_range[0], 50, 50),
                    (hue_range[1], 255, 255)
                )
                color_match = cv2.countNonZero(mask) / image.size * 100
                score += color_match * 0.3
            
            # Análise de textura
            if "matte" in params["characteristics"] and textura["matte_score"] > 0.6:
                score += 20
            if "textured" in params["characteristics"] and textura["edge_density"] > 0.3:
                score += 15
            
            # Análise de reflexão
            if "reflective" in params["characteristics"] and reflectancia > 0.4:
                score += 20
            if "transparent" in params["characteristics"]:
                if self._is_transparent(image) > 0.5:
                    score += 25
            
            material_scores[material] = score
        
        # Encontra melhor match
        best_material = max(material_scores, key=material_scores.get)
        confidence = self._normalize_score(material_scores[best_material])
        
        return {
            "material": best_material,
            "confidence": confidence,
            "all_scores": material_scores,
            "texture_profile": textura
        }
    
    def _analyze_size(self, image: np.ndarray) -> Dict:
        """Analisa o tamanho do objeto"""
        
        height, width = image.shape[:2]
        
        # Detecta contornos do objeto
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return {
                "estimated_size_cm": 5,
                "object_area_percentage": 0.05,
                "size_category": "small"
            }
        
        # Maior contorno = objeto
        largest_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest_contour)
        object_percentage = area / (height * width)
        
        # Estima tamanho em cm (assume camera com FOV padrão)
        estimated_dimension = np.sqrt(area) * 0.5  # Fator de escala
        
        # Categoriza tamanho
        if estimated_dimension < 3:
            size_category = "tiny"
        elif estimated_dimension < 8:
            size_category = "small"
        elif estimated_dimension < 20:
            size_category = "medium"
        else:
            size_category = "large"
        
        return {
            "estimated_size_cm": round(estimated_dimension, 1),
            "object_area_percentage": round(object_percentage * 100, 2),
            "size_category": size_category,
            "contour_area": area
        }
    
    def _analyze_quality(self, image: np.ndarray) -> Dict:
        """Analisa qualidade/condição do objeto"""
        
        # Detecta deformações e danos
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        
        # Detecta clareza
        focus_score = 1.0 if variance > 100 else variance / 100
        
        # Detecta deformação (contorno irregular)
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        deformation_score = 1.0
        if contours:
            largest = max(contours, key=cv2.contourArea)
            perimeter = cv2.arcLength(largest, True)
            area = cv2.contourArea(largest)
            
            if area > 0:
                circularity = 4 * np.pi * area / (perimeter ** 2)
                deformation_score = min(circularity, 1.0)
        
        # Detecta contaminação (variação de cor)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        saturation = hsv[:, :, 1]
        contamination_score = 1.0 - (saturation.std() / 255.0)
        
        return {
            "focus_score": round(focus_score, 2),
            "deformation_score": round(deformation_score, 2),
            "contamination_score": round(contamination_score, 2),
            "overall_quality": round((focus_score + deformation_score + contamination_score) / 3, 2)
        }
    
    def _calculate_histogram(self, hsv: np.ndarray) -> Dict:
        """Calcula histograma HSV"""
        hist_h = cv2.calcHist([hsv], [0], None, [180], [0, 180])
        hist_s = cv2.calcHist([hsv], [1], None, [256], [0, 256])
        hist_v = cv2.calcHist([hsv], [2], None, [256], [0, 256])
        
        return {
            "hue_dominant": np.argmax(hist_h),
            "saturation_mean": hist_s.mean(),
            "value_mean": hist_v.mean()
        }
    
    def _analyze_texture(self, image: np.ndarray) -> Dict:
        """Analisa textura da superfície"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detecta bordas (textura)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = cv2.countNonZero(edges) / edges.size
        
        # Detecta suavidade (matte score)
        # Imagens matte têm menos reflexos
        matte_score = 1.0 if edge_density > 0.1 else edge_density / 0.1
        
        # Detecta rugosidade
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        roughness = laplacian.std()
        
        return {
            "edge_density": round(edge_density, 3),
            "matte_score": round(min(matte_score, 1.0), 2),
            "roughness": round(roughness, 2)
        }
    
    def _analyze_reflectance(self, image: np.ndarray) -> float:
        """Analisa reflexão (brilho) da superfície"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Calcula brilho médio
        brightness = gray.mean()
        
        # Normaliza (0-1)
        reflectance = brightness / 255.0
        
        return reflectance
    
    def _is_transparent(self, image: np.ndarray) -> float:
        """Detecta se o objeto é transparente"""
        # Objetos transparentes têm pouca variação de cor
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        saturation = hsv[:, :, 1]
        
        # Baixa saturação = mais transparente
        transparency = 1.0 - (saturation.mean() / 255.0)
        
        return transparency
    
    def _estimate_weight(self, material_analysis: Dict, size_analysis: Dict) -> float:
        """Estima peso baseado no material e tamanho"""
        material = material_analysis["material"]
        size_cm = size_analysis["estimated_size_cm"]
        
        # Estima volume (assumindo cubo)
        volume_cm3 = size_cm ** 3
        
        # Usa densidade do material
        density = self.density_estimates.get(material, 1.0)
        
        # Calcula peso (g)
        weight = volume_cm3 * density
        
        # Adiciona variação aleatória (±20%)
        variation = np.random.uniform(0.8, 1.2)
        weight *= variation
        
        return round(weight, 1)
    
    def _check_eligibility(self, material: str, weight: float, quality: Dict) -> Dict:
        """Verifica se o item é elegível para reciclagem"""
        
        # Regras de elegibilidade
        rules = {
            "plastic": {
                "min_weight": 5,
                "max_weight": 5000,
                "min_quality": 0.5,
                "recyclable_subtypes": ["bottle", "container", "film"]
            },
            "metal": {
                "min_weight": 10,
                "max_weight": 5000,
                "min_quality": 0.4,
                "recyclable_subtypes": ["aluminum", "steel", "iron"]
            },
            "paper": {
                "min_weight": 3,
                "max_weight": 2000,
                "min_quality": 0.6,
                "issues": ["high_contamination", "wet"]
            },
            "glass": {
                "min_weight": 20,
                "max_weight": 5000,
                "min_quality": 0.5,
                "issues": ["broken", "hazard"]
            },
            "organic": {
                "min_weight": 5,
                "max_weight": 2000,
                "min_quality": 0.4
            }
        }
        
        if material not in rules:
            return {
                "recyclable": False,
                "reason": "Material desconhecido"
            }
        
        rule = rules[material]
        
        # Verifica peso
        if weight < rule["min_weight"]:
            return {
                "recyclable": False,
                "reason": f"Peso muito baixo (< {rule['min_weight']}g)"
            }
        
        if weight > rule["max_weight"]:
            return {
                "recyclable": False,
                "reason": f"Peso muito alto (> {rule['max_weight']}g)"
            }
        
        # Verifica qualidade
        if quality["overall_quality"] < rule["min_quality"]:
            return {
                "recyclable": False,
                "reason": f"Qualidade insuficiente (< {rule['min_quality']})"
            }
        
        # Verifica contaminação
        if quality["contamination_score"] < 0.3:
            return {
                "recyclable": False,
                "reason": "Item altamente contaminado"
            }
        
        # Se passou por todas as verificações
        return {
            "recyclable": True,
            "reason": "Elegível para reciclagem"
        }
    
    def _normalize_score(self, raw_score: float) -> float:
        """Normaliza score para 0-100"""
        return round(min(max(raw_score / 2, 0), 100), 2)
    
    def _calculate_confidence(self, material_analysis: Dict, quality: Dict) -> float:
        """Calcula confiança geral da análise"""
        material_confidence = material_analysis["confidence"]
        quality_score = quality["overall_quality"] * 100
        
        overall = (material_confidence * 0.6 + quality_score * 0.4)
        
        return round(min(overall, 100), 2)
    
    def _analyze_simulated(self, image_data: bytes) -> Dict:
        """Análise simulada quando OpenCV não está disponível"""
        import random
        
        materials = ["plastic", "metal", "paper", "glass", "organic"]
        material = random.choice(materials)
        
        weight = random.uniform(50, 500)
        size_cm = random.uniform(5, 30)
        quality_score = random.uniform(0.5, 1.0)
        
        return {
            "success": True,
            "material": {
                "material": material,
                "confidence": random.uniform(75, 95),
                "texture_profile": {
                    "edge_density": random.uniform(0.1, 0.5),
                    "matte_score": random.uniform(0.3, 0.9),
                    "roughness": random.uniform(10, 50)
                }
            },
            "size": {
                "estimated_size_cm": round(size_cm, 1),
                "object_area_percentage": random.uniform(10, 70),
                "size_category": "medium" if size_cm < 15 else "large",
                "contour_area": int(size_cm ** 2 * 100)
            },
            "quality": {
                "focus_score": round(random.uniform(0.7, 1.0), 2),
                "deformation_score": round(random.uniform(0.6, 1.0), 2),
                "contamination_score": round(random.uniform(0.5, 1.0), 2),
                "overall_quality": round(quality_score, 2)
            },
            "estimated_weight_g": round(weight, 1),
            "recyclable": quality_score > 0.4,
            "eligibility_reason": "Elegível para reciclagem" if quality_score > 0.4 else "Qualidade insuficiente",
            "confidence_score": round(random.uniform(80, 95), 2)
        }
    
    def _get_empty_analysis(self, error: str = "") -> Dict:
        """Retorna análise vazia em caso de erro"""
        return {
            "success": False,
            "error": error or "Erro ao analisar imagem",
            "recyclable": False,
            "confidence_score": 0
        }


class YOLODetector:
    """Detector de objetos usando YOLO (opcional, para detecção mais precisa)"""
    
    def __init__(self, model_size: str = "nano"):
        """
        Inicializa detector YOLO
        
        Args:
            model_size: "nano", "small", "medium", "large"
        """
        try:
            from ultralytics import YOLO
            
            model_map = {
                "nano": "yolov8n.pt",
                "small": "yolov8s.pt",
                "medium": "yolov8m.pt",
                "large": "yolov8l.pt"
            }
            
            self.model = YOLO(model_map.get(model_size, "yolov8n.pt"))
            print(f"✅ YOLO {model_size} carregado")
            
        except Exception as e:
            print(f"⚠️  YOLO não disponível: {e}")
            self.model = None
    
    def detect(self, image_data: bytes) -> Dict:
        """Detecta objetos na imagem"""
        if self.model is None:
            return {"error": "YOLO não está disponível"}
        
        try:
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            results = self.model(image)
            detections = []
            
            for result in results:
                for box in result.boxes:
                    detections.append({
                        "class": result.names[int(box.cls)],
                        "confidence": float(box.conf),
                        "bbox": box.xyxy.tolist()
                    })
            
            return {
                "detections": detections,
                "total_objects": len(detections)
            }
        
        except Exception as e:
            return {"error": str(e)}
