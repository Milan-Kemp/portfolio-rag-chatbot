# Portfolio RAG Chatbot

Een Retrieval-Augmented Generation chatbot die bezoekers vragen laat stellen over
mijn projecten, zoals "hoe loste Milan onderwerpherhaling op in de LinkedIn
pipeline?". Het antwoord komt uitsluitend uit mijn eigen case studies, met de bron
erbij. Staat een antwoord niet in mijn teksten, dan zegt de bot dat, in plaats van
iets te verzinnen. Live gehost op AWS en als widget ingebouwd in mijn portfolio:
dit is de chatbot waarmee je nu praat.

## Waarom dit project

RAG komt steeds terug in de vacatures waar ik naar kijk, en het was een vaardigheid
die ik nog niet kon laten zien. Dit project dicht dat gat, en het is meteen een
werkend onderdeel van mijn portfolio.

## Mijn rol

Ik bepaalde de architectuur en schreef de specificatie: wat de pipeline moet doen,
welke onderdelen erin zitten, wat er niet in hoort (geen cloud-vectorstore, geen
fine-tuning) en waar het mis kan gaan. Claude Code implementeerde dat. Ik testte
elke stap zelf, stuurde bij op wat ik zag, en nam de uitrol op AWS persoonlijk door.

## Hoe het werkt

1. Inlezen: mijn teksten worden in stukken van ongeveer 400 tokens geknipt, op de
   kopjes in de tekst, zodat elk stuk over één onderwerp gaat.
2. Opzoeken: de vraag van de bezoeker wordt omgezet in een vector en vergeleken met
   de stukken in een lokale ChromaDB. De vier meest relevante gaan door.
3. Antwoorden: Claude krijgt alleen die vier stukken en de opdracht om daar
   uitsluitend op te antwoorden en de bron te noemen.

## Problemen waar ik tegenaan liep

- Mijn eigen bestanden werden niet gevonden. Ik had mijn teksten als .txt
  opgeslagen, maar de pipeline las alleen .md. Twee bestanden waren daarbij nog
  leeg. Ik paste de ingest aan en liet hem lege bestanden melden in plaats van
  stil overslaan.
- Gratis API-limiet. Voyage staat zonder betaalmethode maar 3 aanvragen per minuut
  toe. Tijdens het testen liep ik daar direct tegenaan. Ik leerde het verschil
  tussen een bug en een limiet herkennen.
- Slechte weergave van letters in de terminal. Op Windows werden ë en é verminkt.
  Het zat in de weergave, niet in de data. De fix was UTF-8 afdwingen bij het
  printen.
- Docker startte niet. Docker Desktop ontbrak een onderdeel van Windows (WSL). Na
  installeren en herstarten draaide alles.
- Voorbeeldtekst als echte key. Op de server stond in mijn .env nog de
  placeholder-tekst in plaats van mijn echte keys. De fout "API key invalid" leek
  een Voyage-probleem. Een simpele controle van de lengte van de keys liet zien wat
  er mis was.
- Server onbereikbaar ondanks certificaat. Mijn security group in AWS stond alleen
  poort 22 open, niet 80 en 443. In de logs van de proxy stond het letterlijk:
  "likely firewall problem". Na het openzetten van die poorten kwam het certificaat
  er meteen.
- Een privésleutel in een projectmap. Mijn SSH-sleutel stond even in de
  projectmap, waar hij per ongeluk op GitHub of in een Docker-image had kunnen
  belanden. Ik zette hem veilig en liet git en Docker .pem-bestanden negeren.

## Keuzes die ik bewust maakte

- Antwoord alleen uit mijn teksten. De grens "dit staat niet in mijn teksten" vind
  ik de kern van RAG. Een vraag over mijn opleiding, die niet in mijn content
  staat, beantwoordt de bot dan ook met precies dat, plus wat hij wel kan
  vertellen.
- Embedding-cache. Embeddings kosten geld per aanroep. Door ze op te slaan per
  stukje tekst betaal ik bij een update alleen voor wat veranderd is.
- Rate limit. Zodra het endpoint publiek werd, voegde ik een limiet toe per
  bezoeker en een dagelijks maximum voor iedereen samen. Zo ligt mijn maximale
  Claude-kosten vast, ook als iemand de bot probeert te spammen.
- Eén kleine server. Docker met Caddy op één AWS t3.micro in Frankfurt, met een
  vast IP en HTTPS. Geen load balancer of autoscaling: dit is een portfolio-demo,
  geen productiesysteem. Lokaal gebruikte alles samen ongeveer 130 MB geheugen.

## Wat ik geleerd heb

- Hoe een RAG-pipeline in elkaar zit, van chunking en embeddings tot retrieval en
  een system prompt die het model aan zijn bronnen bindt.
- Dat de kwaliteit van het antwoord afhangt van de kwaliteit en hoeveelheid van
  mijn eigen teksten, meer dan van de code. Bij te weinig content schiet de bot
  tekort, en dat is dan een contentprobleem.
- Een app verpakken met Docker en uitrollen op AWS: server, firewall, vast IP,
  domeinnaam en automatisch HTTPS.
- Lezen van logs in plaats van gokken. Bijna elk probleem stond letterlijk in de
  foutmelding.
- Veiligheid bij het publiek maken van een API: keys buiten git en Docker, een
  CORS-allowlist en een limiet op gebruik.

## Resultaat

Een chatbot die live draait op een vast adres, met HTTPS, en als widget in mijn
portfolio staat. Hij beantwoordt vragen over mijn projecten met bronvermelding en
zegt eerlijk wanneer iets niet in mijn teksten staat.

## Tech stack

Python 3.13, FastAPI en Uvicorn, ChromaDB (lokaal, persistent), Voyage AI
(embeddings), Claude API (antwoorden), slowapi (rate limiting), Docker en Docker
Compose, Caddy (reverse proxy en automatisch HTTPS), AWS EC2 (Ubuntu), DuckDNS
(domein), vanilla JavaScript (widget), GitHub Pages (hosting van de site).
