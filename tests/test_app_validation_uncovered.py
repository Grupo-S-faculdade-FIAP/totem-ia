from __future__ import annotations

import base64
import io
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as flask_client:
        yield flask_client


def _img_bytes() -> bytes:
    img = np.zeros((16, 16, 3), dtype=np.uint8)
    import cv2

    ok, buff = cv2.imencode(".jpg", img)
    assert ok
    return bytes(buff)


class TestValidateMechanicalUncoveredBranches:
    def test_validate_mechanical_filename_vazio(self, client):
        payload = {"image": (io.BytesIO(b""), "")}
        response = client.post("/api/validate_mechanical", data=payload, content_type="multipart/form-data")
        assert response.status_code == 400

    def test_validate_mechanical_imdecode_none(self, client):
        payload = {"image": (io.BytesIO(b"abc"), "img.jpg")}
        with patch("app.cv2.imdecode", return_value=None):
            response = client.post("/api/validate_mechanical", data=payload, content_type="multipart/form-data")
        assert response.status_code == 400

    def test_validate_mechanical_pred_none_com_db_none(self, client):
        payload = {"image": (io.BytesIO(b"abc"), "img.jpg")}
        fake_img = np.zeros((8, 8, 3), dtype=np.uint8)
        with patch("app.cv2.imdecode", return_value=fake_img), patch("app.image_classifier") as mock_clf, patch(
            "app.db_connection", None
        ):
            mock_clf.classify_image.return_value = (None, None, None, "ERRO")
            response = client.post("/api/validate_mechanical", data=payload, content_type="multipart/form-data")
        assert response.status_code == 500

    def test_validate_mechanical_erro_generico_esp32_retorna_500(self, client):
        payload = {"image": (io.BytesIO(b"abc"), "img.jpg")}
        fake_img = np.zeros((8, 8, 3), dtype=np.uint8)
        with patch("app.cv2.imdecode", return_value=fake_img), patch("app.image_classifier") as mock_clf, patch(
            "app.requests.post", side_effect=RuntimeError("boom")
        ):
            mock_clf.classify_image.return_value = (1, 0.95, 120.0, "SAT_HIGH")
            response = client.post("/api/validate_mechanical", data=payload, content_type="multipart/form-data")
        assert response.status_code == 500

    def test_validate_mechanical_falha_mecanica_sem_db(self, client):
        payload = {"image": (io.BytesIO(b"abc"), "img.jpg")}
        fake_img = np.zeros((8, 8, 3), dtype=np.uint8)
        with patch("app.cv2.imdecode", return_value=fake_img), patch("app.image_classifier") as mock_clf, patch(
            "app.requests.post"
        ) as mock_post, patch("app.db_connection", None):
            mock_clf.classify_image.return_value = (1, 0.95, 120.0, "SAT_HIGH")
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"presence_detected": False, "weight_ok": False}
            mock_post.return_value = mock_resp
            response = client.post("/api/validate_mechanical", data=payload, content_type="multipart/form-data")
        assert response.status_code == 400

    def test_validate_mechanical_outer_exception_retorna_500(self, client):
        payload = {"image": (io.BytesIO(b"abc"), "img.jpg")}
        with patch("app.np.frombuffer", side_effect=RuntimeError("frombuffer fail")):
            response = client.post("/api/validate_mechanical", data=payload, content_type="multipart/form-data")
        assert response.status_code == 500

    def test_validate_mechanical_json_typeerror_cai_no_except(self, client):
        response = client.post("/api/validate-mechanical", json={"presenca": True, "peso": "abc"})
        assert response.status_code == 500

    def test_validate_mechanical_pred_none_com_db_contexto(self, client):
        payload = {"image": (io.BytesIO(b"abc"), "img.jpg")}
        fake_img = np.zeros((8, 8, 3), dtype=np.uint8)
        fake_db = MagicMock()
        fake_ctx = MagicMock()
        fake_ctx.__enter__.return_value = fake_db
        fake_ctx.__exit__.return_value = None
        with patch("app.cv2.imdecode", return_value=fake_img), patch("app.image_classifier") as mock_clf, patch(
            "app.db_connection", fake_ctx
        ):
            mock_clf.classify_image.return_value = (None, None, None, "ERRO")
            response = client.post("/api/validate_mechanical", data=payload, content_type="multipart/form-data")
        assert response.status_code == 500
        assert fake_db.save_interaction.called

    def test_validate_mechanical_nao_tampinha_com_db_contexto(self, client):
        payload = {"image": (io.BytesIO(b"abc"), "img.jpg")}
        fake_img = np.zeros((8, 8, 3), dtype=np.uint8)
        fake_db = MagicMock()
        fake_ctx = MagicMock()
        fake_ctx.__enter__.return_value = fake_db
        fake_ctx.__exit__.return_value = None
        with patch("app.cv2.imdecode", return_value=fake_img), patch("app.image_classifier") as mock_clf, patch(
            "app.db_connection", fake_ctx
        ):
            mock_clf.classify_image.return_value = (0, 0.3, 40.0, "LOW_SAT_FORCE_TAMPINHA")
            response = client.post("/api/validate_mechanical", data=payload, content_type="multipart/form-data")
        assert response.status_code == 400
        assert fake_db.save_interaction.called

    def test_validate_mechanical_nao_tampinha_com_db_none(self, client):
        payload = {"image": (io.BytesIO(b"abc"), "img.jpg")}
        fake_img = np.zeros((8, 8, 3), dtype=np.uint8)
        with patch("app.cv2.imdecode", return_value=fake_img), patch("app.image_classifier") as mock_clf, patch(
            "app.db_connection", None
        ):
            mock_clf.classify_image.return_value = (0, 0.2, 20.0, "SAT_VERY_LOW")
            response = client.post("/api/validate_mechanical", data=payload, content_type="multipart/form-data")
        assert response.status_code == 400

    def test_validate_mechanical_sucesso_com_db_contexto(self, client):
        payload = {"image": (io.BytesIO(b"abc"), "img.jpg")}
        fake_img = np.zeros((8, 8, 3), dtype=np.uint8)
        fake_db = MagicMock()
        fake_db.save_deposit_data.return_value = 123
        fake_ctx = MagicMock()
        fake_ctx.__enter__.return_value = fake_db
        fake_ctx.__exit__.return_value = None
        with patch("app.cv2.imdecode", return_value=fake_img), patch("app.image_classifier") as mock_clf, patch(
            "app.requests.post"
        ) as mock_post, patch("app.calculate_environmental_impact", return_value={"plastico_reciclado_g": 1.2}), patch(
            "app.db_connection", fake_ctx
        ):
            mock_clf.classify_image.return_value = (1, 0.95, 120.0, "SAT_HIGH")
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"presence_detected": True, "weight_ok": True, "weight_value": 2500}
            mock_post.return_value = mock_resp
            response = client.post("/api/validate_mechanical", data=payload, content_type="multipart/form-data")
        assert response.status_code == 200
        assert fake_db.save_deposit_data.called
        assert fake_db.save_interaction.called

    def test_validate_mechanical_timeout_esp32_usa_fallback(self, client):
        import requests

        payload = {"image": (io.BytesIO(b"abc"), "img.jpg")}
        fake_img = np.zeros((8, 8, 3), dtype=np.uint8)
        with patch("app.cv2.imdecode", return_value=fake_img), patch("app.image_classifier") as mock_clf, patch(
            "app.requests.post", side_effect=requests.exceptions.Timeout("t")
        ), patch("app.calculate_environmental_impact", return_value={"plastico_reciclado_g": 0.5}), patch(
            "app.db_connection", None
        ):
            mock_clf.classify_image.return_value = (1, 0.95, 120.0, "SAT_HIGH")
            response = client.post("/api/validate_mechanical", data=payload, content_type="multipart/form-data")
        assert response.status_code == 200

    def test_validate_mechanical_falha_mecanica_com_db_contexto(self, client):
        payload = {"image": (io.BytesIO(b"abc"), "img.jpg")}
        fake_img = np.zeros((8, 8, 3), dtype=np.uint8)
        fake_db = MagicMock()
        fake_ctx = MagicMock()
        fake_ctx.__enter__.return_value = fake_db
        fake_ctx.__exit__.return_value = None
        with patch("app.cv2.imdecode", return_value=fake_img), patch("app.image_classifier") as mock_clf, patch(
            "app.requests.post"
        ) as mock_post, patch("app.db_connection", fake_ctx):
            mock_clf.classify_image.return_value = (1, 0.95, 120.0, "SAT_HIGH")
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"presence_detected": False, "weight_ok": False}
            mock_post.return_value = mock_resp
            response = client.post("/api/validate_mechanical", data=payload, content_type="multipart/form-data")
        assert response.status_code == 400
        assert fake_db.save_interaction.called


