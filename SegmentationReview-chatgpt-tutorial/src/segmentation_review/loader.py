"""
loader.py — Load segmentation files for review.

Supports NIfTI (.nii, .nii.gz) and NRRD (.nrrd) formats.
All functions return data in a format compatible with 3D Slicer's
vtkMRMLSegmentationNode.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Supported file extensions
SUPPORTED_FORMATS = {".nii", ".nii.gz", ".nrrd"}


def load_segmentation(path: str | Path) -> dict:
    """Load a segmentation file and return a review-ready structure.

    Args:
        path: Path to the segmentation file (.nii, .nii.gz, or .nrrd).

    Returns:
        A dict with keys:
            - ``node``: the loaded segmentation node
            - ``path``: resolved absolute path
            - ``format``: detected file format
            - ``n_segments``: number of segments found

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is not supported.
    """
    path = Path(path).resolve()

    if not path.exists():
        raise FileNotFoundError(f"Segmentation file not found: {path}")

    suffix = _get_suffix(path)
    if suffix not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported format '{suffix}'. Supported: {SUPPORTED_FORMATS}"
        )

    logger.info("Loading segmentation from %s", path)

    # In real Slicer code this would call slicer.util.loadSegmentation()
    node = _load_node(path, suffix)
    n_segments = count_segments(node)

    logger.info("Loaded %d segment(s) from %s", n_segments, path.name)

    return {
        "node": node,
        "path": path,
        "format": suffix,
        "n_segments": n_segments,
    }


def count_segments(segmentation_node) -> int:
    """Return the number of segments in a segmentation node.

    Args:
        segmentation_node: A vtkMRMLSegmentationNode instance.

    Returns:
        Integer count of segments (0 if the node is empty).
    """
    if segmentation_node is None:
        return 0
    return segmentation_node.GetSegmentation().GetNumberOfSegments()


def get_segment_ids(segmentation_node) -> list[str]:
    """Return a list of all segment IDs in the node.

    Args:
        segmentation_node: A vtkMRMLSegmentationNode instance.

    Returns:
        List of segment ID strings. Empty list if node has no segments.
    """
    if segmentation_node is None:
        return []

    seg = segmentation_node.GetSegmentation()
    return [seg.GetNthSegmentID(i) for i in range(seg.GetNumberOfSegments())]


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _get_suffix(path: Path) -> str:
    """Return the effective suffix, handling .nii.gz correctly."""
    name = path.name
    if name.endswith(".nii.gz"):
        return ".nii.gz"
    return path.suffix


def _load_node(path: Path, fmt: str):
    """Stub for slicer.util.loadSegmentation — replaced at runtime by Slicer."""
    # This is replaced by the actual Slicer API in production.
    # Here we return a mock so tests can run outside of Slicer.
    return _MockSegmentationNode(path, fmt)


class _MockSegmentationNode:
    """Minimal stand-in for vtkMRMLSegmentationNode (for testing only)."""

    def __init__(self, path: Path, fmt: str) -> None:
        self._path = path
        self._fmt = fmt
        self._segments = ["Segment_1", "Segment_2"]  # fake segments

    def GetSegmentation(self):
        return self

    def GetNumberOfSegments(self) -> int:
        return len(self._segments)

    def GetNthSegmentID(self, index: int) -> str:
        return self._segments[index]
