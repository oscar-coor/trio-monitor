# ADMIN GUIDE – Konfiguration och Användning

Denna guide beskriver hur du använder admin-gränssnittet för att konfigurera övervakning, servicenivåer, tidsfönster och tema-schema i Trio Monitor.

## Översikt
- Admin-UI levererar CRUD för övervakade köer och användare, SLA/varningsnivåer samt tidsstyrd tema-växling.
- Uppdateringar träder i kraft direkt; backend pollar var 10:e sekund och använder cache TTL <5 s.
- Inline-bekräftelser används (ej blockerande popups) för säkrare UX.

## Förutsättningar
- Backend körs och är nåbar via `/api`.
- Du har korrekta behörigheter och autentisering enligt organisationens policy.

## 1) Övervakade köer och användare
- Lägg till eller ta bort köer under "Övervakning > Köer".
- Lägg till eller ta bort användare under "Övervakning > Användare".
- Ändringar sparas med inline-bekräftelse (gul bekräftelserad med knappar). Ingen `window.confirm` används.

Tips:
- Håll listorna fokuserade på relevanta objekt för att minska brus i dashboarden.

## 2) Servicenivåer och varningsnivåer
- Ange `QUEUE_TIME_LIMIT` (t.ex. 20 s) och `SERVICE_LEVEL_TARGET` (t.ex. 80%).
- Ange förvarningsnivå (t.ex. `WARNING_THRESHOLD` = 18 s) för att kunna agera innan gräns passeras.
- Backend följer dessa värden vid aggregering av `/api/stats` och varningslogik.

## 3) Tidsfönster (monitoreringsperioder)
- Definiera tidsfönster per veckodag (mån–sön) när övervakningen ska vara aktiv.
- Inmatning är härdad: numeriska fält valideras och veckodagar normaliseras.
- Felmeddelanden visas inline; korrigera och spara igen.

Rekommendationer:
- Använd lokala tider enligt verksamhetens öppettider.
- Planera buffertar runt öppning/stängning för att fånga upp eftersläpningar.

## 4) Tema-schema (ljus/mörk)
- Aktivera automatisk tema-växling och ange starttider för ljus och mörk.
- UI växlar i realtid enligt backend-konfigurationen.
- Numeriska inmatningar valideras; fel visas inline.

## 5) Varningspanelen
- Varningslistan är begränsad till de senaste 100 posterna och auto-scrollar till botten när nya varningar kommer.
- Använd varningarna som operativa signaler och justera bemanning eller routing.

## 6) Bekräftelser och återställning
- Alla destruktiva åtgärder (t.ex. radera kö/användare) använder inline-bekräftelserader.
- Klicka "Avbryt" eller utanför för att avbryta; "Bekräfta" för att spara.

## 7) Felsökning
- Frontend visar varningar inline. Kontrollera också webbkonsolens loggar.
- Backend-loggar: `journalctl -u trio-backend -f` (prod) eller terminal i dev.
- Vanliga orsaker:
  - Backend ej nåbar → kontrollera `trio-backend`/Nginx-proxy.
  - CORS/blockad → uppdatera `ALLOWED_ORIGINS`/`FRONTEND_URL`.
  - Ogiltig indata → rätta enligt felmeddelanden, spara igen.

## 8) Bästa praxis
- Håll SLA- och varningsnivåer realistiska. 80/20 är standard men kan justeras.
- Minimera antalet övervakade objekt vid hög trafik för bästa prestanda.
- Granska varningsmönster veckovis och anpassa bemanning.