class TestValidateCompleteUncoveredBranches:
    def test_validate_complete_upload_filename_vazio(self, client):
        payload = {"file": (io.BytesIO(b""), "")}
        response = client.post("/api/validate-complete", data=payload, content_type="multipart/form-data")
        assert response.status_code == 400

    def test_validate_complete_upload_extensao_invalida(self, client):
        payload = {"file": (io.BytesIO(b"abc"), "arquivo.txt")}
        response = client.post("/api/validate-complete", data=payload, content_type="multipart/form-data")
        assert response.status_code == 400

    def test_validate_complete_imagem_none(self, client):
        payload = {"file": (io.BytesIO(b"abc"), "ok.jpg")}
        with patch("app.cv2.imdecode", return_value=None):
            response = client.post("/api/validate-complete", data=payload, content_type="multipart/form-data")
        assert response.status_code == 400

    def test_validate_complete_pred_none_com_db_contexto(self, client):
        img_bytes = _img_bytes()
        payload = {"file": (io.BytesIO(img_bytes), "ok.jpg")}
        fake_db = MagicMock()
        fake_ctx = MagicMock()
        fake_ctx.__enter__.return_value = fake_db
        fake_ctx.__exit__.return_value = None
        with patch("app.image_classifier") as mock_clf, patch("app.db_connection", fake_ctx):
            mock_clf.classify_image.return_value = (None, None, None, "ERRO")
            response = client.post("/api/validate-complete", data=payload, content_type="multipart/form-data")
        assert response.status_code == 500
        assert fake_db.save_interaction.called

    def test_validate_complete_nao_tampinha_com_db_contexto(self, client):
        img_bytes = _img_bytes()
        payload = {"file": (io.BytesIO(img_bytes), "ok.jpg")}
        fake_db = MagicMock()
        fake_ctx = MagicMock()
        fake_ctx.__enter__.return_value = fake_db
        fake_ctx.__exit__.return_value = None
        with patch("app.image_classifier") as mock_clf, patch("app.db_connection", fake_ctx):
            mock_clf.classify_image.return_value = (0, 0.8, 90.0, "NORMAL_SAT_TAMPINHA")
            response = client.post("/api/validate-complete", data=payload, content_type="multipart/form-data")
        assert response.status_code == 200
        assert fake_db.save_interaction.called

    def test_validate_complete_erro_esp32_com_db_contexto(self, client):
        img_bytes = _img_bytes()
        payload = {"image": f"data:image/jpeg;base64,{base64.b64encode(img_bytes).decode('utf-8')}"}
        fake_db = MagicMock()
        fake_ctx = MagicMock()
        fake_ctx.__enter__.return_value = fake_db
        fake_ctx.__exit__.return_value = None
        with patch("app.image_classifier") as mock_clf, patch("app.check_esp32_mechanical", return_value=None), patch(
            "app.db_connection", fake_ctx
        ):
            mock_clf.classify_image.return_value = (1, 0.95, 120.0, "SAT_HIGH")
            response = client.post("/api/validate-complete", json=payload)
        assert response.status_code == 500
        assert fake_db.save_interaction.called

    def test_validate_complete_sucesso_com_db_none(self, client):
        img_bytes = _img_bytes()
        payload = {"image": f"data:image/jpeg;base64,{base64.b64encode(img_bytes).decode('utf-8')}"}
        with patch("app.image_classifier") as mock_clf, patch("app.get_esp32_sensors", return_value=None), patch(
            "app.check_esp32_mechanical", return_value={"ok": True}
        ), patch("app.confirm_esp32_detection"), patch("app.db_connection", None):
            mock_clf.classify_image.return_value = (1, 0.95, 120.0, "SAT_HIGH")
            response = client.post("/api/validate-complete", json=payload)
        assert response.status_code == 200

    def test_validate_complete_excecao_geral(self, client):
        with patch("app.base64.b64decode", side_effect=RuntimeError("boom")):
            response = client.post("/api/validate-complete", json={"image": "abc"})
        assert response.status_code == 500

    def test_validate_complete_sem_payload_json_ou_file(self, client):
        response = client.post("/api/validate-complete", data="x", content_type="text/plain")
        assert response.status_code == 400

    def test_validate_complete_pred_none_com_db_none(self, client):
        img_bytes = _img_bytes()
        payload = {"image": f"data:image/jpeg;base64,{base64.b64encode(img_bytes).decode('utf-8')}"}
        with patch("app.image_classifier") as mock_clf, patch("app.db_connection", None):
            mock_clf.classify_image.return_value = (None, None, None, "ERRO")
            response = client.post("/api/validate-complete", json=payload)
        assert response.status_code == 500

    def test_validate_complete_json_com_presenca_e_peso_explicitos(self, client):
        img_bytes = _img_bytes()
        payload = {
            "image": f"data:image/jpeg;base64,{base64.b64encode(img_bytes).decode('utf-8')}",
            "presenca": True,
            "peso": 2600,
        }
        with patch("app.image_classifier") as mock_clf, patch("app.check_esp32_mechanical", return_value={"ok": True}), patch(
            "app.confirm_esp32_detection"
        ), patch("app.db_connection", None):
            mock_clf.classify_image.return_value = (1, 0.95, 120.0, "SAT_HIGH")
            response = client.post("/api/validate-complete", json=payload)
        assert response.status_code == 200

    def test_validate_complete_file_upload_com_sensores_none(self, client):
        img_bytes = _img_bytes()
        payload = {"file": (io.BytesIO(img_bytes), "ok.jpg")}
        with patch("app.image_classifier") as mock_clf, patch("app.get_esp32_sensors", return_value=None), patch(
            "app.check_esp32_mechanical", return_value={"ok": True}
        ), patch("app.confirm_esp32_detection"), patch("app.db_connection", None):
            mock_clf.classify_image.return_value = (1, 0.95, 120.0, "SAT_HIGH")
            response = client.post("/api/validate-complete", data=payload, content_type="multipart/form-data")
        assert response.status_code == 200

    def test_validate_complete_file_upload_com_sensores_presentes(self, client):
        img_bytes = _img_bytes()
        payload = {"file": (io.BytesIO(img_bytes), "ok.jpg")}
        with patch("app.image_classifier") as mock_clf, patch(
            "app.get_esp32_sensors", return_value={"presenca": True, "peso": 2600}
        ), patch("app.check_esp32_mechanical", return_value={"ok": True}), patch("app.confirm_esp32_detection"), patch(
            "app.db_connection", None
        ):
            mock_clf.classify_image.return_value = (1, 0.95, 120.0, "SAT_HIGH")
            response = client.post("/api/validate-complete", data=payload, content_type="multipart/form-data")
        assert response.status_code == 200

    def test_validate_complete_erro_esp32_com_db_none(self, client):
        img_bytes = _img_bytes()
        payload = {"image": f"data:image/jpeg;base64,{base64.b64encode(img_bytes).decode('utf-8')}"}
        with patch("app.image_classifier") as mock_clf, patch("app.check_esp32_mechanical", return_value=None), patch(
            "app.db_connection", None
        ):
            mock_clf.classify_image.return_value = (1, 0.95, 120.0, "SAT_HIGH")
            response = client.post("/api/validate-complete", json=payload)
        assert response.status_code == 500

    def test_validate_complete_sucesso_com_db_contexto(self, client):
        img_bytes = _img_bytes()
        payload = {"image": f"data:image/jpeg;base64,{base64.b64encode(img_bytes).decode('utf-8')}"}
        fake_db = MagicMock()
        fake_ctx = MagicMock()
        fake_ctx.__enter__.return_value = fake_db
        fake_ctx.__exit__.return_value = None
        with patch("app.image_classifier") as mock_clf, patch("app.check_esp32_mechanical", return_value={"ok": True}), patch(
            "app.confirm_esp32_detection"
        ), patch("app.db_connection", fake_ctx):
            mock_clf.classify_image.return_value = (1, 0.95, 120.0, "SAT_HIGH")
            response = client.post("/api/validate-complete", json=payload)
        assert response.status_code == 200
        assert fake_db.save_deposit_data.called
        assert fake_db.save_interaction.called
