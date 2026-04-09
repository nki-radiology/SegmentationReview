# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This is a **GitHub training repository** for technical colleagues at NKI Radiology who already know Python. The goal is not to build production software, but to teach professional Git/GitHub workflow using a realistic medical imaging domain: a 3D Slicer extension called SegmentationReview.

Topics covered: cloning, branching, commits, push/pull, rebase, conflict resolution, PRs, code review, GitHub Actions CI, commit conventions, and LLM-assisted development hygiene.

## Repository Structure

- `SegmentationReview/` — the original 3D Slicer extension (Python, CMakeLists). The real implementation participants will touch.
- `docs/` — tutorial based md files for the user to go through to get a basic grasp on how to use Git

## 3D Slicer Extension Structure

This repo contains a **scripted (Python-only) 3D Slicer extension** named `SegmentationReview`. Understanding the two-level CMake layout is important when debugging loading issues.

### CMake layout

```
TutorialGithubNKIRadiology/          ← extension root (folder name must match project())
  CMakeLists.txt                     ← extension-level: sets EXTENSION_* metadata, calls add_subdirectory()
  SegmentationReview/                ← module directory
    CMakeLists.txt                   ← module-level: calls slicerMacroBuildScriptedModule()
    SegmentationReview.py            ← the actual Python module
    Resources/
      Icons/SegmentationReview.png
      UI/SegmentationReview.ui       ← Qt Designer UI file loaded at runtime via slicer.util.loadUI()
    Testing/
      CMakeLists.txt
      Python/CMakeLists.txt
```

**Key constraint:** The root `CMakeLists.txt` `project()` name must match the folder name for the Extension Wizard to recognise the extension. This repo's folder is `TutorialGithubNKIRadiology`, so the root CMakeLists.txt uses `project(TutorialGithubNKIRadiology)`.

### Python module class pattern (`ScriptedLoadableModule`)

Every scripted Slicer module follows this four-class pattern in one `.py` file:

| Class | Base class | Purpose |
|---|---|---|
| `SegmentationReview` | `ScriptedLoadableModule` | Module metadata (title, category, contributors). Instantiated at Slicer startup. |
| `SegmentationReviewWidget` | `ScriptedLoadableModuleWidget` | Qt UI logic. `__init__` runs when module is first opened; `setup()` builds the widget tree. |
| `SlicerLikertDLratingLogic` | `ScriptedLoadableModuleLogic` | Computation logic, decoupled from UI. |
| `SlicerLikertDLratingTest` | `ScriptedLoadableModuleTest` | Unit tests runnable from within Slicer. |

Note: the Logic and Test classes in this repo use `SlicerLikertDLrating*` naming (historical), not `SegmentationReview*`.

### Loading the extension for development (no build step needed)

Scripted modules do not need CMake/compilation. To load during development:

1. Open Slicer → **Edit → Application Settings → Modules**
2. Under **Additional module paths**, click `+` and add the `SegmentationReview/` subfolder (the one containing `SegmentationReview.py`)
3. Click OK and restart Slicer

The Extension Wizard (`Developer Tools → Extension Wizard`) can also load the extension by selecting the **root** `TutorialGithubNKIRadiology/` folder — but the Additional module paths method above is simpler and more reliable for day-to-day development.

**Do not** point the Extension Wizard at the `SegmentationReview/` subfolder — that is a module directory, not an extension root, and it will fail with a `KeyError: script does not set 'EXTENSION_HOMEPAGE'` error.


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
