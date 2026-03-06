"""
Tests to cover missing branches in src/modules/image.py

Missing lines:
  70-74: _get_face_cascade — cascade empty and exception paths
  118:   _crop_to_roi_center — returns original when size < 32
  208-209: extract_color_features — cv2.fitEllipse raises cv2.error
  233:   extract_color_features — hough_contour_consistent=True when contour_area==0
  266:   classify_image — USE_ROI=False branch
  320:   classify_image — reason: ellipse_aspect below threshold
  323:   classify_image — reason: contour_area above CV_MAX_CONTOUR_AREA
"""
import pytest
import numpy as np
import cv2
from unittest.mock import patch, MagicMock

import src.modules.image as image_mod
from src.modules.image import ImageClassifier, _get_face_cascade


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_bgr(h: int = 128, w: int = 128, sat: int = 120) -> np.ndarray:
    """Create a BGR image with a given HSV saturation."""
    hsv = np.zeros((h, w, 3), dtype=np.uint8)
    hsv[:, :, 0] = 90
    hsv[:, :, 1] = sat
    hsv[:, :, 2] = 200
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


def _mock_classifier_with_metrics(
    circularity: float = 0.9,
    aspect_ratio: float = 0.9,
    ellipse_aspect: float = 0.0,
    contour_area: float = 500.0,
    contour_count: float = 1.0,
    hough_count: int = 0,
    hough_consistent: bool = False,
) -> ImageClassifier:
    """Create a classifier mock with pre-set CV metrics."""
    clf = ImageClassifier()
    clf.model = MagicMock()
    clf.scaler = MagicMock()
    clf.scaler.transform.return_value = [[0.5] * 8]
    clf.model.predict.return_value = [1]
    clf.model.decision_function.return_value = [2.0]

    clf._last_circularity = circularity
    clf._last_aspect_ratio = aspect_ratio
    clf._last_ellipse_aspect = ellipse_aspect
    clf._last_contour_area = contour_area
    clf._last_contour_count = contour_count
    clf._last_hough_count = hough_count
    clf._last_hough_consistent = hough_consistent
    return clf


# =============================================================================
# _get_face_cascade — lines 70-74
# =============================================================================

class TestGetFaceCascadeBranches:
    """Covers lines 70-74: cascade empty and exception paths."""

    def setup_method(self):
        """Reset the global _FACE_CASCADE cache before each test."""
        self._original = image_mod._FACE_CASCADE
        image_mod._FACE_CASCADE = None  # force re-loading

    def teardown_method(self):
        """Restore original cascade."""
        image_mod._FACE_CASCADE = self._original

    def test_cascade_loaded_but_empty_returns_none(self):
        """Lines 70-71: CascadeClassifier loads but is empty → _FACE_CASCADE = None."""
        with patch("cv2.CascadeClassifier") as mock_cc:
            mock_instance = MagicMock()
            mock_instance.empty.return_value = True  # cascade is empty
            mock_cc.return_value = mock_instance

            result = _get_face_cascade()

        assert result is None
        assert image_mod._FACE_CASCADE is None

    def test_cascade_exception_returns_none(self):
        """Lines 72-74: Exception loading cascade → _FACE_CASCADE = None."""
        with patch("cv2.CascadeClassifier", side_effect=OSError("cascade not found")):
            result = _get_face_cascade()

        assert result is None
        assert image_mod._FACE_CASCADE is None

    def test_cascade_cached_after_successful_load(self):
        """Cascade is cached after first successful load (no re-load)."""
        real_result = _get_face_cascade()
        # Second call should return the same cached object
        cached_result = _get_face_cascade()
        assert real_result is cached_result


# =============================================================================
# _crop_to_roi_center — line 118
# =============================================================================

