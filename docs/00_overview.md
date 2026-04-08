# Git & GitHub Tutorial — Overview

> **Audience:** Technical colleagues at NKI Radiology who know Python but are new to structured Git workflows.
> **Codebase we use:** [`SegmentationReview/SegmentationReview.py`](../SegmentationReview/SegmentationReview.py) — the real extension you may already use clinically.

---

## Modules

| # | Topic | File |
|---|---|---|
| 0 | **Overview** (this page) | `00_overview.md` |
| 1 | **Core concepts** — repo, commit, staging area | `01_core_concepts.md` |
| 2 | **Branches** — create, switch, merge | `02_branches.md` |
| 3 | **Remote workflow** — clone, fetch, pull, push | `03_remote_workflow.md` |
| 4 | **Commit conventions** — Conventional Commits + LLMs | `04_commit_conventions.md` |
| 5 | **Pull Requests** — open, review, merge | `05_pull_requests.md` |
| 6 | **Rebase** — interactive rebase, squash, conflict | `06_rebase.md` |
| 7 | **CI / GitHub Actions** — automated checks on PRs | `07_ci_github_actions.md` |
| 8 | **Exercises** — hands-on A–E | `08_exercises.md` |

Also see [`AGENT_GUIDE.md`](../AGENT_GUIDE.md) at the root for how to use LLMs effectively throughout this workflow.

---

## How to follow along

```bash
# Fork this repo on GitHub, then clone your fork
git clone https://github.com/<your-username>/SegmentationReview.git
cd SegmentationReview

# Set the original as "upstream" to pull instructor updates
git remote add upstream https://github.com/NKIRadiology/SegmentationReview.git
git remote -v
```

All exercises modify `SegmentationReview/SegmentationReview.py`. You will not break anything — changes stay on your own branch until you open a PR.

---

## Workshop agenda (75 min)

| Time | Activity |
|---|---|
| 0–10 min | Why Git matters for research software |
| 10–20 min | Core concepts + mental model walkthrough |
| 20–35 min | Exercise A — first feature branch + commit |
| 35–50 min | Exercise B/C — second commit + code review |
| 50–65 min | Exercise D — rebase and conflict resolution |
| 65–75 min | Exercise E — post-merge hygiene + LLM reflection |

---

## Mental model

```
Working directory  ──git add──►  Staging area  ──git commit──►  Local repo  ──git push──►  Remote (GitHub)
                  ◄──git restore──             ◄──git reset──               ◄──git fetch/pull──
```

Keep this in mind throughout all modules.

---

## Branch strategy used in this repo

```
main (protected — never push directly)
 └── develop  (integration branch)
      ├── feature/<topic>
      ├── fix/<topic>
      ├── docs/<topic>
      └── chore/<topic>
```

---

## Recommended tools

| Tool | Why |
|---|---|
| [VS Code + GitLens](https://marketplace.visualstudio.com/items?itemName=eamodio.gitlens) | Visual diff, blame, history |
| [GitHub CLI (`gh`)](https://cli.github.com/) | Manage PRs from the terminal |
| [lazygit](https://github.com/jesseduffield/lazygit) | Terminal UI for interactive rebase |

Start with module 1 → [01_core_concepts.md](01_core_concepts.md)
