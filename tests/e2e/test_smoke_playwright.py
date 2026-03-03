from __future__ import annotations

import pytest


pytestmark = pytest.mark.e2e


def test_home_page_loads(page, app_server):
    """Smoke test: home deve carregar e conter contexto do totem."""
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