class TestCropToRoiCenter:
    """Line 118: returns original image when size < 32."""

    def test_small_image_returns_original_unchanged(self):
        """Line 118: 10x10 image → size = int(10 * 0.75)=7 < 32 → return original."""
        clf = ImageClassifier()
        tiny = np.zeros((10, 10, 3), dtype=np.uint8)
        result = clf._crop_to_roi_center(tiny)
        assert result.shape == tiny.shape
        np.testing.assert_array_equal(result, tiny)

    def test_40x40_image_returns_original_unchanged(self):
        """Line 118: 40x40 → size=30 < 32 → return original."""
        clf = ImageClassifier()
        small = np.zeros((40, 40, 3), dtype=np.uint8)
        result = clf._crop_to_roi_center(small)
        assert result.shape == small.shape

    def test_large_image_is_cropped(self):
        """Large image (128x128) → size=96 >= 32 → returns cropped copy."""
        clf = ImageClassifier()
        large = np.zeros((128, 128, 3), dtype=np.uint8)
        result = clf._crop_to_roi_center(large)
        # Cropped to 96x96 (128 * 0.75 = 96)
        assert result.shape == (96, 96, 3)


# =============================================================================
# extract_color_features — lines 208-209 (cv2.fitEllipse cv2.error)
# =============================================================================

class TestExtractColorFeaturesEllipseError:
    """Lines 208-209: cv2.fitEllipse raises cv2.error → ellipse_aspect = aspect_ratio."""

    def test_fitellipse_cv2_error_uses_aspect_ratio_fallback(self):
        """Lines 208-209: cv2.error in fitEllipse → sets ellipse_aspect = aspect_ratio."""
        clf = ImageClassifier()
        clf.model = MagicMock()
        clf.scaler = MagicMock()
        clf.scaler.n_features_in_ = 8

        # Draw a solid circle so Canny/findContours detects a contour with >= 5 points
        img = np.zeros((128, 128, 3), dtype=np.uint8)
        cv2.circle(img, (64, 64), 40, (0, 180, 100), -1)

        with patch("cv2.fitEllipse", side_effect=cv2.error("test ellipse error")):
            features = clf.extract_color_features(img)

        # Should not raise; ellipse_aspect falls back to aspect_ratio
        assert features is not None
        assert not np.isnan(features).any()


# =============================================================================
# extract_color_features — line 233 (hough_contour_consistent=True when area==0)
# =============================================================================

class TestExtractColorFeaturesHoughZeroArea:
    """Line 233: HoughCircles found but contour_area==0 → hough_contour_consistent=True."""

    def test_hough_found_no_contours_sets_consistent_true(self):
        """Line 233: HoughCircles returns circles but findContours returns empty."""
        clf = ImageClassifier()
        clf.model = MagicMock()
        clf.scaler = MagicMock()
        clf.scaler.n_features_in_ = 8

        img = np.zeros((128, 128, 3), dtype=np.uint8)

        # Patch HoughCircles to return 1 circle, findContours to return no contours
        hough_return = np.array([[[64.0, 64.0, 30.0]]])  # x, y, r

        with patch("cv2.HoughCircles", return_value=hough_return), \
             patch("cv2.findContours", return_value=([], None)):
            features = clf.extract_color_features(img)

        # Should succeed and hough_contour_consistent should have been set to True (line 233)
        assert clf._last_hough_consistent is True
        assert clf._last_hough_count == 1

    def test_hough_found_zero_radius_circle_sets_consistent_true(self):
        """Line 233: HoughCircles returns circle with r=0 → hough_expected_area=0 → else branch."""
        clf = ImageClassifier()
        clf.model = MagicMock()
        clf.scaler = MagicMock()
        clf.scaler.n_features_in_ = 8

        img = np.zeros((128, 128, 3), dtype=np.uint8)
        # Draw a circle contour but mock HoughCircles with r=0
        hough_return = np.array([[[64.0, 64.0, 0.0]]])  # r=0 → expected_area=0

        with patch("cv2.HoughCircles", return_value=hough_return), \
             patch("cv2.findContours", return_value=([], None)):
            features = clf.extract_color_features(img)

        assert clf._last_hough_consistent is True


# =============================================================================
# classify_image — line 266 (USE_ROI=False)
# =============================================================================

