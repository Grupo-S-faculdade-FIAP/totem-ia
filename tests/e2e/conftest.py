"""
Fixtures E2E para Playwright (Python).
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests
from playwright.sync_api import sync_playwright


APP_URL = "http://127.0.0.1:5003"
ROOT_DIR = Path(__file__).resolve().parents[2]
PLAYWRIGHT_BROWSERS_DIR = ROOT_DIR / ".playwright-browsers"


def _wait_for_server(url: str, timeout_seconds: int = 30) -> bool:
    """Aguarda servidor HTTP responder health dentro do timeout."""
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            response = requests.get(f"{url}/admin", timeout=1)
            if response.status_code in (200, 401, 302):
                return True
        except requests.RequestException:
            pass
        time.sleep(0.5)
    return False


@pytest.fixture(scope="session", autouse=True)
def e2e_toggle():
    """Evita rodar E2E por padrão na suíte unitária."""
    if os.getenv("RUN_E2E") != "1":
        pytest.skip("E2E desativado. Use RUN_E2E=1 para executar Playwright.")
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(PLAYWRIGHT_BROWSERS_DIR)
    with sync_playwright() as pw:
        executable = Path(pw.chromium.executable_path)
    if not executable.exists():
        pytest.skip(
            "Chromium do Playwright não encontrado. Rode: python3 -m playwright install chromium"
        )


@pytest.fixture(scope="session")
def browser():
    """Browser Playwright compartilhado para toda a sessão E2E."""
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        yield b
        b.close()


@pytest.fixture
def page(browser):
    """Página Playwright isolada por teste."""
    context = browser.new_context()
    p = context.new_page()
    yield p
    context.close()


@pytest.fixture(scope="session")
def app_server():
    """Usa servidor Flask já em execução em 5003 ou sobe um novo."""
    # Verifica se já há um servidor rodando
    if _wait_for_server(APP_URL, timeout_seconds=3):
        yield APP_URL
        return

    process = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=str(ROOT_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    if not _wait_for_server(APP_URL, timeout_seconds=45):
        process.terminate()
        process.wait(timeout=10)
        pytest.fail("Falha ao iniciar servidor Flask para E2E.")

    yield APP_URL

    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
