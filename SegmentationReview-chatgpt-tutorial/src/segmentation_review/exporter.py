"""
exporter.py — Export review results to CSV or JSON.

Usage::

    from segmentation_review.exporter import ReviewExporter, ReviewResult, SegmentVerdict

    results = [
        ReviewResult(segment_id="Segment_1", verdict=SegmentVerdict.ACCEPT),
        ReviewResult(segment_id="Segment_2", verdict=SegmentVerdict.REJECT,
                     comment="Over-segmented at boundary"),
    ]
    exporter = ReviewExporter(reviewer="j.devries", case_id="case_001")
    exporter.to_csv("review_case_001.csv", results)
    exporter.to_json("review_case_001.json", results)
"""

from __future__ import annotations

import csv
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class SegmentVerdict(str, Enum):
    ACCEPT = "accept"
    REJECT = "reject"
    FLAG = "flag"  # Needs further discussion


@dataclass
class ReviewResult:
    """The outcome of reviewing a single segment.

    Attributes:
        segment_id: The segment identifier as returned by the Slicer node.
        verdict: One of ``accept``, ``reject``, or ``flag``.
        comment: Optional free-text comment left by the reviewer.
        reviewed_at: ISO 8601 timestamp; set automatically if not provided.
    """

    segment_id: str
    verdict: SegmentVerdict
    comment: Optional[str] = None
    reviewed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class ReviewSummary:
    """Aggregated review for one case.

    Attributes:
        case_id: Unique identifier for the imaging case.
        reviewer: Reviewer identifier (e.g. staff initials or email).
        results: List of per-segment verdicts.
        completed_at: ISO 8601 timestamp of when the review was finalised.
    """

    case_id: str
    reviewer: str
    results: list[ReviewResult]
    completed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def n_accepted(self) -> int:
        return sum(1 for r in self.results if r.verdict == SegmentVerdict.ACCEPT)

    @property
    def n_rejected(self) -> int:
        return sum(1 for r in self.results if r.verdict == SegmentVerdict.REJECT)

    @property
    def n_flagged(self) -> int:
        return sum(1 for r in self.results if r.verdict == SegmentVerdict.FLAG)


class ReviewExporter:
    """Export review results to CSV or JSON.

    Args:
        reviewer: Reviewer identifier (name, email, or initials).
        case_id: Imaging case identifier.
    """

    def __init__(self, reviewer: str, case_id: str) -> None:
        self.reviewer = reviewer
        self.case_id = case_id

    def to_csv(self, path: str | Path, results: list[ReviewResult]) -> Path:
        """Write review results to a CSV file.

        Args:
            path: Destination file path.
            results: List of ReviewResult objects.

        Returns:
            Resolved path of the written file.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = ["case_id", "reviewer", "segment_id", "verdict", "comment", "reviewed_at"]

        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            for result in results:
                writer.writerow(
                    {
                        "case_id": self.case_id,
                        "reviewer": self.reviewer,
                        "segment_id": result.segment_id,
                        "verdict": result.verdict.value,
                        "comment": result.comment or "",
                        "reviewed_at": result.reviewed_at,
                    }
                )

        logger.info("Wrote %d results to %s", len(results), path)
        return path.resolve()

    def to_json(self, path: str | Path, results: list[ReviewResult]) -> Path:
        """Write review results to a JSON file.

        The output follows the SegReview schema (see issue #34).

        Args:
            path: Destination file path.
            results: List of ReviewResult objects.

        Returns:
            Resolved path of the written file.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        summary = ReviewSummary(
            case_id=self.case_id,
            reviewer=self.reviewer,
            results=results,
        )

        payload = {
            "schema_version": "1.0",
            "case_id": summary.case_id,
            "reviewer": summary.reviewer,
            "completed_at": summary.completed_at,
            "stats": {
                "n_accepted": summary.n_accepted,
                "n_rejected": summary.n_rejected,
                "n_flagged": summary.n_flagged,
            },
            "results": [
                {
                    "segment_id": r.segment_id,
                    "verdict": r.verdict.value,
                    "comment": r.comment,
                    "reviewed_at": r.reviewed_at,
                }
                for r in results
            ],
        }

        with path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)

        logger.info("Wrote JSON summary to %s", path)
        return path.resolve()
