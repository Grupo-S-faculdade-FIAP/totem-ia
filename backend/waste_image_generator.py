"""
Gerador de Imagens Realistas de Resíduos
Cria imagens de teste para validação do sistema
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import random
from typing import List, Tuple


class WasteImageGenerator:
    """Gera imagens realistas de resíduos para testes"""
    
    def __init__(self, width: int = 640, height: int = 480):
        self.width = width
        self.height = height
        
        # Cores HSV para diferentes materiais
        self.material_colors = {
            "plastic": {
                "colors": [(100, 150, 150), (120, 200, 200)],  # Ciano/Azul claro
                "transparency": 0.6
            },
            "metal": {
                "colors": [(50, 30, 200), (100, 50, 200)],  # Cinza/Prata
                "transparency": 0.0
            },
            "paper": {
                "colors": [(25, 100, 200), (35, 150, 220)],  # Marrom/Bege
                "transparency": 0.0
            },
            "glass": {
                "colors": [(0, 0, 200), (10, 30, 240)],  # Transparente/Claro
                "transparency": 0.8
            },
            "organic": {
                "colors": [(15, 100, 100), (25, 150, 120)],  # Verde/Marrom
                "transparency": 0.2
            }
        }
        
        print("✅ Gerador de imagens inicializado")
    
    def generate_waste_image(self, material: str, style: str = "realistic") -> np.ndarray:
        """
        Gera uma imagem de resíduo
        
        Args:
            material: Tipo de material (plastic, metal, paper, glass, organic)
            style: "realistic", "simple", "textured"
        
        Returns:
            Imagem como numpy array (BGR)
        """
        # Cria fundo
        image = np.ones((self.height, self.width, 3), dtype=np.uint8) * 230
        
        if style == "realistic":
            return self._generate_realistic(image, material)
        elif style == "textured":
            return self._generate_textured(image, material)
        else:
            return self._generate_simple(image, material)
    
    def _generate_realistic(self, image: np.ndarray, material: str) -> np.ndarray:
        """Gera imagem realista com sombras e textura"""
        
        # Define dimensões do objeto
        obj_width = random.randint(150, 350)
        obj_height = random.randint(150, 350)
        x_start = (self.width - obj_width) // 2 + random.randint(-50, 50)
        y_start = (self.height - obj_height) // 2 + random.randint(-50, 50)
        
        # Cores do material
        colors = self.material_colors.get(material, {}).get("colors", [(128, 128, 128)])
        base_color = random.choice(colors)
        
        # Desenha objeto com gradiente
        for i in range(obj_height):
            alpha = i / obj_height
            # Cria gradiente (mais escuro em cima)
            color_variation = int(base_color[2] * (0.7 + 0.3 * alpha))
            color = (base_color[0], base_color[1], color_variation)
            
            cv2.line(
                image,
                (x_start, y_start + i),
                (x_start + obj_width, y_start + i),
                color,
                1
            )
        
        # Adiciona textura/ruído
        self._add_texture(image, material, x_start, y_start, obj_width, obj_height)
        
        # Adiciona sombra
        self._add_shadow(image, x_start, y_start, obj_width, obj_height)
        
        # Adiciona reflexo (se vidro)
        if material == "glass":
            self._add_reflection(image, x_start, y_start, obj_width, obj_height)
        
        return image
    
    def _generate_textured(self, image: np.ndarray, material: str) -> np.ndarray:
        """Gera imagem com texturas detalhadas"""
        
        # Aplica ruído de Perlin para textura realista
        x, y = np.meshgrid(np.linspace(0, 4, self.width), np.linspace(0, 4, self.height))
        
        # Simula Perlin noise (aproximação com seno)
        noise = np.sin(x) * np.cos(y)
        noise = ((noise + 1) / 2 * 255).astype(np.uint8)
        
        # Define dimensões do objeto
        obj_width = random.randint(150, 350)
        obj_height = random.randint(150, 350)
        x_start = (self.width - obj_width) // 2
        y_start = (self.height - obj_height) // 2
        
        # Cores
        base_color = random.choice(self.material_colors.get(material, {}).get("colors", [(128, 128, 128)]))
        
        # Aplica textura na região do objeto
        for y in range(y_start, min(y_start + obj_height, self.height)):
            for x in range(x_start, min(x_start + obj_width, self.width)):
                texture_intensity = noise[y, x] / 255.0
                
                # Modula cor com textura
                b = int(base_color[0] * (0.7 + 0.3 * texture_intensity))
                g = int(base_color[1] * (0.7 + 0.3 * texture_intensity))
                r = int(base_color[2] * (0.7 + 0.3 * texture_intensity))
                
                image[y, x] = (b, g, r)
        
        # Desenha contorno
        cv2.rectangle(image, (x_start, y_start), (x_start + obj_width, y_start + obj_height), base_color, 2)
        
        return image
    
    def _generate_simple(self, image: np.ndarray, material: str) -> np.ndarray:
        """Gera imagem simples (para testes rápidos)"""
        
        # Define dimensões
        obj_width = random.randint(100, 250)
        obj_height = random.randint(100, 250)
        x_start = (self.width - obj_width) // 2
        y_start = (self.height - obj_height) // 2
        
        # Cores
        base_color = random.choice(self.material_colors.get(material, {}).get("colors", [(128, 128, 128)]))
        
        # Desenha retângulo simples
        cv2.rectangle(image, (x_start, y_start), (x_start + obj_width, y_start + obj_height), base_color, -1)
        
        # Adiciona contorno
        cv2.rectangle(image, (x_start, y_start), (x_start + obj_width, y_start + obj_height), (0, 0, 0), 2)
        
        return image
    
    def _add_texture(self, image: np.ndarray, material: str, x: int, y: int, w: int, h: int):
        """Adiciona textura ao objeto"""
        
        if material == "paper":
            # Textura de papel (linhas/ondulações)
            for i in range(y, min(y + h, self.height)):
                if random.random() > 0.95:
                    cv2.line(image, (x, i), (x + w, i), (200, 190, 180), 1)
        
        elif material == "metal":
            # Reflexos metálicos
            for i in range(3):
                offset = random.randint(0, w // 4)
                cv2.line(image, (x + offset, y), (x + offset, y + h), (255, 255, 255), 1)
        
        elif material == "organic":
            # Textura irregular
            points = []
            for i in range(10):
                px = x + random.randint(0, w)
                py = y + random.randint(0, h)
                points.append((px, py))
            
            if len(points) > 2:
                for i in range(len(points) - 1):
                    cv2.line(image, points[i], points[i + 1], (100, 80, 60), 1)
    
    def _add_shadow(self, image: np.ndarray, x: int, y: int, w: int, h: int):
        """Adiciona sombra sob o objeto"""
        
        # Sombra abaixo
        shadow_y = y + h + 5
        shadow_height = 30
        
        if shadow_y + shadow_height < self.height:
            for i in range(shadow_height):
                alpha = 1.0 - (i / shadow_height)
                color = int(150 * alpha)
                
                cv2.line(
                    image,
                    (x, shadow_y + i),
                    (x + w, shadow_y + i),
                    (color, color, color),
                    2
                )
    
    def _add_reflection(self, image: np.ndarray, x: int, y: int, w: int, h: int):
        """Adiciona reflexo de vidro"""
        
        # Reflexo diagonal
        ref_start_x = x + w // 4
        ref_start_y = y + 10
        ref_width = w // 6
        ref_height = h // 3
        
        cv2.ellipse(
            image,
            (ref_start_x, ref_start_y),
            (ref_width, ref_height),
            0,
            0,
            360,
            (255, 255, 255),
            2
        )
    
    def generate_batch(self, materials: List[str], count: int = 5) -> List[Tuple[np.ndarray, str]]:
        """Gera lote de imagens"""
        images = []
        
        for _ in range(count):
            material = random.choice(materials)
            style = random.choice(["realistic", "textured", "simple"])
            
            image = self.generate_waste_image(material, style)
            images.append((image, material))
        
        return images
    
    def save_image(self, image: np.ndarray, filename: str):
        """Salva imagem em arquivo"""
        cv2.imwrite(filename, image)
    
    def to_bytes(self, image: np.ndarray, format: str = "jpg") -> bytes:
        """Converte imagem para bytes"""
        success, encoded = cv2.imencode(f".{format}", image)
        
        if success:
            return encoded.tobytes()
        return None


class AugmentedImageGenerator(WasteImageGenerator):
    """Gera versões aumentadas de imagens para treino"""
    
    def augment_image(self, image: np.ndarray, transformations: List[str] = None) -> np.ndarray:
        """
        Aplica transformações de augmentação
        
        Args:
            image: Imagem original
            transformations: Lista de transformações a aplicar
        
        Returns:
            Imagem augmentada
        """
        if transformations is None:
            transformations = ["rotate", "brightness", "blur"]
        
        result = image.copy()
        
        for transform in transformations:
            if transform == "rotate":
                result = self._rotate(result)
            elif transform == "brightness":
                result = self._adjust_brightness(result)
            elif transform == "blur":
                result = self._add_blur(result)
            elif transform == "noise":
                result = self._add_noise(result)
            elif transform == "flip":
                result = self._flip(result)
        
        return result
    
    def _rotate(self, image: np.ndarray, angle: int = None) -> np.ndarray:
        """Rotaciona imagem"""
        if angle is None:
            angle = random.randint(-30, 30)
        
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        return cv2.warpAffine(image, matrix, (w, h), borderValue=(230, 230, 230))
    
    def _adjust_brightness(self, image: np.ndarray, factor: float = None) -> np.ndarray:
        """Ajusta brilho"""
        if factor is None:
            factor = random.uniform(0.7, 1.3)
        
        image_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
        image_hsv[:, :, 2] = image_hsv[:, :, 2] * factor
        image_hsv[:, :, 2] = np.clip(image_hsv[:, :, 2], 0, 255)
        
        return cv2.cvtColor(image_hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    
    def _add_blur(self, image: np.ndarray, kernel: int = None) -> np.ndarray:
        """Adiciona blur gaussiano"""
        if kernel is None:
            kernel = random.choice([3, 5, 7])
        
        return cv2.GaussianBlur(image, (kernel, kernel), 0)
    
    def _add_noise(self, image: np.ndarray, intensity: float = 0.02) -> np.ndarray:
        """Adiciona ruído gaussiano"""
        noise = np.random.normal(0, intensity * 255, image.shape)
        
        return np.clip(image.astype(np.float32) + noise, 0, 255).astype(np.uint8)
    
    def _flip(self, image: np.ndarray, direction: str = None) -> np.ndarray:
        """Inverte imagem"""
        if direction is None:
            direction = random.choice(["horizontal", "vertical"])
        
        if direction == "horizontal":
            return cv2.flip(image, 1)
        else:
            return cv2.flip(image, 0)
