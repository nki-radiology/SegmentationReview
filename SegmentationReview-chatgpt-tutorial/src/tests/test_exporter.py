"""Tests for segmentation_review.exporter."""

import csv
import json
from pathlib import Path

import pytest

from segmentation_review.exporter import (
    ReviewExporter,
    ReviewResult,
    ReviewSummary,
    SegmentVerdict,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_results():
    return [
        ReviewResult(
            segment_id="Segment_1",
            verdict=SegmentVerdict.ACCEPT,
            reviewed_at="2024-06-01T10:00:00+00:00",
        ),
        ReviewResult(
            segment_id="Segment_2",
            verdict=SegmentVerdict.REJECT,
            comment="Over-segmented at boundary",
            reviewed_at="2024-06-01T10:02:00+00:00",
        ),
        ReviewResult(
            segment_id="Segment_3",
            verdict=SegmentVerdict.FLAG,
            comment="Discuss with radiologist",
            reviewed_at="2024-06-01T10:03:00+00:00",
        ),
    ]


@pytest.fixture
def exporter():
    return ReviewExporter(reviewer="j.devries", case_id="case_001")


# ---------------------------------------------------------------------------
# ReviewSummary stats
# ---------------------------------------------------------------------------


class TestReviewSummaryStats:
    def test_counts_accepted(self, sample_results):
        summary = ReviewSummary(
            case_id="x", reviewer="y", results=sample_results
        )
        assert summary.n_accepted == 1

    def test_counts_rejected(self, sample_results):
        summary = ReviewSummary(
            case_id="x", reviewer="y", results=sample_results
        )
        assert summary.n_rejected == 1

    def test_counts_flagged(self, sample_results):
        summary = ReviewSummary(
            case_id="x", reviewer="y", results=sample_results
        )
        assert summary.n_flagged == 1

    def test_empty_results(self):
        summary = ReviewSummary(case_id="x", reviewer="y", results=[])
        assert summary.n_accepted == 0
        assert summary.n_rejected == 0
        assert summary.n_flagged == 0


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------


class TestCsvExport:
    def test_creates_file(self, tmp_path, exporter, sample_results):
        out = tmp_path / "review.csv"
        exporter.to_csv(out, sample_results)
        assert out.exists()

    def test_returns_resolved_path(self, tmp_path, exporter, sample_results):
        out = tmp_path / "review.csv"
        returned = exporter.to_csv(out, sample_results)
        assert returned.is_absolute()

    def test_header_columns(self, tmp_path, exporter, sample_results):
        out = tmp_path / "review.csv"
        exporter.to_csv(out, sample_results)
        with out.open() as fh:
            reader = csv.DictReader(fh)
            assert set(reader.fieldnames) == {
                "case_id", "reviewer", "segment_id",
                "verdict", "comment", "reviewed_at",
            }

    def test_row_count(self, tmp_path, exporter, sample_results):
        out = tmp_path / "review.csv"
        exporter.to_csv(out, sample_results)
        with out.open() as fh:
            rows = list(csv.DictReader(fh))
        assert len(rows) == len(sample_results)

    def test_case_id_and_reviewer_in_every_row(
        self, tmp_path, exporter, sample_results
    ):
        out = tmp_path / "review.csv"
        exporter.to_csv(out, sample_results)
        with out.open() as fh:
            for row in csv.DictReader(fh):
                assert row["case_id"] == "case_001"
                assert row["reviewer"] == "j.devries"

    def test_verdict_values_are_strings(self, tmp_path, exporter, sample_results):
        out = tmp_path / "review.csv"
        exporter.to_csv(out, sample_results)
        with out.open() as fh:
            rows = list(csv.DictReader(fh))
        verdicts = {r["verdict"] for r in rows}
        assert verdicts == {"accept", "reject", "flag"}

    def test_empty_comment_written_as_empty_string(
        self, tmp_path, exporter
    ):
        results = [ReviewResult(segment_id="S1", verdict=SegmentVerdict.ACCEPT)]
        out = tmp_path / "review.csv"
        exporter.to_csv(out, results)
        with out.open() as fh:
            row = list(csv.DictReader(fh))[0]
        assert row["comment"] == ""

    def test_creates_parent_directories(self, tmp_path, exporter, sample_results):
        out = tmp_path / "nested" / "deep" / "review.csv"
        exporter.to_csv(out, sample_results)
        assert out.exists()

    def test_empty_results_writes_header_only(self, tmp_path, exporter):
        out = tmp_path / "review.csv"
        exporter.to_csv(out, [])
        with out.open() as fh:
            rows = list(csv.DictReader(fh))
        assert rows == []


# ---------------------------------------------------------------------------
# JSON export
# ---------------------------------------------------------------------------


class TestJsonExport:
    def _load_json(self, path: Path) -> dict:
        with path.open() as fh:
            return json.load(fh)

    def test_creates_file(self, tmp_path, exporter, sample_results):
        out = tmp_path / "review.json"
        exporter.to_json(out, sample_results)
        assert out.exists()

    def test_returns_resolved_path(self, tmp_path, exporter, sample_results):
        out = tmp_path / "review.json"
        returned = exporter.to_json(out, sample_results)
        assert returned.is_absolute()

    def test_schema_version_present(self, tmp_path, exporter, sample_results):
        out = tmp_path / "review.json"
        exporter.to_json(out, sample_results)
        data = self._load_json(out)
        assert data["schema_version"] == "1.0"

    def test_top_level_fields(self, tmp_path, exporter, sample_results):
        out = tmp_path / "review.json"
        exporter.to_json(out, sample_results)
        data = self._load_json(out)
        for key in ("case_id", "reviewer", "completed_at", "stats", "results"):
            assert key in data, f"Missing key: {key}"

    def test_stats_counts(self, tmp_path, exporter, sample_results):
        out = tmp_path / "review.json"
        exporter.to_json(out, sample_results)
        stats = self._load_json(out)["stats"]
        assert stats["n_accepted"] == 1
        assert stats["n_rejected"] == 1
        assert stats["n_flagged"] == 1

    def test_result_entries(self, tmp_path, exporter, sample_results):
        out = tmp_path / "review.json"
        exporter.to_json(out, sample_results)
        results = self._load_json(out)["results"]
        assert len(results) == 3
        segment_ids = {r["segment_id"] for r in results}
        assert segment_ids == {"Segment_1", "Segment_2", "Segment_3"}

    def test_comment_preserved(self, tmp_path, exporter, sample_results):
        out = tmp_path / "review.json"
        exporter.to_json(out, sample_results)
        results = self._load_json(out)["results"]
        rejected = next(r for r in results if r["verdict"] == "reject")
        assert rejected["comment"] == "Over-segmented at boundary"

    def test_null_comment_in_json(self, tmp_path, exporter):
        results = [ReviewResult(segment_id="S1", verdict=SegmentVerdict.ACCEPT)]
        out = tmp_path / "review.json"
        exporter.to_json(out, results)
        data = self._load_json(out)
        assert data["results"][0]["comment"] is None

    def test_valid_json_output(self, tmp_path, exporter, sample_results):
        out = tmp_path / "review.json"
        exporter.to_json(out, sample_results)
        # If this doesn't raise, the JSON is valid
        data = self._load_json(out)
        assert isinstance(data, dict)

    def test_empty_results(self, tmp_path, exporter):
        out = tmp_path / "review.json"
        exporter.to_json(out, [])
        data = self._load_json(out)
        assert data["results"] == []
        assert data["stats"]["n_accepted"] == 0
