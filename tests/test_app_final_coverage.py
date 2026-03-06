"""
Tests to cover remaining missing lines in app.py and root conftest.py.

app.py missing:
  - Lines 439, 442-443: _safe_cv branches (int(v) and except TypeError/ValueError)
  - Lines 557-561: background thread exception in validate_esp32_background
  - Line 585: GET /api/esp32-status route

conftest.py (root) missing:
  - Lines 15-19: sample_image fixture body
  - Lines 25-27: temp_model_path fixture body
"""
from __future__ import annotations

import base64
import io
import json
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest

from app import app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as flask_client:
        yield flask_client


def _img_bytes(h: int = 16, w: int = 16) -> bytes:
    img = np.zeros((h, w, 3), dtype=np.uint8)
    ok, buff = cv2.imencode(".jpg", img)
    assert ok
    return bytes(buff)


def _b64_image(h: int = 16, w: int = 16) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(_img_bytes(h, w)).decode()


def _sync_thread_factory(target=None, daemon=True):
    """Replace threading.Thread with one that runs target() synchronously on start()."""
    mock_t = MagicMock()
    mock_t.start = lambda: (target() if target else None)
    return mock_t


# =============================================================================
# GET /api/esp32-status — line 585
# =============================================================================

class TestEsp32StatusRoute:
    """Line 585: GET /api/esp32-status returns esp32_status dict."""

    def test_esp32_status_returns_200_with_dict(self, client):
        """Line 585: simple GET /api/esp32-status → 200 + JSON dict."""
        response = client.get("/api/esp32-status")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)

    def test_esp32_status_has_status_key(self, client):
        """esp32_status contains a 'status' key."""
        response = client.get("/api/esp32-status")
        data = json.loads(response.data)
        assert "status" in data


# =============================================================================
# _safe_cv branches — lines 439, 442-443
# These are triggered inside /api/validate-complete when classifier is not None
# =============================================================================

class TestSafeCvBranches:
    """Lines 439, 442-443: _safe_cv function inside /api/validate-complete."""

    def test_safe_cv_int_branch_line_439(self, client):
        """
        Line 439: _safe_cv(int_value, 0, 0) → int(v) branch.

        The 'hough' key calls _safe_cv(_last_hough_count, 0, 0).
        When _last_hough_count is an int and decimals=0 (falsy),
        the `return int(v)` branch (line 439) is executed.
        """
        payload = {"image": _b64_image()}

        mock_clf = MagicMock()
        # Set _last_hough_count as a plain int → isinstance(0, (int, float)) = True
        # decimals=0 is falsy → int(v) → LINE 439
        mock_clf._last_hough_count = 0  # int, not MagicMock!
        mock_clf._last_hough_consistent = False
        mock_clf._last_circularity = 0.5
        mock_clf._last_aspect_ratio = 0.5
        mock_clf._last_ellipse_aspect = 0.5
        mock_clf._last_contour_area = 500.0
        mock_clf.classify_image.return_value = (0, 0.85, 80.0, "SVM")

        with patch("app.image_classifier", mock_clf), \
             patch("app.db_connection", None):
            response = client.post("/api/validate-complete", json=payload)

        assert response.status_code == 200

    def test_safe_cv_except_branch_lines_442_443(self, client):
        """
        Lines 442-443: _safe_cv with non-convertible value → except branch.

        The 'circularity' key calls _safe_cv(_last_circularity, 0).
        When _last_circularity is a list (not int/float), float([...]) raises
        TypeError, caught in the except block (lines 442-443).
        """
        payload = {"image": _b64_image()}

        mock_clf = MagicMock()
        mock_clf._last_hough_count = 0
        mock_clf._last_hough_consistent = False
        # list → isinstance fails → float([...]) → TypeError → LINE 442-443
        mock_clf._last_circularity = [1, 2, 3]
        mock_clf._last_aspect_ratio = 0.5
        mock_clf._last_ellipse_aspect = 0.5
        mock_clf._last_contour_area = 500.0
        mock_clf.classify_image.return_value = (0, 0.85, 80.0, "SVM")

        with patch("app.image_classifier", mock_clf), \
             patch("app.db_connection", None):
            response = client.post("/api/validate-complete", json=payload)

        assert response.status_code == 200

    def test_safe_cv_both_branches_in_one_request(self, client):
        """
        Covers BOTH line 439 AND lines 442-443 in a single request.

        hough (int, decimals=0) → LINE 439
        circularity (list) → TypeError → LINES 442-443
        """
        payload = {"image": _b64_image()}

        mock_clf = MagicMock()
        mock_clf._last_hough_count = 5       # int → LINE 439
        mock_clf._last_hough_consistent = False
        mock_clf._last_circularity = [99]    # list → TypeError → LINES 442-443
        mock_clf._last_aspect_ratio = 0.9
        mock_clf._last_ellipse_aspect = 0.9
        mock_clf._last_contour_area = 500.0
        mock_clf.classify_image.return_value = (0, 0.80, 60.0, "SVM")

        with patch("app.image_classifier", mock_clf), \
             patch("app.db_connection", None):
            response = client.post("/api/validate-complete", json=payload)

        assert response.status_code == 200

    def test_safe_cv_with_none_value_returns_default(self, client):
        """_safe_cv(None, 5) → v is None → return default=5 (line 441 else branch)."""
        payload = {"image": _b64_image()}

        mock_clf = MagicMock()
        mock_clf._last_hough_count = 0
        mock_clf._last_hough_consistent = False
        mock_clf._last_circularity = None    # None → returns default
        mock_clf._last_aspect_ratio = 0.5
        mock_clf._last_ellipse_aspect = 0.5
        mock_clf._last_contour_area = 500.0
        mock_clf.classify_image.return_value = (0, 0.80, 60.0, "SVM")

        with patch("app.image_classifier", mock_clf), \
             patch("app.db_connection", None):
            response = client.post("/api/validate-complete", json=payload)

        assert response.status_code == 200


