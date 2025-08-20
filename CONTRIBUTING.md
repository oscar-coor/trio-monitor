# CONTRIBUTING

Tack för att du vill bidra! Följ dessa riktlinjer för en smidig utvecklingsprocess.

## Krav och versioner
- Python 3.12+ (3.13 i CI-matris)
- FastAPI, Pydantic v2, SQLAlchemy 2.0-stil
- Pytest + pytest-cov, mypy, ruff
- Node.js 18+ för frontend

## Setup (lokalt)
```bash
# Backend
cd backend
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

## Kodkonventioner
- Pydantic v2: använd `model_dump()` i stället för `.dict()`.
- SQLAlchemy 2: moderna typer och deklarativ stil från `sqlalchemy.orm`.
- FastAPI: tydliga type hints och `Depends` för beroenden.
- Inga hemligheter i kod/DB; använd `.env` (Pydantic `SecretStr`).

## Tester och kvalitet
- Pytest (mål ≥80% coverage):
```bash
cd backend
pytest -q --cov=backend --cov-report=term-missing
```
- Generera XML som i CI:
```bash
pytest -q --cov=backend --cov-report=xml
```
- mypy (icke-blockerande i CI just nu):
```bash
cd backend
mypy .. --config-file ../mypy.ini
```
- ruff:
```bash
ruff check .
```

## CI (GitHub Actions)
- Workflow: `.github/workflows/python-ci.yml`
  - Matris: Python 3.12, 3.13
  - Steg: pytest m/coverage → ladda upp `coverage.xml` → mypy → ruff
  - mypy/ruff är `continue-on-error` tills baslinje är grön

## Brancher och PR
- Små, fokuserade PR:er; beskriv syfte, påverkan, ev. migration
- Kör tester lokalt innan PR; CI ska bli grön
- Commit-prefix: `chore`, `fix`, `feat`, `refactor`, `test`, `docs`, `ci`

## Katalogstruktur (översikt)
- Backend: `backend/` (FastAPI, config, auth, api_client, database, scheduler, models, tests)
- Frontend: `frontend/` (React 18, Bootstrap, services, components)

## Support
Skapa en issue i repo:t om du stöter på problem. Tack för ditt bidrag!
