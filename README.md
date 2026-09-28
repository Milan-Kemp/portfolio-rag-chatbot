# Portfolio RAG chatbot

A small Retrieval-Augmented Generation system that answers questions about my
projects **using only my own writing** (case studies, READMEs, specs), with a
source citation on every answer. It runs as a chat widget on my portfolio site
so visitors can ask things like *"hoe loste Milan onderwerpherhaling op in de
LinkedIn pipeline?"* and get an answer grounded in my documentation — or a
plain *"dat staat niet in de projectteksten"* when it isn't covered.

---

## What is RAG, and why build it this way

A language model on its own answers from its training data. Ask it about *my*
projects and it will confidently make things up, because it has never seen
them. RAG (Retrieval-Augmented Generation) fixes that by putting a **retrieval
step in front of the model** and forbidding it from answering beyond what that
step returns.

```
                    ┌─────────────┐
   content/*.md ───▶│  ingest.py  │  chunk → embed → store        (offline, once per edit)
                    └─────┬───────┘
                          ▼
                   ChromaDB (local, on disk)
                          ▲
   question ───▶ ┌────────┴────────┐
                 │   retrieve.py   │  embed question → top-k nearest chunks
                 └────────┬────────┘
                          ▼
                 ┌─────────────────┐
                 │    answer.py    │  chunks + question → Claude → grounded answer
                 └────────┬────────┘   (system prompt: answer ONLY from context,
                          ▼             otherwise say you can't)
              answer + source filenames
```

1. **Ingest** — split each document into ~400-token chunks, turn every chunk
   into an embedding (a vector that captures its meaning) with the Voyage AI
   API, and store the vectors + text + source filename in a local ChromaDB.
2. **Retrieve** — embed the visitor's question the same way and pull the 4
   chunks whose vectors sit closest to it.
3. **Generate** — hand those 4 chunks to Claude as context. The system prompt
   makes the grounding rule explicit: answer only from the supplied text, cite
   the source file, and when the text doesn't cover the question, say so
   instead of guessing. **This last rule is the whole point of RAG** — the bot
   never answers past what my source data covers.

The model still writes the prose, but the facts come from retrieved text I
control, and every answer points back to the file it came from.

---

## Project layout

| File | Role |
| --- | --- |
| [`config.py`](config.py) | All paths, model names, chunk sizes, CORS origins — one place to change things. Secrets come from `.env`. |
| [`tokenizer.py`](tokenizer.py) | Token counting for chunk sizing (tiktoken, with a heuristic fallback). |
| [`chunking.py`](chunking.py) | Markdown/text → chunks. Splits on headings, packs paragraphs to a target size, adds overlap. |
| [`ingest.py`](ingest.py) | chunks → Voyage embeddings → ChromaDB. Incremental, with an embedding cache. |
| [`retrieve.py`](retrieve.py) | question → top-k chunks. Importable `retrieve()` + CLI. |
| [`answer.py`](answer.py) | chunks + question → Claude → grounded answer + sources. Importable `answer()` + CLI. |
| [`main.py`](main.py) | Interactive CLI over `answer()` to test the whole thing locally. |
| [`api.py`](api.py) | FastAPI app: `POST /ask`, `GET /health`, CORS locked to your site's origin. |
| [`widget/portfolio-chatbot.js`](widget/portfolio-chatbot.js) | Self-contained vanilla-JS chat widget. One-line embed, no dependencies. |
| [`widget/demo.html`](widget/demo.html) | Loads the widget locally against a dev API. |
| [`Dockerfile`](Dockerfile), [`docker-compose.yml`](docker-compose.yml), [`Caddyfile`](Caddyfile) | Container setup: API + Caddy (HTTPS) with a persistent volume for `storage/`. |
| [`DEPLOY.md`](DEPLOY.md), [`deploy/update.sh`](deploy/update.sh) | Step-by-step AWS deployment and a one-command update script. |
| `content/` | The knowledge base: your `.md` / `.txt` files. |
| `storage/` | Local vector store + embedding cache (gitignored). |

---

## Setup

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1      # Windows PowerShell
                                # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

copy .env.example .env          # then fill in ANTHROPIC_API_KEY and VOYAGE_API_KEY
```

Get the keys from [console.anthropic.com](https://console.anthropic.com/) and
[dashboard.voyageai.com](https://dashboard.voyageai.com/). On Voyage's free
tier without a payment method you're capped at **3 requests/minute** — fine for
testing, but add a card (still free up to 200M tokens) if you hit
`RateLimitError` a lot.

---

## Running it

### 1. Add content

Put `.md` or `.txt` files in `content/`, one per project. Use real Markdown
headings (`#`, `##`) — chunking splits on them and the heading path becomes the
citation shown to the reader. Files whose name starts with `_` are ignored.

### 2. Build the vector store

```bash
python ingest.py
```

Re-run this **every time you add or edit a file in `content/`**. It hashes each
chunk's text and caches the embedding, so a normal re-run only pays the Voyage
API for chunks that actually changed. To force a full rebuild (clears the cache
and the store):

```bash
python ingest.py --reset
```

### 3. Test retrieval only (no Claude call, no Anthropic cost)

```bash
python retrieve.py "hoe loste Milan de te-weinig-resultaten van de job alert bot op"
```

### 4. Test the full pipeline from the CLI

```bash
python main.py                       # interactive loop
python main.py "een losse vraag"     # single shot
```

### 5. Run the API