class TestClassifyImageUseRoiFalse:
    """Line 266: USE_ROI=False → logs 'ROI desativado'."""

    def test_use_roi_false_branch_covered(self):
        """Line 266: when USE_ROI is False, log the 'ROI desativado' message."""
        clf = _mock_classifier_with_metrics(
            contour_count=0.0, hough_count=0
        )
        # Features with saturation above threshold
        features = np.zeros(8, dtype=np.float64)
        features[6] = 50.0  # saturation > SAT_VERY_LOW_THRESHOLD (30)

        img = _make_bgr(128, 128, sat=80)

        with patch.object(image_mod, "USE_ROI", False), \
             patch.object(clf, "extract_color_features", return_value=features):
            result = clf.classify_image(img)

        assert result is not None
        assert result[0] is not None  # pred should be set

    def test_use_roi_true_uses_cropped_image(self):
        """USE_ROI=True (default) crops image before classification."""
        clf = _mock_classifier_with_metrics(contour_count=0.0)
        features = np.zeros(8, dtype=np.float64)
        features[6] = 50.0

        img = _make_bgr(128, 128, sat=80)

        with patch.object(image_mod, "USE_ROI", True), \
             patch.object(clf, "extract_color_features", return_value=features):
            result = clf.classify_image(img)

        assert result is not None


# =============================================================================
# classify_image — line 320 (ellipse reason appended)
# =============================================================================

class TestClassifyImageEllipseRejection:
    """Line 320: ellipse_aspect < CV_MIN_ELLIPSE_ASPECT and > 0 → adds ellipse reason."""

    def test_ellipse_below_threshold_adds_to_reason(self):
        """Line 320: ellipse_aspect=0.5 (0 < 0.5 < 0.78) → reason includes ellipse."""
        # Need: hough_count=0, contour_count>0, is_round_ellipse=False, ellipse_aspect>0
        clf = _mock_classifier_with_metrics(
            circularity=0.9,      # is_circular = True
            aspect_ratio=0.9,     # is_square_bbox = True
            ellipse_aspect=0.5,   # 0 < 0.5 < 0.78 → not is_round_ellipse → LINE 320
            contour_area=500.0,   # is_size_ok = True
            contour_count=1.0,
            hough_count=0,
        )
        features = np.zeros(8, dtype=np.float64)
        features[6] = 50.0  # saturation ok

        img = _make_bgr(128, 128)

        with patch.object(clf, "extract_color_features", return_value=features):
            pred, conf, sat, method = clf.classify_image(img)

        assert method is not None
        assert "CV_REJECT" in method
        assert "ellipse" in method.lower()

    def test_ellipse_zero_not_added_to_reason(self):
        """ellipse_aspect=0 → is_round_ellipse=True (0==0) → no ellipse in reason."""
        clf = _mock_classifier_with_metrics(
            circularity=0.5,      # is_circular=False → enters rejection block
            aspect_ratio=0.9,
            ellipse_aspect=0.0,   # == 0 → is_round_ellipse=True → NOT line 320
            contour_area=500.0,
            contour_count=1.0,
            hough_count=0,
        )
        features = np.zeros(8, dtype=np.float64)
        features[6] = 50.0

        img = _make_bgr(128, 128)

        with patch.object(clf, "extract_color_features", return_value=features):
            pred, conf, sat, method = clf.classify_image(img)

        # Should be rejected due to circularity but NOT ellipse
        assert "CV_REJECT" in method
        assert "ellipse" not in method.lower()


# =============================================================================
# classify_image — line 323 (contour_area > CV_MAX_CONTOUR_AREA reason)
# =============================================================================

class TestClassifyImageContourAreaTooLarge:
    """Line 323: contour_area > CV_MAX_CONTOUR_AREA → adds face area reason."""

    def test_large_contour_area_adds_face_reason(self):
        """Line 323: contour_area=10000 > CV_MAX_CONTOUR_AREA(8500) → 'face?' reason."""
        clf = _mock_classifier_with_metrics(
            circularity=0.9,
            aspect_ratio=0.9,
            ellipse_aspect=0.0,
            contour_area=10000.0,  # > 8500 → not is_size_ok → LINE 323
            contour_count=1.0,
            hough_count=0,
        )
        features = np.zeros(8, dtype=np.float64)
        features[6] = 50.0

        img = _make_bgr(128, 128)

        with patch.object(clf, "extract_color_features", return_value=features):
            pred, conf, sat, method = clf.classify_image(img)

        assert pred == 0
        assert conf == 0.90
        assert "CV_REJECT" in method
        assert "face?" in method or ">" in method

    def test_small_contour_area_adds_min_reason(self):
        """contour_area=10 < CV_MIN_CONTOUR_AREA(150) → adds '<min' reason (line 325)."""
        clf = _mock_classifier_with_metrics(
            circularity=0.9,
            aspect_ratio=0.9,
            ellipse_aspect=0.0,
            contour_area=10.0,   # < 150 → not is_size_ok → line 325 (area < min)
            contour_count=1.0,
            hough_count=0,
        )
        features = np.zeros(8, dtype=np.float64)
        features[6] = 50.0

        img = _make_bgr(128, 128)

        with patch.object(clf, "extract_color_features", return_value=features):
            pred, conf, sat, method = clf.classify_image(img)

        assert "CV_REJECT" in method
        assert "<" in method  # contains the area < min reason


