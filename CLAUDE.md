# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This is a **GitHub training repository** for technical colleagues at NKI Radiology who already know Python. The goal is not to build production software, but to teach professional Git/GitHub workflow using a realistic medical imaging domain: a 3D Slicer extension called SegmentationReview.

Topics covered: cloning, branching, commits, push/pull, rebase, conflict resolution, PRs, code review, GitHub Actions CI, commit conventions, and LLM-assisted development hygiene.

## Repository Structure

- `SegmentationReview/` — the original 3D Slicer extension (Python, CMakeLists). The real implementation participants will touch.
- `SegmentationReview-chatgpt-tutorial/` — ChatGPT-generated tutorial draft. Contains the most complete reference structure: `src/`, `docs/tutorial/`, `.github/` (CI workflows, PR template, issue templates), `scripts/check.sh`, `pyproject.toml`, `commitlint.config.js`, `CONTRIBUTING.md`, `CHANGELOG.md`.
- `SegmentationReview-claude-tutorial/` — Claude-generated tutorial draft. Contains `docs/` (workshop plan, exercise scripts, capabilities map, LLM hygiene guide) and `src/`.

Both tutorial drafts are **references** for building out the main repo. Features, exercises, and structural decisions should draw from both.

## Development Commands

These are set up in `SegmentationReview-chatgpt-tutorial/` and should be replicated in the main repo:

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all checks at once (format, lint, type, tests, commitlint)
./scripts/check.sh

# Individual checks
black --check src/
ruff check src/
mypy src/segmentation_review/
pytest --cov=segmentation_review --cov-report=term-missing --cov-fail-under=80

# Single test file
pytest src/tests/test_loader.py -v
```

## Commit Conventions

Follows **Conventional Commits**: `type(scope): description`

Valid types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`  
Valid scopes: `loader`, `exporter`, `ui`, `review`, `ci`, `deps`, `tutorial`, `tests`, `release`

Rules:
- Subject line ≤ 72 characters, imperative mood
- Body explains **why**, not just what
- Reference issues: `Closes #42` or `Related to #17`

Enforced via `commitlint.config.js` + GitHub Actions `commitlint` job on PRs.

## Branch Strategy

Trunk-based with `develop` as integration branch:

```
main (protected)
 └── develop
      ├── feature/<topic>
      ├── fix/<topic>
      ├── refactor/<topic>
      ├── docs/<topic>
      └── chore/<topic>
```

Never push directly to `main`. PRs to `develop`; `develop` merges into `main` via PR. Branch names: lowercase kebab-case.

## GitHub Setup (Intended Final State)

- `main` is branch-protected: require PR + 1 review + CI checks pass + no direct push
- Squash merge for feature branches, rebase merge for hotfixes
- Delete head branches after merge
- PR template: `.github/PULL_REQUEST_TEMPLATE.md` (type of change, test steps, checklist)
- Issue templates: bug report, feature request
- GitHub Actions CI: lint (black + ruff), type check (mypy), tests with coverage (py3.9 + py3.11), commitlint on PRs

## AGENT_GUIDE.md

An `AGENT_GUIDE.md` needs to be created at the repo root. It teaches participants how to use LLMs productively in a repository context. Key sections to include:
- Prompting for commit messages from a diff
- Prompting for PR descriptions
- Generating code review suggestions
- Splitting LLM output into logical commits
- What NOT to do (commit code you don't understand, one massive LLM dump, fake TODOs)

## Workshop Exercises (Reference)

The exercises in `SegmentationReview-claude-tutorial/docs/03_exercise_script.md` are the intended hands-on tasks:
- **A**: Create feature branch, edit a file, commit, push, open PR
- **B**: Add follow-up commit, discuss squash vs multi-commit
- **C**: Code review — leave and respond to comments
- **D**: Rebase — another participant merges to main, rebase feature branch, resolve conflict, `push --force-with-lease`
- **E**: Post-merge hygiene — delete branch, inspect history, compare merge strategies
