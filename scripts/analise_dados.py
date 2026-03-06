#!/usr/bin/env python3
"""
Script de análise estatística dos dados do TOTEM IA.

Gera gráficos com Matplotlib e Seaborn:
- Padrões temporais (depósitos por dia/hora)
- Distribuição de resultados (sucesso, rejeitado, etc.)
- Correlação confiança ML × peso
- Exportação CSV para análise externa

Uso:
    python scripts/analise_dados.py
    python scripts/analise_dados.py --output-dir relatorios/
"""
from __future__ import annotations

import argparse
import csv
import os
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use('Agg')  # Backend sem display para servidor
import matplotlib.pyplot as plt
import seaborn as sns

# Ajustar para encontrar o BD na raiz do projeto
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DB_PATH = PROJECT_ROOT / "totem_data.db"
OUTPUT_DIR = PROJECT_ROOT / "relatorios"


def load_data(db_path: Path) -> tuple[list[dict], list[dict]]:
    """Carrega deposits e interactions do SQLite."""
    import sqlite3
    if not db_path.exists():
        print(f"⚠️ Banco não encontrado: {db_path}")
        return [], []

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(deposits)")
    col_names = [r[1] for r in cur.fetchall()]
    cur.execute("SELECT * FROM deposits ORDER BY timestamp")
    deposits = [dict(zip(col_names, row)) for row in cur.fetchall()]

    cur.execute("PRAGMA table_info(interactions)")
    col_names = [r[1] for r in cur.fetchall()]
    cur.execute("SELECT * FROM interactions ORDER BY timestamp")
    interactions = [dict(zip(col_names, row)) for row in cur.fetchall()]

    conn.close()
    return deposits, interactions


def plot_temporal_pattern(deposits: list[dict], output_path: Path) -> None:
    """Gráfico de depósitos por dia (padrão temporal)."""
    if not deposits:
        print("⚠️ Sem dados para gráfico temporal")
        return

    dates = []
    for d in deposits:
        ts = d.get("timestamp")
        if ts is not None:
            dates.append(datetime.fromtimestamp(ts).date())

    from collections import Counter
    counts = Counter(dates)
    sorted_dates = sorted(counts.keys())
    values = [counts[d] for d in sorted_dates]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(range(len(sorted_dates)), values, color="steelblue", edgecolor="navy", alpha=0.8)
    ax.set_xticks(range(len(sorted_dates)))
    ax.set_xticklabels([d.strftime("%d/%m") for d in sorted_dates], rotation=45)
    ax.set_xlabel("Data")
    ax.set_ylabel("Número de depósitos")
    ax.set_title("Padrão temporal: depósitos por dia")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"✅ Salvo: {output_path}")


def plot_results_distribution(interactions: list[dict], output_path: Path) -> None:
    """Gráfico de distribuição de resultados (sucesso, rejeitado, etc.)."""
    if not interactions:
        print("⚠️ Sem dados para gráfico de distribuição")
        return

    from collections import Counter
    results = Counter(i.get("resultado", "desconhecido") for i in interactions)
    labels = list(results.keys())
    sizes = list(results.values())

    fig, ax = plt.subplots(figsize=(8, 8))
    colors = sns.color_palette("Set3", len(labels))
    ax.pie(sizes, labels=labels, autopct="%1.1f%%", colors=colors, startangle=90)
    ax.set_title("Distribuição de resultados das interações")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"✅ Salvo: {output_path}")


def plot_confidence_vs_weight(deposits: list[dict], output_path: Path) -> None:
    """Gráfico de dispersão: confiança ML × peso (correlação)."""
    confidences = []
    weights = []
    for d in deposits:
        c, w = d.get("ml_confidence"), d.get("weight_value")
        if c is not None and w is not None:
            confidences.append(float(c))
            weights.append(int(w))

    if len(confidences) < 2:
        print("⚠️ Dados insuficientes para gráfico de correlação")
        return

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.scatterplot(x=confidences, y=weights, ax=ax, alpha=0.7)
    ax.set_xlabel("Confiança ML")
    ax.set_ylabel("Peso (g)")
    ax.set_title("Correlação: confiança ML × peso do depósito")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"✅ Salvo: {output_path}")


def export_csv(deposits: list[dict], interactions: list[dict], output_path: Path) -> None:
    """Exporta dados para CSV."""
    if not deposits and not interactions:
        print("⚠️ Sem dados para exportar CSV")
        return

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if deposits:
            writer.writerow(["id", "timestamp", "ml_confidence", "weight_value", "weight_ok", "plastico_reciclado_g"])
            for d in deposits:
                writer.writerow([
                    d.get("id"),
                    d.get("timestamp"),
                    d.get("ml_confidence"),
                    d.get("weight_value"),
                    d.get("weight_ok"),
                    d.get("plastico_reciclado_g"),
                ])
        if interactions:
            writer.writerow([])
            writer.writerow(["id", "deposit_id", "timestamp", "resultado"])
            for i in interactions:
                writer.writerow([
                    i.get("id"),
                    i.get("deposit_id"),
                    i.get("timestamp"),
                    i.get("resultado"),
                ])
    print(f"✅ Salvo: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Análise estatística dos dados do TOTEM IA")
    parser.add_argument("--db", default=str(DB_PATH), help="Caminho do banco SQLite")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR), help="Diretório de saída dos gráficos")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    deposits, interactions = load_data(Path(args.db))
    print(f"📊 Carregados: {len(deposits)} depósitos, {len(interactions)} interações")

    plot_temporal_pattern(deposits, output_dir / "padrao_temporal.png")
    plot_results_distribution(interactions, output_dir / "distribuicao_resultados.png")
    plot_confidence_vs_weight(deposits, output_dir / "correlacao_confianca_peso.png")
    export_csv(deposits, interactions, output_dir / "dados_exportados.csv")

    print("✅ Análise concluída.")


if __name__ == "__main__":
    main()
