from __future__ import annotations

from datetime import datetime, timedelta


def is_admin_authenticated(auth_header: str, expected_token: str) -> bool:
    """Valida token Bearer em header Authorization."""
    if not auth_header or not auth_header.startswith('Bearer '):
        return False
    token = auth_header.split(' ', 1)[1].strip()
    return token == expected_token


def build_daily_trend(deposits: list[dict], days: int = 7) -> dict[str, list]:
    """Monta série diária real baseada no timestamp dos depósitos."""
    today = datetime.now().date()
    date_buckets = {today - timedelta(days=i): 0 for i in range(days)}

    for deposit in deposits:
        timestamp = deposit.get('timestamp')
        if isinstance(timestamp, (int, float)):
            deposit_date = datetime.fromtimestamp(timestamp).date()
            if deposit_date in date_buckets:
                date_buckets[deposit_date] += 1

    ordered_dates = [today - timedelta(days=i) for i in range(days - 1, -1, -1)]
    return {
        'labels': [day.strftime('%a') for day in ordered_dates],
        'values': [date_buckets[day] for day in ordered_dates]
    }


def build_analytics_report(deposits: list[dict], interactions: list[dict]) -> dict:
    """Consolida métricas de uso e impacto para relatório analítico."""
    total_interactions = len(interactions)
    aceitas = len(deposits)
    rejeitadas = max(total_interactions - aceitas, 0)

    confidence_values = [
        float(deposit['ml_confidence'])
        for deposit in deposits
        if deposit.get('ml_confidence') is not None
    ]
    weight_values = [
        float(deposit['weight_value'])
        for deposit in deposits
        if deposit.get('weight_value') is not None
    ]
    total_weight_grams = sum(weight_values)

    results_distribution: dict[str, int] = {}
    for interaction in interactions:
        result_name = str(interaction.get('resultado', 'desconhecido'))
        results_distribution[result_name] = results_distribution.get(result_name, 0) + 1

    return {
        'kpis': {
            'total_interactions': total_interactions,
            'accepted_deposits': aceitas,
            'rejected_or_failed': rejeitadas,
            'acceptance_rate_percent': round((aceitas / total_interactions) * 100, 2) if total_interactions else 0.0,
            'avg_ml_confidence': round(sum(confidence_values) / len(confidence_values), 4) if confidence_values else 0.0,
            'avg_weight_grams': round(sum(weight_values) / len(weight_values), 2) if weight_values else 0.0,
            'total_recycled_kg': round(total_weight_grams / 1000.0, 3)
        },
        'trend_7d': build_daily_trend(deposits, days=7),
        'interaction_results': results_distribution,
        'generated_at': datetime.now().isoformat()
    }
