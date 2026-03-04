from __future__ import annotations

import importlib
import io
from unittest.mock import MagicMock, patch

import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as flask_client:
        yield flask_client


def _multipart_file(name: str, content: bytes = b"fake-image-content") -> dict:
    return {"file": (io.BytesIO(content), name)}


class TestBasicAuthAndStaticImage:
    def test_basic_auth_malformado_retorna_false(self):
        from app import _is_valid_basic_auth

        assert _is_valid_basic_auth("Basic ###not_base64###") is False

    def test_serve_test_image_quando_nao_existe_retorna_404(self, client):
        fake_path = MagicMock()
        fake_path.exists.return_value = False
        with patch("app.Path", return_value=fake_path):
            response = client.get("/test_tampinha.jpg")
        assert response.status_code == 404

    def test_requires_totem_auth_static_path(self):
        from app import _requires_totem_auth

        assert _requires_totem_auth("/static/app.js") is False

    def test_admin_login_page_route_retorna_html(self, client):
        response = client.get("/admin/login")
        assert response.status_code == 200

    def test_debug_image_success_path(self, client):
        with patch("app.os.path.exists", return_value=True), patch("app.os.path.isfile", return_value=True), patch(
            "app.send_file"
        ) as mock_send:
            mock_send.return_value = app.response_class(status=200)
            response = client.get("/debug-image/ok.jpg")
        assert response.status_code == 200

    def test_debug_image_exception_path(self, client):
        with patch("app.os.path.exists", side_effect=RuntimeError("boom")):
            response = client.get("/debug-image/ok.jpg")
        assert response.status_code == 500

    def test_module_reload_cobre_modo_debug_true(self, monkeypatch):
        import app as app_module

        monkeypatch.setenv("MODO_DEBUG", "true")
        importlib.reload(app_module)
        assert app_module.MODO_DEBUG is True

        monkeypatch.setenv("MODO_DEBUG", "false")
        importlib.reload(app_module)


class TestClassifyFileUploadBranches:
    def test_classify_upload_nome_vazio_retorna_400(self, client):
        data = _multipart_file("")
        response = client.post("/api/classify", data=data, content_type="multipart/form-data")
        assert response.status_code == 400

    def test_classify_upload_extensao_invalida_retorna_400(self, client):
        data = _multipart_file("arquivo.txt")
        response = client.post("/api/classify", data=data, content_type="multipart/form-data")
        assert response.status_code == 400

    def test_classify_upload_arquivo_grande_retorna_400(self, client):
        large_bytes = b"x" * (10 * 1024 * 1024 + 1)
        data = _multipart_file("grande.jpg", large_bytes)
        response = client.post("/api/classify", data=data, content_type="multipart/form-data")
        assert response.status_code == 400

    def test_classify_upload_decode_none_retorna_400(self, client):
        data = _multipart_file("ok.jpg", b"not-an-image")
        with patch("app.cv2.imdecode", return_value=None):
            response = client.post("/api/classify", data=data, content_type="multipart/form-data")
        assert response.status_code == 400
