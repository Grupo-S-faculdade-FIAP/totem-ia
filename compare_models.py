"""
Comparação entre ViT e Random Forest para Tampinhas Plásticas
Análise de benchmarking dos dois modelos
"""

import os
import json
import logging
import numpy as np
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_metrics(model_name: str, model_dir: str) -> dict:
    """Carrega métricas de um modelo treinado."""
    metrics_file = os.path.join(model_dir, "metrics.json")
    
    if not os.path.exists(metrics_file):
        logger.warning(f"Arquivo de métricas não encontrado: {metrics_file}")
        return {}
    
    with open(metrics_file, 'r') as f:
        metrics = json.load(f)
    
    return metrics


def generate_comparison_report(ml_metrics: dict, vit_metrics: dict) -> str:
    """Gera relatório de comparação formatado."""
    
    report = []
    report.append("=" * 80)
    report.append("🏆 COMPARAÇÃO DE MODELOS: ViT vs Random Forest")
    report.append("=" * 80)
    report.append("")
    
    # Análise de Teste
    report.append("📊 RESULTADOS DE TESTE")
    report.append("-" * 80)
    report.append("")
    
    if "test" in ml_metrics and "test" in vit_metrics:
        ml_test = ml_metrics["test"]
        vit_test = vit_metrics.get("test", {})
        
        # Criar tabela comparativa
        report.append(f"{'Métrica':<20} {'Random Forest':<20} {'ViT':<20} {'Vencedor':<15}")
        report.append("-" * 75)
        
        metrics_to_compare = ["accuracy", "precision", "recall", "f1_score"]
        
        for metric in metrics_to_compare:
            ml_val = ml_test.get(metric, 0)
            vit_val = vit_test.get(metric, 0)
            
            if isinstance(ml_val, (int, float)) and isinstance(vit_val, (int, float)):
                winner = "✓ ViT" if vit_val > ml_val else "✓ RF" if ml_val > vit_val else "Empate"
                report.append(f"{metric:<20} {ml_val:<20.4f} {vit_val:<20.4f} {winner:<15}")
        
        report.append("")
    
    # Análise de Tempo
    report.append("⏱️  ANÁLISE DE TEMPO DE TREINAMENTO")
    report.append("-" * 80)
    report.append("")
    
    ml_time = ml_metrics.get("test", {}).get("training_time", 0)
    vit_time = vit_metrics.get("training_time", 0)
    
    if ml_time > 0 and vit_time > 0:
        speedup = vit_time / ml_time
        report.append(f"Random Forest:  {ml_time:.2f} segundos")
        report.append(f"ViT:            {vit_time:.2f} segundos ({vit_time/60:.2f} minutos)")
        report.append(f"Diferença:      {speedup:.1f}x mais rápido (RF)")
        report.append("")
    
    # Recomendações
    report.append("💡 RECOMENDAÇÕES")
    report.append("-" * 80)
    report.append("")
    
    ml_accuracy = ml_test.get("accuracy", 0) if "test" in ml_metrics else 0
    vit_accuracy = vit_test.get("accuracy", 0) if "test" in vit_metrics else 0
    
    if ml_accuracy > 0.9 and vit_accuracy > 0.9:
        report.append("✓ Ambos os modelos têm ótimo desempenho (>90%)")
        report.append("  - Use Random Forest para deployment rápido e leve")
        report.append("  - Use ViT se precisar de melhor generalização em dados novos")
    elif ml_accuracy > vit_accuracy:
        report.append("✓ Random Forest é SUPERIOR neste dataset")
        report.append("  - Recomendado para produção (mais rápido e preciso)")
        report.append("  - Dataset pode não se beneficiar de deep learning")
    else:
        report.append("✓ ViT é SUPERIOR neste dataset")
        report.append("  - Recomendado para aplicações que exigem melhor generalização")
        report.append("  - Pode se beneficiar de mais dados ou fine-tuning extra")
    
    report.append("")
    report.append("=" * 80)
    report.append(f"Relatório gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 80)
    
    return "\n".join(report)


def main():
    """Função principal para gerar comparação."""
    logger.info("🏆 Comparação de Modelos")
    logger.info("=" * 60)
    
    ml_dir = "models/ml-cap-classifier"
    vit_dir = "models/vit-cap-finetuned"
    
    # Verificar se modelos foram treinados
    if not os.path.exists(ml_dir) or not os.path.exists(vit_dir):
        logger.error("❌ Ambos os modelos precisam ser treinados primeiro!")
        logger.info(f"   Execute: python train_ml.py")
        logger.info(f"   Execute: python train_vit.py")
        return
    
    # Carregar métricas
    logger.info("\n📂 Carregando métricas...")
    ml_metrics = load_metrics("Random Forest", ml_dir)
    vit_metrics = load_metrics("ViT", vit_dir)
    
    if not ml_metrics or not vit_metrics:
        logger.error("❌ Não conseguiu carregar métricas dos modelos")
        return
    
    # Gerar relatório
    report = generate_comparison_report(ml_metrics, vit_metrics)
    
    # Exibir
    print("\n" + report)
    
    # Salvar relatório
    report_file = "COMPARISON_REPORT.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"\n💾 Relatório salvo em: {report_file}")


if __name__ == "__main__":
    main()
