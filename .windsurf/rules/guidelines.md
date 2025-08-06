---
trigger: always_on
---

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