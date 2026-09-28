# Chatbot online zetten op AWS (stap voor stap)

Doel: de chatbot draait op `https://milan-bot.duckdns.org` en je portfolio-site
op GitHub Pages kan hem aanroepen.

Je hebt nodig: een creditcard (voor AWS), je API-keys, en ongeveer 45 minuten.
Alle opdrachten die je "in PowerShell" typt, typ je op je eigen pc. Opdrachten
"op de server" typ je in het venster dat verbonden is met AWS (vanaf stap 5).

---

## Kosten en veiligheid (lees dit eerst)

- **AWS**: nieuwe accounts krijgen een gratis periode (tegoed of gratis tier).
  Daarna kost een t3.micro met vast IP-adres ongeveer **€12-15 per maand**.
  Controleer op het scherm bij aanmelden wat er voor jouw account geldt.
- **Zet direct een budgetalarm** (stap 1), dan krijg je een mail als de kosten
  oplopen.
- **Claude-kosten**: elke vraag kost een paar cent. De limieten in de app
  (5 vragen per minuut en 50 per dag per bezoeker, 300 per dag in totaal)
  begrenzen dat. Ook nuttig: stel bij Anthropic een **maandlimiet** in
  (console.anthropic.com → Settings → Limits).
- **Voyage-limiet**: zonder betaalmethode mag Voyage maar 3 aanvragen per
  minuut. Bij een publieke chatbot loop je daar snel tegenaan. Voeg een
  betaalmethode toe op dashboard.voyageai.com. Je eerste 200 miljoen tokens blijven
  gratis, alleen de limiet gaat omhoog.
- Optioneel maar aan te raden voor publiek gebruik: zet `ANSWER_MODEL=claude-sonnet-5`
  in het `.env` op de server. Dat is ongeveer 2,5 keer goedkoper per antwoord.

---

## Stap 0: de code op GitHub zetten (eenmalig)

De server haalt je code van GitHub. Je project staat daar nog niet.

1. Ga naar https://github.com/new, kies de naam `portfolio-rag-chatbot`,
   zet hem op **Public**, vink niets aan (geen README) en klik *Create repository*.
   (Public is prima: je `.env` met keys wordt nooit meegestuurd, dat regelt `.gitignore`.)
2. Typ in PowerShell in de projectmap:

```bash
git init
git add .
git commit -m "Portfolio RAG chatbot"
git branch -M main
git remote add origin https://github.com/milan-kemp/portfolio-rag-chatbot.git
git push -u origin main
```

3. Controleer op GitHub dat er **geen** `.env`-bestand tussen staat. Staat het
   er toch, stop dan en meld het, dan roteren we je keys.

---

## Stap 1: AWS-account en budgetalarm

1. Ga naar https://aws.amazon.com en maak een account (of log in).
2. Ga naar **Billing → Budgets → Create budget**, kies *Zero spend budget* of
   een maandbudget van €5, en vul je e-mailadres in.

## Stap 2: server (EC2) aanmaken

1. Zet rechtsboven de regio op **Europe (Frankfurt) eu-central-1**.
2. Zoek **EC2** → **Launch instance** en vul in:
   - **Name**: `milan-bot`
   - **Image**: *Ubuntu Server 24.04 LTS*
   - **Instance type**: `t3.micro`
   - **Key pair**: *Create new key pair*, naam `milan-bot-key`, type RSA, formaat `.pem`.
     Er wordt een bestand gedownload. **Bewaar dat goed**, het is je sleutel om in te loggen.
   - **Network settings → Edit**, en zorg dat er drie regels staan:
     - SSH (poort 22), bron **My IP** (alleen jouw internetadres)
     - HTTP (poort 80), bron Anywhere
     - HTTPS (poort 443), bron Anywhere
   - **Storage**: zet op **20 GiB** (gp3)
3. Klik **Launch instance**.

## Stap 3: vast IP-adres (Elastic IP)

Zonder dit verandert het IP-adres bij elke herstart.

1. In EC2, links: **Elastic IPs → Allocate Elastic IP address → Allocate**.
2. Selecteer het nieuwe IP → **Actions → Associate Elastic IP address** → kies je
   instance `milan-bot` → **Associate**.
3. Noteer het IP-adres (bijvoorbeeld `3.70.12.5`).

## Stap 4: DuckDNS naar het IP laten wijzen

