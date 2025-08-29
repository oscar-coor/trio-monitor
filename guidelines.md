# Riktlinjer – Nuvarande fas: Testning, Refaktorering och CI (Aug 2025)

Detta dokument beskriver praktiska riktlinjer för den pågående fasen där fokus är teknisk skuldnedtagning, Pydantic v2/SQLAlchemy 2‑anpassning och stabil CI.

- Status (Aug 2025)
  - Backend kör FastAPI + Pydantic v2 + SQLAlchemy 2 (2.0‑stil) med 10s polling och SQLite‑cache.
  - Admin/tema är implementerat: val av köer/användare, tidsfönster, SLA‑mätning, temaschema och temainställningar.
  - Trio‑anslutningsinställningar (bas‑URL, användare/lösen, API‑token, CC‑ID) kan hanteras via API och uppdaterar auth i runtime.
  
- Mål (denna fas)
  - Kodbasen ska vara Pydantic v2‑kompatibel och ren från legacy‑mönster (json_encoders, .dict()).
  - SQLAlchemy 2.0‑stil används konsekvent (orm.declarative_base, typhjälpmedel, future‑API).
  - CI kör Pytest med coverage, mypy och ruff. Coverage‑rapport publiceras och badges visas i README.
  - Varningsfilter i pytest.ini hålls minimala och skärps efterhand tills testkörning är ren.

- Versionsmål
  - Python 3.12+ (3.13 i matrisen)
  - FastAPI 0.104.1 (enligt `backend/requirements.txt`)
  - Pydantic v2 (2.9.0)
  - SQLAlchemy 2.0.36
  - APScheduler 3.10.4, httpx 0.25.2
  - Pytest 7.4.3 + pytest‑cov, pytest‑asyncio 0.21.1
  - mypy, ruff

- Kodkonventioner (Backend)
  - Pydantic v2
    - Använd .model_dump() istället för .dict().
    - Använd model_config = ConfigDict(...) (INTE class Config) om/ när specialkonfig krävs.
    - Undvik json_encoders; lita på Pydantic v2 standardseriering för datetime/date/time.
  - SQLAlchemy 2
    - Importera declarative_base från sqlalchemy.orm.
    - Följ 2.0‑stilen (typer på kolumner och modeller, ingen deprecated API).
  - FastAPI
    - Type hints på samtliga endpoints och hjälpfunktioner.
    - Depends för beroendeinjektion (auth, db‑sessioner, konfig).
  - Säkerhet och logging
    - Hantera hemligheter i .env (ingen hårdkodning). Logga aldrig hemligheter.
    - Vid behov använd "safe dump" (t.ex. settings.model_dump() med maskering) för loggning.

- Testning
  - Pytest
    - pytest.ini innehåller: registrerade markers (t.ex. integration), addopts "-q" och begränsade filterwarnings.
    - Mål: >= 80% coverage. Kör:
      - Lokalt (i `backend/`): `pytest -q --cov=backend --cov-report=term-missing`
      - CI: genererar coverage.xml (`--cov-report=xml`) och laddar upp som artifact.
     - Tester ligger i `backend/tests/`. Kör tester från mappen `backend/` då pytest.ini ligger där.
  - Varningspolicy
    - Behåll få filter i pytest.ini nu; ta bort/strama efter att koden är helt uppdaterad.
     - Nuvarande filter (i `backend/pytest.ini`) dämpar Pydantic v2‑deprecation kring `Config`, `json_encoders`, `.dict()` samt vissa SQLAlchemy 2‑varningar. Målet är att successivt kunna ta bort dessa.

- CI (GitHub Actions)
  - Workflow: `.github/workflows/python-ci.yml`
  - Matris: Python 3.12 och 3.13.
  - Steg: Install → Pytest m/coverage → ladda upp coverage.xml → mypy → ruff.
  - Artifact: `coverage-xml` (sökväg `backend/coverage.xml`).
  - mypy/ruff körs initialt som non‑blocking (continue-on-error). När baseline är uppnådd görs de blockerande.
  - README innehåller CI‑badge och instruktioner för coverage, mypy, ruff.

- Admin & Tema – funktioner och API
  - Admin (se `backend/admin_api.py`, `backend/admin_service.py`):
    - Lista tillgängliga tjänster: GET `/api/admin/services`.
    - Lista tillgängliga användare: GET `/api/admin/users`.
    - Hantera övervakade köer/tjänster: GET/POST/PUT/DELETE `/api/admin/monitored-services`.
    - Hantera övervakade användare: GET/POST/PUT/DELETE `/api/admin/monitored-users`.
    - Tidsfönster för mätning (vardag/helg mm): GET/PUT `/api/admin/time-windows`.
    - SLA‑statistik: GET `/api/admin/sla-metrics` (filter: service_id, datumintervall).
    - Samlad admin‑konfig: GET `/api/admin/config`.
    - Initiera standardvärden (tema): POST `/api/admin/initialize-defaults`.
  - Anslutningsinställningar till Trio (lagras i DB, maskeras vid GET):
    - GET/PUT `/api/admin/connection-settings`.
    - POST `/api/admin/test-connection` testar aktuell konfiguration och uppdaterar inte state.
  - Tema (se `backend/theme_service.py`):
    - Aktuellt tema/status: GET `/api/theme/current`, GET `/api/theme/status`.
    - Manuellt läge: POST/DELETE `/api/theme/manual-override`.
    - Temaschema (automatiska tider inkl. natt/över‑midnatt): GET/PUT `/api/admin/theme-schedule`.
    - Temainställningar (färger per tema): GET/PUT `/api/admin/theme-settings`.

- Prestanda och Polling
  - Polling varje 10 s. Cache‑TTL i SQLite < 5 s för att minimera externa API‑anrop.
  - APScheduler för schemalagd hämtning, robust felhantering och retries.

