from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.e2e


def _totem_basic_auth_headers() -> dict[str, str]:
    """Retorna header Basic Auth para páginas protegidas do totem."""
    token = base64.b64encode(b"aluno:fiap2026").decode("utf-8")
    return {"Authorization": f"Basic {token}"}


def _load_test_image_base64() -> str:
    image_path = Path("test_tampinha.jpg")
    assert image_path.exists(), "Imagem de teste não encontrada: test_tampinha.jpg"
    return base64.b64encode(image_path.read_bytes()).decode("utf-8")


def _admin_login(page, app_server: str, username: str = "admin", password: str = "admin123"):
    return page.request.post(
        f"{app_server}/api/admin/login",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"username": username, "password": password}),
    )


@pytest.mark.parametrize(
    "route",
    [
        "/",
        "/admin",
        "/admin/dashboard",
        "/totem_intro.html",
        "/totem_v2.html",
        "/esp32_simulator.html",
        "/processing",
        "/finalization",
        "/rewards",
        "/test",
    ],
)
def test_public_pages_available(page, app_server, route):
    """Páginas públicas/base devem responder com conteúdo HTML."""
    response = page.request.get(f"{app_server}{route}", headers=_totem_basic_auth_headers())
    assert response.ok
    assert "text/html" in response.headers.get("content-type", "")


def test_home_page_loads(page, app_server):
    """Smoke test: home deve carregar e conter contexto do totem."""
    page.context.set_extra_http_headers(_totem_basic_auth_headers())
    page.goto(f"{app_server}/", wait_until="domcontentloaded")

    title = page.title()
    body_text = page.locator("body").inner_text()

    assert title
    assert "TOTEM" in title.upper() or "TOTEM" in body_text.upper()


def test_health_endpoint_ok(page, app_server):
    """Smoke test: endpoint de health deve retornar JSON com status ok."""
    response = page.request.get(f"{app_server}/api/health")

    assert response.ok
    payload = response.json()
    assert payload.get("status") == "ok"
    assert "timestamp" in payload


def test_admin_dashboard_requires_auth(page, app_server):
    """Dashboard admin deve rejeitar acesso sem Bearer token."""
    response = page.request.get(f"{app_server}/api/admin/dashboard")
    assert response.status == 401
    payload = response.json()
    assert payload.get("status") == "erro"


def test_admin_analytics_requires_auth(page, app_server):
    """Relatório analítico admin também deve exigir Bearer token."""
    response = page.request.get(f"{app_server}/api/admin/analytics-report")
    assert response.status == 401
    payload = response.json()
    assert payload.get("status") == "erro"


def test_admin_login_api_invalid_credentials(page, app_server):
    """Credenciais inválidas devem retornar 401 no login admin."""
    response = _admin_login(page, app_server, username="wrong", password="wrong")
    assert response.status == 401
    payload = response.json()
    assert payload.get("success") is False


def test_admin_login_api_returns_token(page, app_server):
    """Login válido deve retornar token para chamadas protegidas."""
    response = _admin_login(page, app_server)
    assert response.status == 200
    payload = response.json()
    assert payload.get("success") is True
    assert isinstance(payload.get("token"), str) and payload["token"]


def test_admin_dashboard_with_token(page, app_server):
    """Dashboard admin deve retornar dados quando token é válido."""
    login = _admin_login(page, app_server)
    assert login.status == 200
    token = login.json()["token"]

    response = page.request.get(
        f"{app_server}/api/admin/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status == 200
    payload = response.json()
    assert payload.get("success") is True
    assert "stats" in payload
    assert "trend" in payload
    assert "deposits" in payload


def test_admin_analytics_with_token(page, app_server):
    """Relatório analítico deve retornar estrutura consolidada com token válido."""
    login = _admin_login(page, app_server)
    assert login.status == 200
    token = login.json()["token"]

    response = page.request.get(
        f"{app_server}/api/admin/analytics-report",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status == 200
    payload = response.json()
    assert payload.get("success") is True
    assert "report" in payload
    assert "kpis" in payload["report"]
    assert "generated_at" in payload["report"]


def test_admin_login_ui_redirects_to_dashboard(page, app_server):
    """Fluxo UI de login deve redirecionar para dashboard."""
    page.goto(f"{app_server}/admin", wait_until="domcontentloaded")
    page.fill("#username", "admin")
    page.fill("#password", "admin123")
    page.click("#loginBtn")

    page.wait_for_url("**/admin/dashboard", timeout=10000)
    assert "/admin/dashboard" in page.url
    assert page.locator("h1").first.is_visible()


def test_classify_requires_image(page, app_server):
    """Classify sem imagem deve retornar 400."""
    response = page.request.post(
        f"{app_server}/api/classify",
        headers={"Content-Type": "application/json"},
        data=json.dumps({}),
    )
    assert response.status == 400
    payload = response.json()
    assert "error" in payload


def test_classify_invalid_base64_returns_error(page, app_server):
    """Base64 inválido deve retornar erro controlado."""
    response = page.request.post(
        f"{app_server}/api/classify",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"image": "data:image/jpeg;base64,###INVALID###"}),
    )
    assert response.status in (400, 500)
    payload = response.json()
    assert "timestamp" in payload or "error" in payload


