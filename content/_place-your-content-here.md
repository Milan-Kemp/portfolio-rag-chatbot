# This folder holds the knowledge base

Drop your `.md` or `.txt` files here: case studies, project READMEs,
technical specs. Anything you'd want a visitor to be able to ask about.

- One file per project (or per topic) works well.
- Use real Markdown headings (`#`, `##`, `###`). Chunking splits on them, and
  the heading path becomes the source citation shown to the reader.
- Files whose name starts with `_` (like this one) are ignored by `ingest.py`,
  so you can keep notes in here without polluting the index.

After adding or editing files, re-run:

    python ingest.py
