# Offerte Automation Pipeline

Een productie-pipeline voor ReFurnity, een B2B circulair interieurmanagementbedrijf,
die prijsopgaves van leveranciers automatisch verwerkt tot professionele offertes,
orderbevestigingen en facturen. Voorheen ging het uitwerken van een offerte
grotendeels met de hand: gegevens overtypen, prijzen narekenen, opmaak herhalen.
Een Lovable-dashboard, een N8N-workflow, Claude API-extractie en een
Python/FastAPI-microservice op Render werken samen tot één doorlopende flow, van
upload tot einddocument.

## Hoe het werkt

De pipeline bestaat uit zes stappen:

1. Upload: één of meerdere leveranciersdocumenten (PDF, Word, Excel) worden
   geüpload. Foto's die bij het document horen worden genormaliseerd zodat ze
   consistent ogen in de output.
2. Extractie: Claude API leest het brondocument en zet regelitems, prijzen en
   specificaties om naar gestructureerde data. Validators vangen edge cases op,
   zoals lege velden die anders de rest van de pipeline zouden breken.
3. Review: de geëxtraheerde data is direct te controleren en aan te passen in een
   Lovable-dashboard, inclusief korting- en toeslagpercentages per regel of over
   het totaal.
4. Orkestratie: een lokale N8N-workflow verbindt alle stappen en stuurt data door
   naar de generatie-service, beveiligd met een API-key op de webhook.
5. Generatie: een Python/FastAPI-microservice zet de data om in het uiteindelijke
   document, met de huisstijl van ReFurnity.
6. Output: het eindresultaat wordt gegenereerd in het gewenste formaat (Word, PDF
   of Excel) en opgeslagen in een geschiedenis-overzicht, gegroepeerd per klant
   zodat eerdere offertes terug te vinden zijn.

## Mijn rol

Ik bepaalde de architectuur en de API-contracten tussen de onderdelen. Claude Code
bouwde en implementeerde de Python/FastAPI-microservice.

## Drie documenttypes

- Offerte: regelitems, korting en toeslag verwerkt in het eindtotaal,
  ReFurnity-branding, export naar Word, PDF of Excel.
- Orderbevestiging: zelfde datamodel, ander document. Wordt direct gegenereerd
  vanuit een geaccepteerde offerte.
- Factuur: sluit de flow af, met dezelfde velden en validatie als de eerdere twee
  documenten.

## Het probleem: wensen vertalen naar exacte output

De grootste uitdaging zat niet in de techniek van documenten genereren,
maar in het precies vertalen van de wensen van de opdrachtgever naar
concrete output. ReFurnity had specifieke eisen aan hoe een offerte,
orderbevestiging en factuur eruit moesten zien, tot in details als
opmaak, volgorde van informatie, en welke gegevens waar hoorden te staan.
Een output die inhoudelijk klopte maar niet exact aansloot bij hun format
was voor hen niet bruikbaar.

## De oplossing

Ik leerde hierbij vooral hoe ik de wensen van een opdrachtgever nauwkeurig
kan doorgronden en vertalen naar een werkende technische oplossing: niet
alleen vragen wat ze willen, maar doorvragen op het waarom achter een eis,
zodat de output niet slechts een benadering werd maar precies aansloot bij
wat ReFurnity nodig had voor hun eigen administratie en klantcommunicatie.

## Belangrijkste les: bijna elke bug was een field-name mismatch

Data stroomt door drie systemen die onafhankelijk zijn ontwikkeld (Lovable, N8N
en de Python-service), en die moeten het exact eens zijn over veldnamen. Vrijwel
iedere bug tijdens de bouw kwam hieruit voort. Het herhaalbare fix-patroon: eerst
de exacte JSON bekijken in de Input-tab van N8N, en pas daarna verder debuggen.

## Resultaat

Een pipeline die offertes, orderbevestigingen en facturen genereert in
precies het format dat ReFurnity vereist, nog steeds in gebruik.

## Tech stack

Lovable (dashboard met live editing en geschiedenis-pagina), N8N (lokale workflow,
webhook met API-key, ngrok-tunnel), Claude API (extractie van regelitems en
prijzen), Pydantic validators, Python en FastAPI (generatie-service op Render, met
een warmup ping), python-docx (Word-output), PIL (normaliseren van foto's).
