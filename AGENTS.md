# Repository Guidelines

## Project Structure & Module Organization
This repository is currently in bootstrap state (no committed source tree yet). Use this layout as you add code:
- `src/` for application or library code
- `tests/` for automated tests mirroring `src/` paths
- `assets/` for static files (images, fixtures, sample data)
- `docs/` for design notes, architecture decisions, and onboarding docs

Keep modules focused and small. Prefer feature-oriented folders when multiple components appear (example: `src/auth/`, `src/api/`).

## Build, Test, and Development Commands
No build system is configured yet. Until one is added, use baseline repository checks:
- `git status` shows pending changes before commits
- `git diff` reviews edits locally
- `rg "pattern" src tests` searches code quickly

When introducing a toolchain, add explicit scripts/targets and update this file with one-command workflows (for example: `make test` or `npm test`).

## Coding Style & Naming Conventions
- Use 4 spaces for indentation unless the language standard requires otherwise
- Use UTF-8 text and Unix line endings (`LF`)
- Name files and directories consistently; prefer `snake_case` for Python-style projects and `kebab-case` for config/docs files
- Keep functions small, side effects explicit, and public APIs documented

If you add formatters or linters, commit their config and run them before opening a PR.

## Testing Guidelines
- Place tests in `tests/` with paths matching the code under test
- Name tests clearly by behavior (example: `tests/api/test_login_flow.py`)
- Add regression tests for every bug fix
- Aim for meaningful coverage of critical paths, not only line-count targets

Document test commands in this file as soon as a framework is chosen.

## Commit & Pull Request Guidelines
With no existing history yet, adopt this convention now:
- Commit format: `type(scope): short imperative summary` (example: `feat(auth): add token validator`)
- Keep commits focused and atomic
- Reference issue IDs in commit/PR descriptions when applicable

PRs should include:
- What changed and why
- Test evidence (commands + results)
- Screenshots or logs for UI/behavioral changes
- Any follow-up work or known limitations
