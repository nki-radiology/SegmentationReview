"""Tests for segmentation_review.loader."""

import pytest
from pathlib import Path

from segmentation_review.loader import (
    SUPPORTED_FORMATS,
    _get_suffix,
    count_segments,
    get_segment_ids,
    load_segmentation,
    _MockSegmentationNode,
)


# ---------------------------------------------------------------------------
# _get_suffix
# ---------------------------------------------------------------------------


class TestGetSuffix:
    def test_nii_gz(self, tmp_path):
        p = tmp_path / "seg.nii.gz"
        assert _get_suffix(p) == ".nii.gz"

    def test_nii(self, tmp_path):
        p = tmp_path / "seg.nii"
        assert _get_suffix(p) == ".nii"

    def test_nrrd(self, tmp_path):
        p = tmp_path / "seg.nrrd"
        assert _get_suffix(p) == ".nrrd"


# ---------------------------------------------------------------------------
# count_segments
# ---------------------------------------------------------------------------


class TestCountSegments:
    def test_none_node_returns_zero(self):
        assert count_segments(None) == 0

    def test_mock_node_returns_correct_count(self):
        node = _MockSegmentationNode(Path("fake.nrrd"), ".nrrd")
        assert count_segments(node) == 2


# ---------------------------------------------------------------------------
# get_segment_ids
# ---------------------------------------------------------------------------


class TestGetSegmentIds:
    def test_none_node_returns_empty_list(self):
        assert get_segment_ids(None) == []

    def test_mock_node_returns_ids(self):
        node = _MockSegmentationNode(Path("fake.nrrd"), ".nrrd")
        ids = get_segment_ids(node)
        assert len(ids) == 2
        assert all(isinstance(i, str) for i in ids)


# ---------------------------------------------------------------------------
# load_segmentation
# ---------------------------------------------------------------------------


class TestLoadSegmentation:
    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="not found"):
            load_segmentation(tmp_path / "nonexistent.nrrd")

    def test_unsupported_format_raises(self, tmp_path):
        bad_file = tmp_path / "seg.dcm"
        bad_file.touch()
        with pytest.raises(ValueError, match="Unsupported format"):
            load_segmentation(bad_file)

    @pytest.mark.parametrize("ext", [".nii", ".nrrd"])
    def test_supported_formats_return_dict(self, tmp_path, ext):
        seg_file = tmp_path / f"seg{ext}"
        seg_file.touch()
        result = load_segmentation(seg_file)
        assert "node" in result
        assert result["n_segments"] == 2
        assert result["format"] == ext

    def test_nii_gz_format_detected(self, tmp_path):
        seg_file = tmp_path / "seg.nii.gz"
        seg_file.touch()
        result = load_segmentation(seg_file)
        assert result["format"] == ".nii.gz"

    def test_path_is_resolved_absolute(self, tmp_path):
        seg_file = tmp_path / "seg.nrrd"
        seg_file.touch()
        result = load_segmentation(seg_file)
        assert result["path"].is_absolute()
