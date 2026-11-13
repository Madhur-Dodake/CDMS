# AGENTS.md

Instructions, conventions, and guidelines for AI agents working in this repository.

---

## 1. Project Context
- **Project**: CDMS (Case / Court Data Management System)
- **Purpose**: Academic Software Engineering project tracking cases, records, and related workflows.

---

## 2. Branch & Git Strategy
- **`main`**: Protected, stable production/release branch. Never commit directly to `main`. Merges into `main` occur only at the end of completed, verified project phases.
- **`dev`**: Default daily working branch. All active development, feature implementations, and incremental commits must be targeted to `dev` (or short-lived feature branches merged into `dev`).
- **Commit Messages**: Follow standard conventional commits format (e.g., `feat: ...`, `fix: ...`, `docs: ...`, `refactor: ...`, `chore: ...`).

---

## 3. Environment & Security
- Never commit credentials, secrets, or API keys. Keep environment-specific settings in `.env`.
- Ensure all virtual environments (`venv`, `.venv`) and dependency trees (`node_modules`) remain ignored by Git.

---

## 4. Code Quality & Standards
- Maintain modular, well-documented code with clear separation of concerns.
- Verify changes compile, build, and pass any relevant unit/integration tests before finalizing tasks.
- Keep documentation up to date with any schema or architectural changes.
