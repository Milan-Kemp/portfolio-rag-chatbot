# Job Alert Automation

Een dagelijkse automation die vacatures ophaalt via de Adzuna API, ze met 
de Claude API scoort tegen mijn eigen criteria, en de beste matches mailt. 
Draait zelfstandig via GitHub Actions, elke ochtend.

## Mijn rol

Gebouwd om mijn eigen sollicitatieproces te automatiseren. Ik schreef de
architectuur en een gedetailleerde technische spec, inclusief edge cases zoals
API-limieten en dubbele meldingen. Claude Code implementeerde de Python.

## Architectuur

De pipeline bestaat uit vier stappen die na elkaar draaien:
1. fetch_jobs.py haalt vacatures op via Adzuna, gefilterd op zoektermen en 
   locatie (60km rond Purmerend, of remote/hybride)
2. Filter: vacatures die al eerder beoordeeld zijn (seen_jobs.json) worden 
   overgeslagen, zodat Claude ze niet elke dag opnieuw hoeft te scoren
3. score_jobs.py stuurt de nieuwe vacatures in één Claude API-call naar het 
   model, met mijn scoringscriteria uit config.yaml, en krijgt gestructureerde 
   JSON terug: score 1-10, motivatie, matches en mismatches per vacature
4. send_email.py mailt de top 3 vacatures boven de drempelscore

## Het probleem: te weinig resultaten

Na de eerste paar dagen kreeg ik bijna geen mails meer. Uit de GitHub Actions 
logs bleek dat mijn zoekradius (aanvankelijk 30km) en zoektermen te smal 
waren: dezelfde paar vacatures werden op dag 1 al opgehaald en als 
"beoordeeld" gemarkeerd in seen_jobs.json, waardoor er op dag 2 simpelweg 
niks nieuws overbleef om te scoren.

## De oplossing

Ik verruimde de radius naar 60km en breidde de zoektermen uit met bredere, 
minder overlappende termen (junior software developer, AI engineer, junior 
developer). Ik voegde ook logging toe die per zoekterm laat zien hoeveel 
resultaten Adzuna teruggaf, zodat ik in het vervolg zelf kan zien welke 
termen niks opleveren.

Een tweede probleem kwam daarna naar boven: de threshold bleek te streng. 
Met de bredere zoekopdracht kwamen er wel 15 nieuwe vacatures binnen, maar 
geen enkele haalde de drempelscore van 6. De motivaties lieten een duidelijk 
patroon zien: vacatures waren óf te senior (3+ jaar ervaring), óf vroegen 
zelf programmeren in talen als PHP/C#/Node.js die niet bij mijn profiel 
passen, óf waren sales/consultancy-rollen met AI als marketing-laagje.

## Resultaat

De aangepaste versie leverde binnen een paar dagen een eerste sterke match 
op: een afstudeerstage AI Solutions Engineer met een score van 8/10, exact 
aansluitend bij mijn profiel (AI-agents bouwen met Microsoft Copilot, 
stage/starter-niveau).

## Tech stack

Python, Adzuna API, Claude API (gestructureerde JSON-output via json_schema), 
GitHub Actions (cron + workflow_dispatch voor handmatig testen), Gmail SMTP 
met app-specifiek wachtwoord voor verzending.