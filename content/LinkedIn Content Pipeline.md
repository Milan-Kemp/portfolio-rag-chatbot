# LinkedIn Content Pipeline

Een AI-gedreven B2B content pipeline, gebouwd tijdens mijn stage bij ReFurnity, die
LinkedIn-posts en blogartikelen genereert vanuit RSS-feeds en performance-data,
via N8N en Claude. Contentproductie voor LinkedIn bleef bij ReFurnity vaak liggen:
goede ideeën, geen tijd om ze uit te werken. Met een Lovable-dashboard beheert het
team de pipeline zelfstandig. Er wordt nooit automatisch gepubliceerd.

## Hoe het werkt

De pipeline bestaat uit zes stappen:

1. Monitoring: een N8N-workflow houdt relevante RSS-feeds continu in de gaten en
   verzamelt nieuwe artikelen als bronmateriaal voor content.
2. Performance: bereik- en engagementcijfers van eerder gepubliceerde posts worden
   bijgehouden in Google Sheets en dienen als input: wat werkte al goed bij deze
   doelgroep?
3. AI-generatie: Claude API combineert de RSS-input met performance-inzichten en
   schrijft LinkedIn-posts en blogartikelen in de tone-of-voice van ReFurnity.
4. Review: het team bekijkt elk gegenereerd concept in het Lovable-dashboard,
   bewerkt waar nodig en keurt goed. Niets gaat door zonder menselijke controle.
5. Opmaak: goedgekeurde blogartikelen worden weggeschreven naar Google Docs, waar
   verdere redactie en opmaak plaatsvindt voor publicatie.
6. Publicatie: na finale controle plaatst het team de content zelf op LinkedIn.

## Het probleem: onderwerpherhaling

De grootste uitdaging was onderwerpsturing. De flow kon zelf leren welke
onderwerpen goed scoorden op interacties, maar dat leidde tot een
zelfversterkend effect: als een AI-gerelateerd onderwerp goed scoorde,
koos de flow steeds vaker datzelfde soort onderwerp, waardoor de content
op den duur eenzijdig werd en zich ging herhalen.

## De oplossing

Ik loste dit op door brede onderwerpcategorieën vooraf te definiëren en bij
te houden hoe vaak elke categorie al gebruikt was (een simpele telling per
onderwerp). Daarmee bleef de flow vrij om zelf een onderwerp binnen die
categorieën te kiezen, maar hield het systeem rekening met spreiding: een
onderwerp dat al vaak was langsgekomen, werd minder waarschijnlijk opnieuw
gekozen. Daarnaast bleef het mogelijk om zelf handmatig met een specifiek
onderwerp te komen, buiten de automatische selectie om.

## Belangrijkste les: automatiseer het denkwerk, niet de publish-knop

De pipeline versnelt research, structuur en een eerste concept: het werk dat de
meeste tijd kost. Publicatie blijft bewust een handmatige stap: merkstem, toon en
timing op LinkedIn zijn te gevoelig om zonder review de deur uit te laten gaan. Het
Lovable-dashboard is daarom niet alleen een preview, maar de plek waar het team elk
concept goedkeurt, bijschaaft of afwijst voordat het verder gaat.

## Output

- LinkedIn-post: kant-en-klaar conceptbericht in de tone-of-voice van ReFurnity,
  klaar voor review in het dashboard.
- Blogartikel: langere vorm content vanuit dezelfde RSS-bron, weggeschreven naar
  Google Docs voor redactie.
- Performance-loop: resultaten van gepubliceerde content vloeien terug in Google
  Sheets en verbeteren de volgende generatie-ronde.

## Resultaat

Een contentpipeline die zelfstandig kan kiezen en leren van performance,
zonder dat die keuzevrijheid omslaat in eenzijdige, herhaalde content. Het
systeem draait nog steeds en wordt dagelijks gebruikt bij ReFurnity.

## Tech stack

N8N (workflow-orchestratie), RSS-feeds (bronmateriaal), Claude API
(contentgeneratie), Google Sheets (performance-data), Lovable (dashboard voor
review), Google Docs (redactie van blogartikelen), Templated.io, tellingslogica
voor onderwerpspreiding, LinkedIn als publicatiekanaal.