def test_classify_valid_base64_contract(page, app_server):
    """Classify com payload válido deve responder contrato esperado."""
    image_b64 = _load_test_image_base64()
    response = page.request.post(
        f"{app_server}/api/classify",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"image": f"data:image/jpeg;base64,{image_b64}"}),
    )
    assert response.status in (200, 500)
    payload = response.json()
    if response.status == 200:
        assert payload.get("status") in {"sucesso", "rejeitado"}
        assert isinstance(payload.get("is_tampinha"), bool)
        assert "confidence" in payload
        assert "method" in payload
        assert "timestamp" in payload
    else:
        # Em fallback/erro interno, contrato mínimo de erro deve existir.
        assert payload.get("status") == "erro"
        assert "timestamp" in payload


def test_validate_complete_accepts_base64_payload(page, app_server):
    """Endpoint de validação completa deve aceitar JSON com imagem base64."""
    image_path = Path("test_tampinha.jpg")
    assert image_path.exists(), "Imagem de teste não encontrada: test_tampinha.jpg"

    image_b64 = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    payload = {
        "image": f"data:image/jpeg;base64,{image_b64}",
        "presenca": True,
        "peso": 2600,
    }
    response = page.request.post(
        f"{app_server}/api/validate-complete",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
    )

    # A rota pode retornar 200 (classificação/validação) ou 500 (falha ESP32).
    assert response.status in (200, 500)
    payload = response.json()
    assert "timestamp" in payload
    assert "status" in payload


def test_validate_mechanical_json_paths(page, app_server):
    """Validação mecânica JSON deve cobrir aprovado e rejeitado."""
    approved = page.request.post(
        f"{app_server}/api/validate-mechanical",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"presenca": True, "peso": 2600}),
    )
    assert approved.status == 200
    approved_payload = approved.json()
    assert approved_payload.get("status") == "aprovado"

    rejected = page.request.post(
        f"{app_server}/api/validate-mechanical",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"presenca": False, "peso": 1000}),
    )
    assert rejected.status == 200
    rejected_payload = rejected.json()
    assert rejected_payload.get("status") == "rejeitado"


def test_save_deposit_requires_image(page, app_server):
    """save_deposit sem imagem deve retornar 400."""
    response = page.request.post(
        f"{app_server}/api/save_deposit",
        headers={"Content-Type": "application/json"},
        data=json.dumps({}),
    )
    assert response.status == 400
    payload = response.json()
    assert payload.get("status") == "erro"


def test_speech_endpoints_contract(page, app_server):
    """speech/info e speech/sustainability devem responder contrato válido."""
    info_response = page.request.get(f"{app_server}/api/speech/info")
    assert info_response.status == 200
    info_payload = info_response.json()
    assert "available" in info_payload
    assert "size" in info_payload
    assert info_payload.get("url") == "/api/speech/sustainability"

    speech_response = page.request.get(f"{app_server}/api/speech/sustainability")
    assert speech_response.status in (200, 500)
    if speech_response.status == 200:
        assert "audio" in speech_response.headers.get("content-type", "")


def test_esp32_health_contract(page, app_server):
    """Endpoint esp32-health deve responder online ou offline com timestamp."""
    response = page.request.get(f"{app_server}/api/esp32-health")
    assert response.status in (200, 503)
    payload = response.json()
    assert payload.get("status") in {"online", "offline"}
    assert "timestamp" in payload
