# Git & GitHub Tutorial — Overview

> **Audience:** Technical colleagues who know Python but are new to structured Git workflows.  
> **Repo context:** We use `SegmentationReview` as a concrete, familiar example throughout.

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
| 6 | **Rebase** — interactive rebase, squash, fixup | `06_rebase.md` |
| 7 | **GitHub Actions CI** — automated checks on PRs | `07_ci_github_actions.md` |
| 8 | **Practical exercises** — hands-on tasks | `08_exercises.md` |

---

## How to follow along

```bash
# Fork this repo on GitHub, then clone your fork
git clone https://github.com/<your-username>/SegmentationReview.git
cd SegmentationReview

# Set the original as "upstream" so you can pull updates
git remote add upstream https://github.com/your-org/SegmentationReview.git
git remote -v
```

You'll work through the exercises in module 8 using this repo as your sandbox.

---

## Mental model

```
Working directory  ──git add──►  Staging area  ──git commit──►  Local repo  ──git push──►  Remote (GitHub)
                  ◄──git restore──             ◄──git reset──               ◄──git fetch/pull──
```

Keep this diagram in mind as you go through the modules.

---

## Recommended tools

| Tool | Why |
|---|---|
| [VS Code + GitLens](https://marketplace.visualstudio.com/items?itemName=eamodio.gitlens) | Visual diff, blame, history |
| [GitHub CLI (`gh`)](https://cli.github.com/) | Manage PRs from the terminal |
| [lazygit](https://github.com/jesseduffield/lazygit) | Terminal UI for Git — great for interactive rebase |

Start with module 1 → [01_core_concepts.md](01_core_concepts.md)