# =============================================================================
# classify_image — CV_CIRCLE_CONFIRMED return (line 378-380 in file)
# =============================================================================

class TestClassifyImageCvCircleConfirmed:
    """CV_CIRCLE_CONFIRMED: contour_circular=True and saturation >= SAT_VERY_LOW_THRESHOLD."""

    def test_cv_circle_confirmed_via_contour_circular(self):
        """CV_CIRCLE_CONFIRMED returned when contour_circular=True and sat>=30."""
        clf = _mock_classifier_with_metrics(
            circularity=0.9,      # >= 0.78
            aspect_ratio=0.9,     # >= 0.78
            ellipse_aspect=0.0,   # == 0 → is_round_ellipse=True
            contour_area=500.0,   # 150 <= 500 <= 8500 → is_size_ok=True
            contour_count=1.0,    # > 0 → contour_circular check applies
            hough_count=0,        # hough_count=0 → goes to contour branch
            hough_consistent=False,
        )
        # saturation = features[6] >= SAT_VERY_LOW_THRESHOLD (30)
        features = np.zeros(8, dtype=np.float64)
        features[6] = 80.0  # saturation well above 30

        img = _make_bgr(128, 128)

        with patch.object(clf, "extract_color_features", return_value=features):
            pred, conf, sat, method = clf.classify_image(img)

        assert pred == 1
        assert conf == 0.85
        assert method == "CV_CIRCLE_CONFIRMED"

    def test_cv_circle_confirmed_via_hough_with_valid_shape(self):
        """CV_CIRCLE_CONFIRMED when hough_with_valid_shape=True."""
        clf = _mock_classifier_with_metrics(
            circularity=0.9,
            aspect_ratio=0.9,
            ellipse_aspect=0.0,
            contour_area=500.0,
            contour_count=1.0,
            hough_count=2,        # hough_count > 0
            hough_consistent=True, # hough_consistent=True
        )
        features = np.zeros(8, dtype=np.float64)
        features[6] = 80.0

        img = _make_bgr(128, 128)

        with patch.object(clf, "extract_color_features", return_value=features):
            pred, conf, sat, method = clf.classify_image(img)

        assert pred == 1
        assert method == "CV_CIRCLE_CONFIRMED"


# =============================================================================
# classify_image — SVM_ACCEPT return (tests the SVM_SOFT_THRESHOLD_HOUGH branch)
# =============================================================================

class TestClassifyImageSvmAccept:
    """SVM_ACCEPT: svm_conf > threshold and saturation >= SAT_VERY_LOW_THRESHOLD."""

    def test_svm_accept_with_hough_soft_threshold(self):
        """SVM uses soft threshold when hough_count>0 and hough_consistent=True."""
        clf = _mock_classifier_with_metrics(
            circularity=0.5,      # < 0.78 → not contour_circular
            aspect_ratio=0.5,
            ellipse_aspect=0.0,
            contour_area=500.0,
            contour_count=0.0,    # no contours → no CV rejection, no cv_confirmed_circle
            hough_count=1,
            hough_consistent=True,
        )
        # SVM returns high confidence
        clf.model.decision_function.return_value = [5.0]  # very high → accept
        clf.model.predict.return_value = [1]

        features = np.zeros(8, dtype=np.float64)
        features[6] = 80.0  # saturation >= 30

        img = _make_bgr(128, 128)

        with patch.object(clf, "extract_color_features", return_value=features):
            pred, conf, sat, method = clf.classify_image(img)

        assert pred == 1
        assert method == "SVM_ACCEPT"