```bash
uvicorn api:app --reload             # http://127.0.0.1:8000  (docs at /docs)
```

```bash
curl -X POST http://127.0.0.1:8000/ask ^
  -H "Content-Type: application/json" ^
  -d "{\"question\": \"welke tech stack gebruikte de LinkedIn pipeline?\"}"
```

### 6. Try the widget

Serve the repo and open the demo page against the running API:

```bash
python -m http.server 8000
```

Open `http://127.0.0.1:8000/widget/demo.html`, click the chat icon bottom-right.

---

## Deployment (Docker + Caddy on AWS EC2)

The API runs as two containers defined in [`docker-compose.yml`](docker-compose.yml):

- **`api`** — the FastAPI app ([`Dockerfile`](Dockerfile), Python 3.13-slim, one
  Uvicorn worker). Secrets are read from a `.env` file on the server at runtime
  and are never baked into the image (`.dockerignore` excludes `.env`).
- **`caddy`** — reverse proxy that terminates HTTPS with an automatic
  Let's Encrypt certificate ([`Caddyfile`](Caddyfile)) and forwards to `api`.

The vector store lives in a Docker named volume (`rag_storage`), so it survives
restarts and redeploys: no re-ingest after every deploy, and `ingest.py` stays
incremental thanks to the embedding cache. Because `/ask` is public and every
call costs money, it is rate limited with slowapi (per IP per minute and per day,
plus a global daily cap; see `RATE_LIMIT_*` in `.env.example`).

Test the whole stack locally:

```bash
docker compose up --build        # then open https://localhost/docs (accept the local-cert warning)
```

Step-by-step AWS setup (EC2, security group, Elastic IP, DuckDNS domain, first
deploy, updates): see [`DEPLOY.md`](DEPLOY.md).

## Putting the widget on the portfolio site

1. **The API is public** at `https://milan-bot.duckdns.org` (see above).
2. **`ALLOWED_ORIGINS`** on the server must include your site's origin:
   `ALLOWED_ORIGINS=https://milan-kemp.github.io` (only the origin matters, not
   the `/Milan-portfolio` path). Without it the browser blocks the widget's
   request (CORS).
3. **Copy** `widget/portfolio-chatbot.js` into your portfolio repo and add one
   line before `</body>` in your `index.html`:

   ```html
   <script src="portfolio-chatbot.js"
           data-api="https://milan-bot.duckdns.org"></script>
   ```

   The widget shows a loading indicator while retrieval + generation run (a few
   seconds), and a friendly message if a visitor hits the rate limit. Use `https`
   for the API: browsers block an `https` page (GitHub Pages) from calling a
   plain `http` API.

---

## Design choices (and why)

| Choice | Why |
| --- | --- |
| **Voyage AI** embeddings | Strong retrieval quality; keeps the embedding model independent from the answer model. `input_type` distinguishes `document` (ingest) from `query` (retrieve), which measurably helps accuracy. |
| **ChromaDB, local & persistent** | The corpus is a portfolio's worth of text. A local on-disk store needs no server and no cloud bill. Cosine distance. |
| **Heading-aware chunking** | Splitting on headings keeps each chunk inside one topic, so its embedding isn't a blur of two subjects. The heading path doubles as the citation. |
| **~400-token chunks, ~80 overlap** | Big enough to hold a full point, small enough to stay specific. Overlap keeps a sentence that straddles a boundary whole in at least one chunk. Tunable in `.env`. |
| **Embedding cache keyed by chunk hash** | Embeddings cost money per call; iterating on content shouldn't. Only `--reset` or a model change forces a full re-embed. |
| **top-k = 4** | Enough context for a focused answer without burying the model or blowing the token budget. Tunable in `.env`. |
| **Grounding enforced in the system prompt** | `answer.py` instructs Claude to use only the `<context>` block and to say plainly when the answer isn't there. No general knowledge, no gap-filling. |
| **`claude-opus-5`, `effort` left at default, `max_tokens` 1024** | Answers are short and grounded. For a high-traffic public widget, set `ANSWER_MODEL=claude-sonnet-5` in `.env` — ~2.5x cheaper output, negligible quality loss for this task. |
| **CORS allowlist, not `*`** | Only the portfolio origin (and localhost) may call the API from a browser. |
| **Rate limit + global daily cap** | The endpoint is public and each call spends Claude and Voyage credits. Per-IP limits stop spamming; the global cap puts a hard ceiling on total spend even if someone rotates IPs. |
| **Docker + Caddy on one small EC2 box** | A portfolio demo doesn't need a load balancer or autoscaling. Compose keeps the setup reproducible; Caddy gives HTTPS with zero certificate config. |

---

## Known failure modes

- **Weak chunking → irrelevant or partial retrieval.** The defaults are a
  reasonable starting point. If test answers are off, `CHUNK_TARGET_TOKENS` /
  `CHUNK_OVERLAP_TOKENS` in `.env` are the first knobs — then re-run
  `ingest.py --reset`.
- **Thin content → the bot falls short on simple questions.** That's a content
  problem, not a code problem. The fix is more `.md` files, not more retrieval
  tuning. With only a handful of projects written up, expect gaps.
- **Voyage free-tier rate limit (3 rpm).** Not a bug — space out calls or add a
  payment method (still free up to 200M tokens).
- **`ingest.py --reset` re-embeds everything** and costs money. The plain run
  doesn't; use it unless you changed `EMBED_MODEL`.
