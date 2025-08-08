# Trio Monitor – Systemöversikt och Progressionsplan

## 1) Systemöversikt
- Syfte: Realtidsmonitorering av Trio Enterprise köer och agentstatus, med larm vid >20 s kötid och uppföljning mot 80% service level. Konfigurerbar övervakning (köer/användare), SLA‑nivåer, tidsfönster och schemalagd tema‑växling.
- Målgrupp: Operatörer (driftsvy), Teamledare (SLA/historik), IT/Säkerhet (driftbarhet), Produkt/PM (prioritering).
- KPI: Service Level (<20 s, mål 80%), genomsnittlig kötid, längst väntetid, kölängd, agenttillgänglighet, UI TTI <1 s, datafärskhet <10 s.

## 2) Arkitekturöversikt
- Frontend: React 18, Bootstrap, Chart.js, Axios. Funktionella komponenter + hooks. 10 s polling. Tema‑system (ljus/mörk) med tidsstyrd auto‑växling.
- Backend: FastAPI (Python 3.12+), httpx, APScheduler (10 s polling), SQLite (cache + historik), Pydantic/typing, Depends/DI, .env för konfig/credentials. CORS, logging, retries, timeouts.
- Dataflöde:
  1) APScheduler triggar polling → api_client hämtar Trio (httpx + retries/timeout)
  2) database skriver cache/historik (TTL <5 s)
  3) Endpoints exponerar aggregerad status (dashboard) + admin‑CRUD
  4) Frontend hämtar `/api/stats` var 10 s; admin anropar `/api/admin/*`

## 3) Backenddesign (moduler)
- `app.py`: FastAPI‑app, routers, CORS, health
- `config.py`: .env (.API_URL, tokens, polling, cache_TTL, TZ)
- `auth.py`: Trio‑auth, token i minne, förnyelse/retries
- `api_client.py`: httpx‑klient, timeouts + exponentiell backoff
- `database.py`: SQLite, session, CRUD för cache/historik
- `models.py`: SQLAlchemy‑modeller + Pydantic‑scheman
- `scheduler.py`: APScheduler‑jobb, isolera fel, robust körning
- `tests/`: Pytest (auth, polling, endpoints, tidsfönster/SLA)
- Endpoints (exempel):
  - GET `/api/health`
  - GET `/api/stats`
  - GET `/api/metrics/sla?from=&to=&window=`
  - Admin: `/api/admin/{queues,users,sla,timewindows,theme-schedule}`

## 4) Datamodell (SQLite, föreslagen)
- `queues(id, trio_queue_id, name, active)`
- `users(id, trio_user_id, name, active)`
- `queue_snapshots(id, queue_id, ts_utc, waiting_count, longest_wait_sec, avg_wait_sec)`
- `agent_snapshots(id, user_id, ts_utc, status, calls_in_progress)`
- `sla_config(id, threshold_sec=20, target_pct=80)`
- `time_windows(id, day_type=weekday|weekend, start_local, end_local)`
- `theme_schedule(id, light_start_local, dark_start_local, enabled)`
- `selections`: `monitored_queues(queue_id)`, `monitored_users(user_id)`
- Not: Inga hemligheter i DB; tokens hålls i minne/miljö.

## 5) Frontenddesign
- Struktur: `App.js`, `components/{Dashboard, QueueTable, AgentTable, AdminView/*}`, `services/api.js`
- Dashboard: KPI‑kort, tabeller, grafer (Chart.js), färgkodning (grön/röd), 10 s polling
- Admin: CRUD för köer, användare, SLA, tidsfönster, tema‑schema. Validering med React Hook Form
- Tema: CSS‑variabler, ThemeContext, realtidsbyte enligt backend‑schema

## 6) Säkerhet och resiliens
- HTTPS (Test/Prod), CORS, inga hemligheter i repo/DB, tokenrotation
- httpx retries (ex. 3×) och korta timeouts
- Degraderat läge: servera senaste cache med tidsstämpel

## 7) Test och observability
- Backend: Pytest (auth, api_client m. retries, scheduler m. mock, endpoints, tidsfönster, SLA). Coverage ≥80%
- Frontend: Jest/RTL (KPI/diagram, polling, tema, admin‑formulär)
- Loggning: strukturerad (gärna JSON) för polling latency, cache hit rate, API‑felgrad, SLA‑avvikelser

## 8) Drift och deployment
- Miljöer: Dev → Test → Prod; konfig via .env per miljö
- CI/CD: Lint, test, coverage‑gate; build frontend; paketera backend (ev. Docker); deploy
- Historik‑retention och DB‑rotation efter behov

## 9) Risker och åtgärder
- API‑limits/latens → cache <5 s, backoff, timeouts
- Tidszon/klocka → UTC internt, lokal visning; server‑tid som källa
- UI‑prestanda → memoization, selektiv re‑render, pagination/virtualisering
- Scope creep → definiera icke‑mål och change control

## 10) Progressionsplan (milstolpar, leverabler, DoD)
- M1 Grundplattform (1–1.5 v)
  - Backend skelett (FastAPI, CORS, health), httpx‑klient, APScheduler dummy, SQLite setup/schema
  - Frontend init (React 18, Bootstrap, Axios, Dashboard skeleton)
  - DoD: Health OK, första polling skriver till DB, dashboard renderar statiska kort
- M2 Realtidsmonitorering (1.5–2 v)
  - Trio‑anrop, cache/TTL, `/api/stats` aggregering, felhantering
  - Dashboard med kö/agentstatus, färgkod, 10 s polling i UI
  - DoD: Löpande uppdatering, indikator >20 s, degraderat läge fungerar
- M3 SLA och historik (1.5–2 v)
  - Historiktabeller, SLA‑beräkning inom tidsfönster, trender/grafer, export (CSV)
  - DoD: SLA‑vy med 80%‑mål över vald period
- M4 Admin‑gränssnitt (1–1.5 v)
  - DB‑schema och endpoints: queues/users/SLA/timewindows/theme‑schedule
  - Admin‑UI CRUD + validering; koppling till pollinglogik
  - DoD: Konfigurerbar övervakning utan kodförändringar
- M5 Tema‑schema & härdning (1 v)
  - Auto ljus/mörk tema, realtidsbyte; prestandaoptimering; fler tester
  - DoD: Stabil upplevelse dag/natt, coverage ≥80%
- M6 Release & drift (0.5–1 v)
  - Dokumentation, körmanual, CI/CD, miljö‑.env, observability och larm
  - DoD: Test/Prod‑release enligt checklista

## 11) Backlog (epics → exempel)
- Data/Cache: cache <5 s; backoff
- Dashboard: röd indikator vid >20 s; historikgrafer
- SLA/Analys: 80%‑mål per dag/vecka; tidfönsterlogik
- Admin: välja köer/användare; sätta SLA/tidfönster; temaschema
- Tema: auto‑växling efter klockslag
- Kvalitet & Säkerhet: ≥80% test; säker konfig

## 12) RACI (översikt)
- Utveckling: Responsible; Tech lead: Accountable; IT/Drift/Sec: Consulted; Operatörer/Teamledare: Informed

## 13) Öppna frågor
- Trio endpoints och rate limits per miljö? Roll-/behörighetsmodell för admin? Historik‑retention och rapportkrav (exportformat, periodisering)? Driftform (Docker/on‑prem/cloud) och certifikat/PKI?
"@ -Encoding UTF8