# =============================================================================
# Background thread exception — lines 557-561
# =============================================================================

class TestBackgroundThreadException:
    """
    Lines 557-561: Exception inside validate_esp32_background thread.

    We patch threading.Thread to run synchronously and make get_esp32_sensors
    raise an exception to trigger the except block in the background function.
    """

    def test_background_thread_exception_covered(self, client):
        """Lines 557-561: get_esp32_sensors raises inside thread → esp32_status error."""
        payload = {"image": _b64_image()}

        mock_clf = MagicMock()
        mock_clf._last_hough_count = 0
        mock_clf._last_hough_consistent = False
        mock_clf._last_circularity = 0.9
        mock_clf._last_aspect_ratio = 0.9
        mock_clf._last_ellipse_aspect = 0.9
        mock_clf._last_contour_area = 500.0
        # Returns tampinha (pred=1) so the background thread starts
        mock_clf.classify_image.return_value = (1, 0.95, 120.0, "SAT_HIGH")

        with patch("app.image_classifier", mock_clf), \
             patch("app.db_connection", None), \
             patch("app.get_esp32_sensors", side_effect=RuntimeError("sensor failure")), \
             patch("threading.Thread", side_effect=_sync_thread_factory):
            response = client.post("/api/validate-complete", json=payload)

        # Route itself should still succeed (thread errors are caught)
        assert response.status_code == 200

    def test_background_thread_exception_updates_esp32_status(self, client):
        """After exception, esp32_status reflects error state."""
        import app as app_module

        payload = {"image": _b64_image()}

        mock_clf = MagicMock()
        mock_clf._last_hough_count = 0
        mock_clf._last_hough_consistent = False
        mock_clf._last_circularity = 0.9
        mock_clf._last_aspect_ratio = 0.9
        mock_clf._last_ellipse_aspect = 0.9
        mock_clf._last_contour_area = 500.0
        mock_clf.classify_image.return_value = (1, 0.95, 120.0, "SAT_HIGH")

        with patch("app.image_classifier", mock_clf), \
             patch("app.db_connection", None), \
             patch("app.get_esp32_sensors", side_effect=ValueError("bad sensor data")), \
             patch("threading.Thread", side_effect=_sync_thread_factory):
            client.post("/api/validate-complete", json=payload)

        # After sync thread execution, esp32_status should show error
        assert app_module.esp32_status.get("status") == "error"
        assert "bad sensor data" in app_module.esp32_status.get("message", "")


# =============================================================================
# Root conftest.py fixtures — lines 15-19 and 25-27
# These fixtures are in /conftest.py (root level) and are available here.
# =============================================================================

class TestRootConftestFixtures:
    """
    Covers root conftest.py lines 15-19 (sample_image body)
    and lines 25-27 (temp_model_path body).
    """

    def test_sample_image_fixture_is_ndarray(self, sample_image):
        """Lines 15-19: sample_image fixture creates a 128x128 BGR image."""
        assert isinstance(sample_image, np.ndarray)
        assert sample_image.ndim == 3
        assert sample_image.shape == (128, 128, 3)

    def test_sample_image_fixture_is_uint8(self, sample_image):
        """sample_image has dtype uint8."""
        assert sample_image.dtype == np.uint8

    def test_temp_model_path_fixture_exists(self, temp_model_path):
        """Lines 25-27: temp_model_path fixture creates a Path that exists."""
        assert isinstance(temp_model_path, Path)
        assert temp_model_path.exists()
        assert temp_model_path.is_dir()

    def test_temp_model_path_fixture_name(self, temp_model_path):
        """temp_model_path directory is named 'svm'."""
        assert temp_model_path.name == "svm"
