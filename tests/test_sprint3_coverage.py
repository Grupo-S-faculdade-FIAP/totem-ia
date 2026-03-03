"""
Testes focados na cobertura da demanda Sprint 3:
- Segurança admin (Bearer token)
- Relatório analítico consolidado
- Helpers de tendência e KPIs
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import numpy as np
import cv2
import base64
import time

import app as app_module
from app import app
from src.modules.sprint3_analytics import (
    build_analytics_report,
    build_daily_trend,
    is_admin_authenticated,
)


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as flask_client:
        yield flask_client


class TestSprint3Helpers:
    def test_is_admin_authenticated_sem_header(self):
        assert is_admin_authenticated('', 'admin_token') is False

    def test_is_admin_authenticated_com_token_valido_customizado(self):
        assert is_admin_authenticated('Bearer token_seguro', 'token_seguro') is True

    def test_build_daily_trend_ignora_timestamp_invalido(self):
        deposits = [
            {'timestamp': time.time()},
            {'timestamp': 'invalido'}
        ]
        trend = build_daily_trend(deposits, days=7)
        assert len(trend['labels']) == 7
        assert len(trend['values']) == 7
        assert all(isinstance(value, int) for value in trend['values'])
        assert sum(trend['values']) >= 1

    def test_build_analytics_report_com_lista_vazia(self):
        report = build_analytics_report([], [])
        assert report['kpis']['total_interactions'] == 0
        assert report['kpis']['accepted_deposits'] == 0
        assert report['kpis']['acceptance_rate_percent'] == 0.0
        assert report['interaction_results'] == {}

    def test_ensure_db_connection_cria_quando_nao_existe(self):
        with patch('app.DatabaseConnection') as mock_db_cls:
            fake_db = MagicMock()
            mock_db_cls.return_value = fake_db
            app_module.db_connection = None

            result = app_module._ensure_db_connection()

            assert result is fake_db
            fake_db.init_db.assert_called_once()

    def test_ensure_db_connection_reutiliza_existente(self):
        fake_existing = MagicMock()
        app_module.db_connection = fake_existing
        result = app_module._ensure_db_connection()
        assert result is fake_existing


class TestSprint3Endpoints:
    def test_dashboard_erro_interno_retorna_500(self, client):
        with patch('app.is_admin_authenticated', return_value=True), \
             patch('app._ensure_db_connection', side_effect=Exception('erro_forcado')):
            response = client.get('/api/admin/dashboard')

        assert response.status_code == 500
        data = response.get_json()
        assert data['success'] is False

    def test_analytics_report_erro_interno_retorna_500(self, client):
        with patch('app.is_admin_authenticated', return_value=True), \
             patch('app._ensure_db_connection', side_effect=Exception('erro_forcado')):
            response = client.get('/api/admin/analytics-report')

        assert response.status_code == 500
        data = response.get_json()
        assert data['status'] == 'erro'

    def test_debug_confirm_detection_type_invalido(self, client):
        with patch('app.MODO_DEBUG', True):
            response = client.post('/api/debug-confirm', json={
                'detection_type': 'objeto_desconhecido',
                'confidence': 0.7
            })

        assert response.status_code == 400

    def test_save_deposit_rejeita_quando_nao_tampinha(self, client):
        image = np.zeros((32, 32, 3), dtype=np.uint8)
        _, buffer = cv2.imencode('.jpg', image)
        image_b64 = base64.b64encode(buffer).decode('utf-8')

        with patch('app.image_classifier') as mock_clf:
            mock_clf.classify_image.return_value = (0, 0.1, 10.0, 'SAT_VERY_LOW')
            response = client.post('/api/save_deposit', json={
                'image': image_b64
            })

        assert response.status_code == 400
