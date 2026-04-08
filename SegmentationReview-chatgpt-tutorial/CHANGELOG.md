# Changelog

All notable changes to SegmentationReview are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).  
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- JSON export with inter-rater agreement stats (`ReviewExporter.to_json`)
- `count_segments()` and `get_segment_ids()` helpers in `loader.py`
- Full Git & GitHub tutorial in `docs/tutorial/`
- GitHub Actions CI: lint, type-check, test, commitlint
- Branch protection rules and PR template

### Changed
- `load_segmentation()` now returns a typed dict with `n_segments` included

### Fixed
- `_get_suffix()` now correctly identifies `.nii.gz` as a compound extension

---

## [0.1.0] — 2024-05-01

### Added
- Initial project scaffold
- `load_segmentation()` for NIfTI and NRRD files
- CSV export via `ReviewExporter.to_csv()`
- Basic pytest suite
