"""
Fine-tuning do Vision Transformer para Classificação de Tampinhas Plásticas
Dataset: color-cap (2100 imagens treino, 200 validação, 100 teste)
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from transformers import ViTForImageClassification, ViTImageProcessor, get_linear_schedule_with_warmup
from transformers import ViTImageProcessor
from PIL import Image
from pathlib import Path
import json
import logging
import numpy as np
from tqdm import tqdm
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CapDataset(Dataset):
    """Dataset customizado para tampinhas plásticas."""
    
    def __init__(self, image_dir: str, labels_dir: str, processor, class_mapping: dict = None):
        """
        Args:
            image_dir: Diretório com imagens
            labels_dir: Diretório com labels (não usados ainda, usando nome da pasta)
            processor: ViTImageProcessor
            class_mapping: Mapeamento de classe para índice
        """
        self.processor = processor
        self.image_files = sorted(Path(image_dir).glob("*.jpg")) + \
                          sorted(Path(image_dir).glob("*.jpeg")) + \
                          sorted(Path(image_dir).glob("*.png"))
        
        # Criar mapeamento de classes baseado em metadados ou usar padrão
        if class_mapping is None:
            self.class_mapping = self._get_default_classes()
        else:
            self.class_mapping = class_mapping
        
        logger.info(f"📸 Dataset carregado: {len(self.image_files)} imagens")
        logger.info(f"📋 Classes: {len(self.class_mapping)}")
    
    @staticmethod
    def _get_default_classes():
        """Retorna classes padrão."""
        return {
            "Vermelho": 0,
            "Azul": 1,
            "Verde": 2,
            "Amarelo": 3,
            "Branco": 4,
            "Preto": 5,
            "Laranja": 6,
            "Rosa": 7,
            "Roxo": 8,
            "Marrom": 9,
            "Cinza": 10,
            "Transparente": 11
        }
    
    def __len__(self):
        return len(self.image_files)
    
    def __getitem__(self, idx):
        image_path = self.image_files[idx]
        
        try:
            image = Image.open(image_path).convert("RGB")
        except Exception as e:
            logger.error(f"Erro ao carregar {image_path}: {e}")
            # Retornar imagem padrão em caso de erro
            image = Image.new('RGB', (224, 224))
        
        # Processar imagem
        encoding = self.processor(images=image, return_tensors="pt")
        
        # Para agora, usar label aleatório (será substituído por YOLO detection)
        # TODO: Integrar com detecção YOLO para extrair label da tampinha
        label = np.random.randint(0, len(self.class_mapping))
        
        return {
            "pixel_values": encoding["pixel_values"].squeeze(),
            "label": torch.tensor(label, dtype=torch.long)
        }


class CapFineTuner:
    """Fine-tuner para modelo ViT de tampinhas plásticas."""
    
    def __init__(self, model_name: str = "google/vit-base-patch16-224", 
                 num_labels: int = 12,
                 device: str = None):
        """
        Args:
            model_name: Nome do modelo base
            num_labels: Número de classes
            device: Dispositivo (cuda/cpu)
        """
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_name = model_name
        self.num_labels = num_labels
        
        logger.info(f"🚀 Inicializando fine-tuner")
        logger.info(f"   Modelo: {model_name}")
        logger.info(f"   Classes: {num_labels}")
        logger.info(f"   Dispositivo: {self.device}")
        
        # Carregar processador e modelo
        self.processor = ViTImageProcessor.from_pretrained(model_name)
        self.model = ViTForImageClassification.from_pretrained(
            model_name,
            num_labels=num_labels,
            ignore_mismatched_sizes=True
        ).to(self.device)
        
        self.training_history = {
            "train_loss": [],
            "train_accuracy": [],
            "val_loss": [],
            "val_accuracy": [],
            "learning_rates": []
        }
    
    def train(self, train_loader: DataLoader, val_loader: DataLoader,
              num_epochs: int = 10, learning_rate: float = 1e-4,
              output_dir: str = "models/cap-finetuned"):
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
        
        # Configurar otimizador
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=learning_rate)
        total_steps = len(train_loader) * num_epochs
        scheduler = get_linear_schedule_with_warmup(
            optimizer,
            num_warmup_steps=0,
            num_training_steps=total_steps
        )
        
        # Função de perda
        criterion = nn.CrossEntropyLoss()
        
        best_val_accuracy = 0.0
        patience = 3
        patience_counter = 0
        
        for epoch in range(num_epochs):
            logger.info(f"\n📅 Época {epoch + 1}/{num_epochs}")
            
            # ===== TREINO =====
            self.model.train()
            train_loss = 0.0
            train_correct = 0
            train_total = 0
            
            progress_bar = tqdm(train_loader, desc="Treino")
            for batch in progress_bar:
                pixel_values = batch["pixel_values"].to(self.device)
                labels = batch["label"].to(self.device)
                
                # Forward pass
                outputs = self.model(pixel_values=pixel_values, labels=labels)
                loss = outputs.loss
                
                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                optimizer.step()
                scheduler.step()
                
                # Métricas
                train_loss += loss.item()
                logits = outputs.logits
                predictions = torch.argmax(logits, dim=-1)
                train_correct += (predictions == labels).sum().item()
                train_total += labels.size(0)
                
                progress_bar.set_postfix({
                    "loss": f"{loss.item():.4f}",
                    "lr": f"{scheduler.get_last_lr()[0]:.2e}"
                })
            
            avg_train_loss = train_loss / len(train_loader)
            avg_train_accuracy = train_correct / train_total
            
            # ===== VALIDAÇÃO =====
            self.model.eval()
            val_loss = 0.0
            val_correct = 0
            val_total = 0
            
            with torch.no_grad():
                progress_bar = tqdm(val_loader, desc="Validação")
                for batch in progress_bar:
                    pixel_values = batch["pixel_values"].to(self.device)
                    labels = batch["label"].to(self.device)
                    
                    outputs = self.model(pixel_values=pixel_values, labels=labels)
                    loss = outputs.loss
                    
                    val_loss += loss.item()
                    logits = outputs.logits
                    predictions = torch.argmax(logits, dim=-1)
                    val_correct += (predictions == labels).sum().item()
                    val_total += labels.size(0)
            
            avg_val_loss = val_loss / len(val_loader)
            avg_val_accuracy = val_correct / val_total
            
            # ===== LOG =====
            logger.info(f"📊 Treino    - Loss: {avg_train_loss:.4f} | Acurácia: {avg_train_accuracy*100:.2f}%")
            logger.info(f"📊 Validação - Loss: {avg_val_loss:.4f} | Acurácia: {avg_val_accuracy*100:.2f}%")
            
            # Guardar histórico
            self.training_history["train_loss"].append(avg_train_loss)
            self.training_history["train_accuracy"].append(avg_train_accuracy)
            self.training_history["val_loss"].append(avg_val_loss)
            self.training_history["val_accuracy"].append(avg_val_accuracy)
            self.training_history["learning_rates"].append(scheduler.get_last_lr()[0])
            
            # Early stopping e checkpoint
            if avg_val_accuracy > best_val_accuracy:
                best_val_accuracy = avg_val_accuracy
                patience_counter = 0
                
                logger.info(f"✅ Melhor modelo encontrado! Acurácia: {best_val_accuracy*100:.2f}%")
                self._save_model(output_dir)
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    logger.info(f"⚠️  Early stopping - nenhuma melhora em {patience} épocas")
                    break
        
        logger.info(f"\n✨ Treinamento concluído!")
        return self.training_history
    
    def _save_model(self, output_dir: str):
        """Salva modelo e processador."""
        os.makedirs(output_dir, exist_ok=True)
        
        self.model.save_pretrained(output_dir)
        self.processor.save_pretrained(output_dir)
        
        # Salvar classes
        classes_mapping = {
            "Vermelho": 0,
            "Azul": 1,
            "Verde": 2,
            "Amarelo": 3,
            "Branco": 4,
            "Preto": 5,
            "Laranja": 6,
            "Rosa": 7,
            "Roxo": 8,
            "Marrom": 9,
            "Cinza": 10,
            "Transparente": 11
        }
        
        with open(os.path.join(output_dir, "classes.json"), 'w') as f:
            json.dump({v: k for k, v in classes_mapping.items()}, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 Modelo salvo em: {output_dir}")


def main():
    """Main function para treinar o modelo."""
    logger.info("🎨 Sistema de Fine-tuning de Tampinhas Plásticas")
    logger.info("=" * 60)
    
    # Configurações
    dataset_base = "datasets/color-cap"
    output_dir = "models/cap-finetuned"
    
    train_path = f"{dataset_base}/train/images"
    val_path = f"{dataset_base}/valid/images"
    
    # Verificar dataset
    if not os.path.exists(train_path):
        logger.error(f"❌ Dataset não encontrado em {train_path}")
        return
    
    # Inicializar fine-tuner
    finetuner = CapFineTuner(num_labels=12)
    
    # Carregar dados
    logger.info("\n📂 Carregando datasets...")
    processor = finetuner.processor
    
    train_dataset = CapDataset(train_path, f"{dataset_base}/train/labels", processor)
    val_dataset = CapDataset(val_path, f"{dataset_base}/valid/labels", processor)
    
    # Criar DataLoaders
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False, num_workers=0)
    
    # Treinar
    history = finetuner.train(
        train_loader=train_loader,
        val_loader=val_loader,
        num_epochs=15,
        learning_rate=1e-4,
        output_dir=output_dir
    )
    
    # Salvar histórico
    logger.info("\n💾 Salvando histórico de treinamento...")
    with open(os.path.join(output_dir, "training_history.json"), 'w') as f:
        json.dump(history, f, indent=2)
    
    logger.info(f"✅ Histórico salvo em {output_dir}/training_history.json")


if __name__ == "__main__":
    main()
