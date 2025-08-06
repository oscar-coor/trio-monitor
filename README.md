# Trio Monitor - Realtidsövervakning för Trio Enterprise API

Ett modernt dashboard för realtidsövervakning av kötider i kontaktcenter med fokus på 20-sekunders gränsen och servicenivåmål på 80%.

## 🎯 Huvudfunktioner

- **Realtidsövervakning** - Uppdateras var 10:e sekund
- **20-sekunders kötidsgräns** - Kritisk övervakning med färgkodade varningar
- **Servicenivåmål** - 80% av samtal besvarade inom 20 sekunder
- **Agentövervakning** - Status och prestanda för alla agenter
- **Historiska data** - Trender och analys över tid
- **Responsiv design** - Fungerar på alla enheter

## 🏗️ Arkitektur

### Backend (Python + FastAPI)
```
backend/
├── app.py               # Huvudapp med FastAPI endpoints
├── config.py            # Konfiguration via .env
├── auth.py              # Autentisering mot Trio Enterprise API
├── api_client.py        # API-anrop och datahantering
├── database.py          # SQLite för caching och historik
├── scheduler.py         # Polling-loop var 10:e sekund
├── models.py            # Datamodeller med Pydantic
├── tests/               # Enhetstester
├── requirements.txt     # Python-beroenden
└── .env                 # Miljövariabler
```

### Frontend (React 18+)
```
frontend/
├── src/
│   ├── App.js           # Huvudkomponent
│   ├── components/      # Dashboard-komponenter
│   │   ├── Dashboard.js
│   │   ├── Header.js
│   │   ├── QueueTable.js
│   │   ├── AgentTable.js
│   │   ├── MetricsChart.js
│   │   └── AlertContainer.js
│   ├── services/        # API-klient
│   └── index.js         # Entry point
├── public/              # Statiska filer
└── package.json         # NPM-beroenden
```

## 🚀 Installation och Setup

### 1. Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

Konfigurera `.env` filen:
```env
TRIO_API_BASE_URL=https://your-trio-api-url.com
TRIO_API_USERNAME=your_username
TRIO_API_PASSWORD=your_password
TRIO_API_TOKEN=your_api_token

DATABASE_URL=sqlite:///./db.sqlite
POLLING_INTERVAL=10
QUEUE_TIME_LIMIT=20
WARNING_THRESHOLD=18
SERVICE_LEVEL_TARGET=80
```

Starta backend:
```bash
python app.py
```

Backend körs på `http://localhost:8000`

### 2. Frontend Setup

```bash
cd frontend
npm install
npm start
```

Frontend körs på `http://localhost:3000`

## 📊 Dashboard-funktioner

### Huvudmått
- **Totala Agenter** - Antal aktiva agenter
- **Väntande Samtal** - Aktuella samtal i kö
- **Längsta Väntetid** - Kritisk indikator med färgkodning
- **Servicenivå** - Procentandel mot 80%-målet

### Köstatus (Färgkodning)
- 🟢 **Bra** - Under 15 sekunder
- 🟡 **Varning** - 15-20 sekunder  
- 🔴 **Kritisk** - Över 20 sekunder

### Realtidsdata
- **Kötabell** - Detaljerad status för alla köer
- **Agenttabell** - Status och prestanda per agent
- **Trenddiagram** - Historiska väntetider
- **Varningar** - Automatiska alerts vid gränsöverskridanden

## 🔧 API Endpoints

### Backend REST API

- `GET /` - Grundläggande info
- `GET /health` - Hälsokontroll
- `GET /api/dashboard` - Komplett dashboard-data
- `GET /api/agents` - Agentstatus
- `GET /api/queues` - Kömetriker
- `GET /api/service-level` - Servicenivådata
- `GET /api/alerts` - Aktiva varningar
- `GET /api/stats` - Systemstatistik
- `GET /api/historical/{queue_id}` - Historisk data
- `POST /api/alerts/{alert_id}/acknowledge` - Bekräfta varning

## 🎨 Design och UX

### Färgschema
- **Primär**: Blå gradient för header
- **Framgång**: Grön för bra status
- **Varning**: Gul för varningsnivå
- **Kritisk**: Röd för kritiska situationer

### Responsiv Design
- **Desktop**: Fullständig dashboard-layout
- **Tablet**: Anpassad kolumnlayout
- **Mobil**: Staplade kort och tabeller

### Svenskt Gränssnitt
- Alla texter på svenska
- Svenska datumformat
- Lokaliserade tidsformat

## 🧪 Testning

### Backend-tester
```bash
cd backend
pytest tests/
```

### Frontend-tester
```bash
cd frontend
npm test
```

## 📈 Prestanda och Skalning

- **Caching**: SQLite för att minska API-anrop
- **Polling**: Optimerad 10-sekunders intervall
- **Databas**: Automatisk rensning av gammal data
- **Frontend**: Effektiv state-hantering med React hooks

## 🔒 Säkerhet

- **API-autentisering**: Token-baserad säkerhet
- **CORS**: Konfigurerad för säker frontend-kommunikation
- **Miljövariabler**: Känslig data i .env-filer
- **Input-validering**: Pydantic-modeller för datavalidering

## 📱 Användningsområden

### För Telefonister
1. **Proaktiv arbetsbelastningsbalansering**
2. **Personlig prestationscoaching**
3. **Stressreducering genom förutsägbarhet**
4. **Kvalitetsfokuserade pauser**
5. **Teamsamordning för komplexa ärenden**

### För Företagsledning
6. **Gamification och incitamentsprogram**
7. **Prediktiv personalplanering**
8. **Kundnöjdhetsoptimering**
9. **Kostnadseffektiv kapacitetsplanering**
10. **Compliance och kvalitetssäkring**

## 🔮 Framtida Utveckling

- **AI-driven analys** för prediktiv kövolym
- **Omnikanalintegration** (chat, e-post, sociala medier)
- **Mobilapp** för remote-övervakning
- **Avancerad rapportering** med exportfunktioner
- **Integrationer** med andra kontaktcenter-system

## 🆘 Felsökning

### Vanliga Problem

**Backend startar inte:**
- Kontrollera .env-konfiguration
- Verifiera Python-version (3.12+)
- Installera beroenden: `pip install -r requirements.txt`

**Frontend ansluter inte:**
- Kontrollera att backend körs på port 8000
- Verifiera proxy-inställningar i package.json
- Kontrollera CORS-konfiguration

**Ingen data visas:**
- Kontrollera Trio API-anslutning
- Verifiera autentiseringsuppgifter
- Kolla backend-loggar för fel

## 📞 Support

För teknisk support och frågor, kontakta utvecklingsteamet eller skapa en issue i projektets repository.

---

**Trio Monitor** - Utvecklad för optimal kontaktcenter-prestanda med fokus på 20-sekunders servicenivå och 80% måluppfyllelse.
