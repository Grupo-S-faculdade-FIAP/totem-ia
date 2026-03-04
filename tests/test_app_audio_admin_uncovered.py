from __future__ import annotations

import base64
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as flask_client:
        yield flask_client


class TestSpeechErrorBranches:
    def test_get_sustainability_speech_excecao_controlada(self, client):
        with patch("app.generate_sustainability_speech", side_effect=RuntimeError("audio fail")):
            response = client.get("/api/speech/sustainability")
        assert response.status_code == 500

    def test_get_speech_info_excecao_controlada(self, client):
        with patch("app.Path", side_effect=RuntimeError("path fail")):
            response = client.get("/api/speech/info")
        assert response.status_code == 500

    def test_get_sustainability_speech_wav_sucesso(self, client, tmp_path):
        wav_file = tmp_path / "audio.wav"
        wav_file.write_bytes(b"RIFF....WAVE")
        with patch("app.generate_sustainability_speech", return_value=str(wav_file)):
            response = client.get("/api/speech/sustainability")
        assert response.status_code == 200
        assert response.headers.get("Accept-Ranges") == "bytes"

    def test_get_sustainability_speech_mp3_sucesso(self, client, tmp_path):
        mp3_file = tmp_path / "audio.mp3"
        mp3_file.write_bytes(b"ID3")
        with patch("app.generate_sustainability_speech", return_value=str(mp3_file)):
            response = client.get("/api/speech/sustainability")
        assert response.status_code == 200
        assert "audio" in response.headers.get("Content-Type", "").lower()

    def test_get_sustainability_speech_extensao_desconhecida(self, client, tmp_path):
        unknown = tmp_path / "audio.bin"
        unknown.write_bytes(b"abc")
        with patch("app.generate_sustainability_speech", return_value=str(unknown)):
            response = client.get("/api/speech/sustainability")
        assert response.status_code == 200


class TestAdminAndDebugExtraBranches:
    def test_admin_login_excecao_controlada(self, client):
        response = client.post("/api/admin/login", data="texto", content_type="text/plain")
        assert response.status_code == 500

    def test_debug_confirm_sem_json_no_debug(self, client):
        with patch("app.MODO_DEBUG", True):
            response = client.post("/api/debug-confirm", data="texto", content_type="text/plain")
        assert response.status_code == 400

    def test_debug_confirm_tampinha_com_db_contexto(self, client):
        fake_db = MagicMock()
        fake_ctx = MagicMock()
        fake_ctx.__enter__.return_value = fake_db
        fake_ctx.__exit__.return_value = None
        with patch("app.MODO_DEBUG", True), patch("app.db_connection", fake_ctx):
            response = client.post("/api/debug-confirm", json={"detection_type": "tampinha", "confidence": 0.9})
        assert response.status_code == 200
        assert fake_db.save_interaction.called

    def test_debug_confirm_nao_tampinha_com_db_contexto(self, client):
        fake_db = MagicMock()
        fake_ctx = MagicMock()
        fake_ctx.__enter__.return_value = fake_db
        fake_ctx.__exit__.return_value = None
        with patch("app.MODO_DEBUG", True), patch("app.db_connection", fake_ctx):
            response = client.post("/api/debug-confirm", json={"detection_type": "nao_tampinha", "confidence": 0.2})
        assert response.status_code == 200
        assert fake_db.save_interaction.called

    def test_debug_confirm_excecao_controlada(self, client):
        with patch("app.MODO_DEBUG", True), patch("app.float", side_effect=RuntimeError("float fail")):
            response = client.post("/api/debug-confirm", json={"detection_type": "tampinha", "confidence": "1"})
        assert response.status_code == 500

    def test_save_deposit_sem_json_retorna_400(self, client):
        response = client.post("/api/save_deposit", data="texto", content_type="text/plain")
        assert response.status_code == 400

    def test_save_deposit_imagem_none_retorna_400(self, client):
        fake_b64 = base64.b64encode(b"abc").decode("utf-8")
        with patch("app.cv2.imdecode", return_value=None):
            response = client.post("/api/save_deposit", json={"image": fake_b64})
        assert response.status_code == 400

    def test_save_deposit_excecao_controlada(self, client):
        with patch("app.base64.b64decode", side_effect=RuntimeError("b64 fail")):
            response = client.post("/api/save_deposit", json={"image": "abc"})
        assert response.status_code == 500


class TestAudioGeneratorBranches:
    def test_generate_sustainability_speech_quando_existe(self, tmp_path, monkeypatch):
        import app as app_module

        monkeypatch.chdir(tmp_path)
        target = tmp_path / "static" / "audio" / "sustainability_speech.wav"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"RIFF....WAVE")
        result = app_module.generate_sustainability_speech()
        assert result is not None
        assert result.endswith("sustainability_speech.wav")

    def test_generate_sustainability_speech_cria_placeholder(self, tmp_path, monkeypatch):
        import app as app_module

        monkeypatch.chdir(tmp_path)
        result = app_module.generate_sustainability_speech()
        assert result is not None
        assert os.path.exists(result)

    def test_generate_sustainability_speech_falha_no_wave(self, tmp_path, monkeypatch):
        import app as app_module

        monkeypatch.chdir(tmp_path)
        fake_wave = MagicMock()
        fake_wave.open.side_effect = RuntimeError("wave fail")
        with patch.dict(sys.modules, {"wave": fake_wave}):
            result = app_module.generate_sustainability_speech()
        assert result is None
