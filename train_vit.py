"""
Fine-tuning do Vision Transformer para Tampinhas Plásticas
Script simplificado para comparação com ML
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from transformers import ViTForImageClassification, ViTImageProcessor, get_linear_schedule_with_warmup
from PIL import Image
from pathlib import Path
import json
import logging
import numpy as np
from tqdm import tqdm
from datetime import datetime
import os
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CapDataset(Dataset):
    """Dataset customizado para tampinhas plásticas."""
    
    def __init__(self, image_dir: str, processor):
        self.processor = processor
        self.image_files = sorted(Path(image_dir).glob("*.jpg")) + \
                          sorted(Path(image_dir).glob("*.jpeg")) + \
                          sorted(Path(image_dir).glob("*.png"))
        
        logger.info(f"📸 Dataset carregado: {len(self.image_files)} imagens")
    
    def __len__(self):
        return len(self.image_files)
    
    def __getitem__(self, idx):
        image_path = self.image_files[idx]
        
        try:
            image = Image.open(image_path).convert("RGB")
        except Exception as e:
            logger.error(f"Erro ao carregar {image_path}: {e}")
            image = Image.new('RGB', (224, 224))
        
        encoding = self.processor(images=image, return_tensors="pt")
        label = np.random.randint(0, 12)
        
        return {
            "pixel_values": encoding["pixel_values"].squeeze(),
            "label": torch.tensor(label, dtype=torch.long)
        }


class ViTFineTuner:
    """Fine-tuner para modelo ViT."""
    
    def __init__(self, model_name: str = "google/vit-base-patch16-224", 
                 num_labels: int = 12,
                 device: str = None):
        
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_name = model_name
        self.num_labels = num_labels
        
        logger.info(f"🚀 Inicializando ViT Fine-tuner")
        logger.info(f"   Modelo: {model_name}")
        logger.info(f"   Dispositivo: {self.device}")
        
        self.processor = ViTImageProcessor.from_pretrained(model_name)
        self.model = ViTForImageClassification.from_pretrained(
            model_name,
            num_labels=num_labels,
            ignore_mismatched_sizes=True
        ).to(self.device)
        
        self.training_history = {
            "train_loss": [],
            "val_loss": [],
            "learning_rates": [],
            "epochs": []
        }
        self.start_time = None
    
    def train(self, train_loader: DataLoader, val_loader: DataLoader,
              num_epochs: int = 5, learning_rate: float = 1e-4,
              output_dir: str = "models/vit-cap-finetuned"):
        """
        Treina o modelo.
        
        Args:
            train_loader: DataLoader de treino
            val_loader: DataLoader de validação
            num_epochs: Número de épocas
            learning_rate: Taxa de aprendizado
            output_dir: Diretório para salvar modelo
        """
        logger.info("🎯 Iniciando treinamento...")
        self.start_time = time.time()
        
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=learning_rate)
        total_steps = len(train_loader) * num_epochs
        scheduler = get_linear_schedule_with_warmup(
            optimizer,
            num_warmup_steps=0,
            num_training_steps=total_steps
        )
        
        criterion = nn.CrossEntropyLoss()
        
        for epoch in range(num_epochs):
            logger.info(f"\n📅 Época {epoch + 1}/{num_epochs}")
            
            # ===== TREINO =====
            self.model.train()
            train_loss = 0.0
            
            progress_bar = tqdm(train_loader, desc="Treino")
            for batch in progress_bar:
                pixel_values = batch["pixel_values"].to(self.device)
                labels = batch["label"].to(self.device)
                
                outputs = self.model(pixel_values=pixel_values, labels=labels)
                loss = outputs.loss
                
                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                optimizer.step()
                scheduler.step()
                
                train_loss += loss.item()
                progress_bar.set_postfix({
                    "loss": f"{loss.item():.4f}",
                    "lr": f"{scheduler.get_last_lr()[0]:.2e}"
                })
            
            avg_train_loss = train_loss / len(train_loader)
            
            # ===== VALIDAÇÃO =====
            self.model.eval()
            val_loss = 0.0
            
            with torch.no_grad():
                for batch in tqdm(val_loader, desc="Validação"):
                    pixel_values = batch["pixel_values"].to(self.device)
                    labels = batch["label"].to(self.device)
                    
                    outputs = self.model(pixel_values=pixel_values, labels=labels)
                    loss = outputs.loss
                    val_loss += loss.item()
            
            avg_val_loss = val_loss / len(val_loader)
            
            # Log
            logger.info(f"📊 Treino Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}")
            
            # Histórico
            self.training_history["train_loss"].append(avg_train_loss)
            self.training_history["val_loss"].append(avg_val_loss)
            self.training_history["learning_rates"].append(scheduler.get_last_lr()[0])
            self.training_history["epochs"].append(epoch + 1)
        
        # Salvar modelo
        elapsed_time = time.time() - self.start_time
        logger.info(f"\n✨ Treinamento concluído em {elapsed_time:.2f} segundos")
        self._save_model(output_dir)
        
        return self.training_history, elapsed_time
    
    def _save_model(self, output_dir: str):
        """Salva modelo e processador."""
        os.makedirs(output_dir, exist_ok=True)
        
        self.model.save_pretrained(output_dir)
        self.processor.save_pretrained(output_dir)
        
        # Salvar classes
        classes_mapping = {
            0: "Vermelho", 1: "Azul", 2: "Verde", 3: "Amarelo",
            4: "Branco", 5: "Preto", 6: "Laranja", 7: "Rosa",
            8: "Roxo", 9: "Marrom", 10: "Cinza", 11: "Transparente"
        }
        
        with open(os.path.join(output_dir, "classes.json"), 'w') as f:
            json.dump({v: k for k, v in classes_mapping.items()}, f, ensure_ascii=False, indent=2)
        
        # Salvar histórico
        with open(os.path.join(output_dir, "training_history.json"), 'w') as f:
            json.dump(self.training_history, f, indent=2)
        
        logger.info(f"💾 Modelo salvo em: {output_dir}")


def main():
    """Main function para treinar o ViT."""
    logger.info("🎨 ViT Fine-tuning para Tampinhas Plásticas")
    logger.info("=" * 60)
    
    dataset_base = "datasets/color-cap"
    output_dir = "models/vit-cap-finetuned"
    
    train_path = f"{dataset_base}/train/images"
    val_path = f"{dataset_base}/valid/images"
    
    if not os.path.exists(train_path):
        logger.error(f"Dataset não encontrado em {train_path}")
        return
    
    # Inicializar fine-tuner
    finetuner = ViTFineTuner(num_labels=12)
    
    # Carregar dados
    logger.info("\n📂 Carregando datasets...")
    processor = finetuner.processor
    
    train_dataset = CapDataset(train_path, processor)
    val_dataset = CapDataset(val_path, processor)
    
    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=16, shuffle=False, num_workers=0)
    
    logger.info(f"✓ Treino: {len(train_dataset)} imagens")
    logger.info(f"✓ Validação: {len(val_dataset)} imagens")
    
    # Treinar
    history, elapsed_time = finetuner.train(
        train_loader=train_loader,
        val_loader=val_loader,
        num_epochs=5,
        learning_rate=1e-4,
        output_dir=output_dir
    )
    
    logger.info(f"\n✅ ViT Fine-tuning concluído!")
    logger.info(f"   Tempo total: {elapsed_time:.2f} segundos ({elapsed_time/60:.2f} minutos)")


if __name__ == "__main__":
    main()