1. Ga naar https://www.duckdns.org en log in.
2. Vul bij `milan-bot` het IP-adres uit stap 3 in en klik **update ip**.
3. Controleer in PowerShell (na een minuutje):

```bash
nslookup milan-bot.duckdns.org
```

Je moet je IP-adres terugzien.

## Stap 5: inloggen op de server

1. Zet het gedownloade `milan-bot-key.pem` in je map Downloads.
2. Windows wil de sleutel afschermen. Typ in PowerShell (pas het pad aan als nodig):

```bash
icacls "$env:USERPROFILE\Downloads\milan-bot-key.pem" /inheritance:r /grant:r "$($env:USERNAME):(R)"
```

3. Verbind (vervang `JOUW-IP` door het IP uit stap 3):

```bash
ssh -i "$env:USERPROFILE\Downloads\milan-bot-key.pem" ubuntu@JOUW-IP
```

Typ `yes` als het vraagt of je door wilt gaan. Je ziet nu `ubuntu@ip-...:~$`.
Alles hieronder typ je **in dit venster**.

> Werkt het later niet meer (timeout)? Dan is je thuis-IP veranderd. Pas in AWS
> de SSH-regel van je security group aan naar *My IP*.

## Stap 6: server voorbereiden (op de server)

Docker installeren:

```bash
curl -fsSL https://get.docker.com | sudo sh
```

Jezelf toestemming geven om Docker te gebruiken:

```bash
sudo usermod -aG docker ubuntu
```

Een reserve-geheugenbestand (swap) aanmaken, omdat de server maar 1 GB geheugen heeft:

```bash
sudo fallocate -l 1G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile && echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

Log uit en weer in, zodat de Docker-toestemming actief wordt:

```bash
exit
```

Verbind daarna opnieuw met dezelfde `ssh`-opdracht als in stap 5.

## Stap 7: de chatbot installeren (op de server)

Code ophalen:

```bash
git clone https://github.com/milan-kemp/portfolio-rag-chatbot.git
```

```bash
cd portfolio-rag-chatbot
```

Je instellingen en keys aanmaken. Dit bestand staat alleen op de server, nooit in git:

```bash
cp .env.example .env
```

```bash
nano .env
```

Vul in (verwijder het `#` aan het begin van de regels die je gebruikt):

```
ANTHROPIC_API_KEY=jouw-anthropic-key
VOYAGE_API_KEY=jouw-voyage-key
DOMAIN=milan-bot.duckdns.org
ALLOWED_ORIGINS=https://milan-kemp.github.io
```

Opslaan in nano: `Ctrl+O`, `Enter`, dan afsluiten met `Ctrl+X`.

Je kennisbank vullen (eenmalig, duurt een paar minuten door het bouwen):

```bash
docker compose run --rm api python ingest.py
```

De chatbot starten:

```bash
docker compose up -d
```

## Stap 8: controleren

Open in je browser **https://milan-bot.duckdns.org/health**. Je moet
`{"status":"ok","chunks":16}` zien, en het slotje in de adresbalk moet dicht zijn.
Het certificaat kan de eerste keer een halve minuut duren. Bij problemen:

```bash
docker compose logs caddy
```

Test daarna https://milan-bot.duckdns.org/docs zoals je lokaal deed.

## Stap 9: de widget op je portfolio-site zetten

Zie de sectie *Putting the widget on the portfolio site* in de README. Kort:
kopieer `widget/portfolio-chatbot.js` naar je portfolio-repo en voeg vóór
`</body>` in je `index.html` toe:

```html
<script src="portfolio-chatbot.js" data-api="https://milan-bot.duckdns.org"></script>
```

---

## Later: content of code bijwerken

Op je pc: wijzig bestanden, dan in PowerShell:

```bash
git add .
git commit -m "Update"
git push
```

Op de server:

```bash
bash ~/portfolio-rag-chatbot/deploy/update.sh
```

Dat haalt de wijzigingen op, verwerkt alleen nieuwe of gewijzigde tekst
opnieuw (goedkoop) en herstart de chatbot. De vectorstore blijft bewaard.

## Handige opdrachten (op de server, in de projectmap)

| Wat | Opdracht |
|---|---|
| Status bekijken | `docker compose ps` |
| Logs bekijken | `docker compose logs -f api` |
| Geheugengebruik | `docker stats --no-stream` |
| Herstarten | `docker compose restart` |
| Stoppen | `docker compose down` |
