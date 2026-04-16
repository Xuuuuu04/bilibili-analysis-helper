# Project Structure

Updated: 2026-02-07

## Top-level Layout
```text
.
- .env.example
- .gitignore
- CONTRIBUTING.md
- LICENSE
- README.md
- README_EN.md
- README_JP.md
- asgi.py
- assets
- docs
- pyproject.toml
- requirements.txt
- src
- tests
```

## Conventions
- Keep executable/business code under src/ as the long-term target.
- Keep docs under docs/ (or doc/ for Cangjie projects).
- Keep local runtime artifacts and secrets out of version control.
