---
trigger: always_on
---

# Riktlinjer – Nuvarande fas: Testning, Refaktorering och CI (Aug 2025)

Detta dokument beskriver praktiska riktlinjer för den pågående fasen där fokus är teknisk skuldnedtagning, Pydantic v2/SQLAlchemy 2‑anpassning och stabil CI.

- Mål (denna fas)
  - Kodbasen ska vara Pydantic v2‑kompatibel och ren från legacy‑mönster (json_encoders, .dict()).
  - SQLAlchemy 2.0‑stil används konsekvent (orm.declarative_base, typhjälpmedel, future‑API).
  - CI kör Pytest med coverage, mypy och ruff. Coverage‑rapport publiceras och badges visas i README.
  - Varningsfilter i pytest.ini hålls minimala och skärps efterhand tills testkörning är ren.

- Versionsmål
  - Python 3.12+ (3.13 i matrisen)
  - FastAPI senaste kompatibla i requirements
  - Pydantic v2
  - SQLAlchemy 2.0.36
  - Pytest + pytest-cov
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
      - Lokalt: pytest -q --cov=backend --cov-report=term-missing
      - CI: genererar coverage.xml och laddar upp som artifact.
  - Varningspolicy
    - Behåll få filter i pytest.ini nu; ta bort/strama efter att koden är helt uppdaterad.

- CI (GitHub Actions)
  - Matris: Python 3.12 och 3.13.
  - Steg: Install → Pytest m/coverage → ladda upp coverage.xml → mypy → ruff.
  - mypy/ruff körs initialt som non‑blocking (continue-on-error). När baseline är uppnådd görs de blockerande.
  - README innehåller CI‑badge och instruktioner för coverage, mypy, ruff.

- Prestanda och Polling
  - Polling varje 10 s. Cache‑TTL i SQLite < 5 s för att minimera externa API‑anrop.
  - APScheduler för schemalagd hämtning, robust felhantering och retries.

- Domänspecifikt (projektmål)
  - 20‑sekunders kötidsgräns; 80% service level.
  - Admin‑konfigurationer för val av köer/användare/SLA och tema‑schema (ljus/mörk) med realtidsuppdatering.

- Kodkvalitet
  - Formatterare: Black (Python) och Prettier (React). Lint: ruff.
  - Konsekvent namngivning och docstrings där det ger värde.

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