- Domänspecifikt (projektmål)
  - 20‑sekunders kötidsgräns; 80% service level.
  - Admin‑konfigurationer för val av köer/användare/SLA och tema‑schema (ljus/mörk) med realtidsuppdatering.

- Kodkvalitet
  - Formatterare: Black (Python) och Prettier (React). Lint: ruff.
  - Konsekvent namngivning och docstrings där det ger värde.

- Migrering och modulval
  - Appen föredrar förbättrade moduler om de finns (`auth_improved.py`, `config_improved.py`, `database_improved.py`, `scheduler_improved.py`) med fallback till legacy.
  - Ny/ändrad kod ska målrikta 2.0‑stilen och Pydantic v2 i de förbättrade modulerna. Lägg inte till ny funktionalitet i legacy utan migrera.

- Lokala kommandon (snabbguide)
  - Installera (från repo‑root): `python -m pip install -r backend/requirements.txt`
  - Kör tester (i `backend/`): `pytest -q --cov=backend --cov-report=term-missing`
  - Starta backend (i `backend/`): `uvicorn app:app --reload`

- PR/Commit‑policy
  - Små, fokuserade PR:s. Beskriv syfte, påverkan och ev. migrationssteg.
  - Kör tester lokalt innan PR. PR ska vara grön i CI.
  - Rekommenderade commit‑prefix: chore, fix, feat, refactor, test, docs, ci.

—

Nedan följer tidigare version (legacy‑referens). Den kommer successivt att bantas när alla delar är uppdaterade.

Backend: Python och FastAPI (Version 3.12+)
För backend-delen, fokusera på FastAPI:s styrkor som typningsstöd och beroendeinjektion. Följ dessa riktlinjer för att undvika vanliga fallgropar och säkerställa prestanda.

Projektstruktur: Organisera koden i moduler för skalbarhet. Använd en struktur som:
text
backend/
├── app.py               # Huvudapp med FastAPI och endpoints
├── config.py            # Konfiguration (URL, credentials via .env)
├── auth.py              # Autentisering
├── api_client.py        # API-anrop till TE API
├── database.py          # SQLite-modeller
├── scheduler.py         # Polling-loop
├── models.py            # Datamodeller
├── tests/               # Tester
├── .env                 # Miljövariabler
└── db.sqlite            # Cache-DB
Detta främjar separation av ansvar och enkel testning.

Typningsstöd och Validering: Använd Python type hints för alla funktioner och endpoints. Detta genererar automatisk dokumentation och validering. Exempel:

text
from fastapi import FastAPI, Depends
from pydantic import BaseModel

class AgentState(BaseModel):
    name: str
    status: str

def get_agents() -> list[AgentState]:
    return [...]  # Hämta data
Undvik att skippa typer för att minska fel.

Beroendeinjektion: Hantera beroenden med FastAPI:s Depends för testbarhet. Exempelvis, injicera autentisering och databasanslutningar.

Felhantering och Säkerhet: Implementera retries för API-fel, HTTPS och tokenhantering i minne. Använd logging och undvik att lagra känslig data i DB.

Prestanda och Polling: Använd APScheduler för asynkron polling. Cache data i SQLite för att minska API-anrop, med en gräns på <5 sekunder för cache.

Tester: Skriv enhetstester med Pytest för auth, polling och endpoints. Täck minst 80% av koden.

Frontend: React (Version 18+)
För React-delen, prioritera funktionella komponenter, hooks och responsiv design för att matcha projektets krav på realtidsuppdateringar och svenskt gränssnitt.

Komponentstruktur: Använd funktionella komponenter med hooks. Exempel:

text
import { useEffect, useState } from 'react';
import Chart from 'chart.js/auto';

function Dashboard() {
  const [data, setData] = useState(null);

  useEffect(() => {
    // Polla backend
    const fetchData = async () => {
      const res = await fetch('/api/stats');
      setData(await res.json());
    };
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  return <div>{data && <Chart data={data} />}</div>;
}
Detta säkerställer reaktivitet och enkel state-hantering.

Projektstruktur: Organisera som:

text
frontend/
├── src/
│   ├── App.js           # Huvudkomponent
│   ├── components/      # Dashboard.js, AdminView.js
│   ├── services/        # Axios-klient
│   └── index.js         # Entry point
├── public/              # Statiska filer
└── package.json         # Beroenden
Håll komponenter återanvändbara och modulära.

State Management: Använd useState och useEffect för lokal state. För komplexa fall, integrera Context API eller Redux. Undvik onödiga re-renders med useMemo.

UI och Responsivitet: Använd Bootstrap eller Material-UI för responsiv design. Implementera svenskt språk via konstanter (t.ex. {label: "Agentstatus"}). Färgkodning för status (grönt för ledig, rött för upptagen).

Säkerhet och Prestanda: Validera input med React Hook Form. Optimera polling med Axios och hantera fel med retries.

Tester: Använd Jest för komponenttester. Täck interaktioner och state-ändringar.

Allmänna Riktlinjer för AI-Kodagenten
AI-Specifika Principer: Agenten bör följa en "plan-act-observe"-cykel: Skapa en plan, generera kod, testa och iterera. Använd reflektion för att fixa fel autonomt.

Säkerhet och Etik: Undvik hårdkodade hemligheter; använd .env. Säkerställ att koden är fri från sårbarheter som XSS.

Dokumentation och Läsbarhet: Kommentera kod och använd konsekventa namngivningar. Formatera med Black för Python och Prettier för React.

Integration med Projektet: Bygg på befintlig arkitektur från konversationen, som polling var 10:e sekund och caching. Inkludera 20-sekunders kötidsgräns med visuella indikatorer.