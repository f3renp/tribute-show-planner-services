# Tribute Show Planner

A playlist checker for live concerts. A tribute act keeps a catalogue of
songs and outfits, puts songs in order for a show, and the app reports what
is wrong with that order: running time over the limit, outfit changes
without a long enough break, poor energy pacing, and retired or repeated
songs.

It runs as two services, each a Flask app served by waitress with its own
SQLite database (ADR-6 in `ADR.md`):

- **Catalogue** (`services/catalogue/`): songs and outfits, at
  http://localhost:8001/catalogue/. Owns the `outfits` and `songs` tables.
- **Shows** (`services/shows/`): shows, ordered setlists and the setlist
  checks (`shows/rules.py`), at http://localhost:8002/shows/. Owns the
  `shows` and `setlist_items` tables.

The shows service gets song details only from the catalogue's JSON API,
over HTTP:

| Endpoint | Returns |
|----------|---------|
| `GET /api/songs?ids=3,7` | The songs with these ids (unknown ids are left out) |
| `GET /api/songs/active` | The songs that can be added to a setlist |
| `GET /health` (both services) | `{"status": "ok"}` |

## Run locally

You need Docker with Docker Compose. From the repository root:

```
docker compose up --build
```

Then open http://localhost:8001 (catalogue) or http://localhost:8002
(shows). Stop with Ctrl+C. `docker compose down` removes the containers;
the data stays in the `catalogue-data` and `shows-data` volumes until you
run `docker compose down -v`.

There is no other setup step and no `.env` file is needed. At startup each
service creates its tables if they are missing. If the catalogue is empty,
it also adds a demo catalogue (`seed.py`): 7 outfits and 20 songs, with one
song already retired. A catalogue that already has data is never changed.

### Without Docker (for development)

Each service runs on its own with Python 3.10 or newer (developed with
3.14). In two terminals, with a virtual environment active:

```
cd services/catalogue
pip install -r requirements.txt
$env:PORT = "8001"; python app/main.py      # macOS/Linux: PORT=8001 python app/main.py
```

```
cd services/shows
pip install -r requirements.txt
$env:PORT = "8002"; python app/main.py      # macOS/Linux: PORT=8002 python app/main.py
```

## Configuration

Everything is set through environment variables with defaults.
`docker-compose.yml` sets the ones the containers need; `.env.example`
lists the ones you may want to change.

| Variable | Service | Default | What it does |
|----------|---------|---------|--------------|
| `PORT` | both | `8000` | Port the server listens on. It always binds to `0.0.0.0`. |
| `DATA_DIR` | both | `data` (`/data` in the image) | Folder for the SQLite file: `catalogue.db` or `shows.db`. |
| `CATALOGUE_URL` | shows | `http://localhost:8001` | Where shows calls the catalogue API. Compose sets `http://catalogue:8000`. |
| `CATALOGUE_TIMEOUT` | shows | `5` | Seconds to wait for the catalogue. |
| `CATALOGUE_PUBLIC_URL` | shows | `http://localhost:8001` | Catalogue address for links in the browser. |
| `SHOWS_PUBLIC_URL` | catalogue | `http://localhost:8002` | Shows address for links in the browser. |

A relative `DATA_DIR` is relative to the folder the service is started
from.

## Tests and coverage

Each service has its own tests in its `tests/` folder. The database tests
each run on a new temporary SQLite file. The shows tests never call the
real catalogue: they use a fake one (the `catalogue` fixture in
`services/shows/tests/conftest.py`).

The test tools are in each service's `requirements-dev.txt`, which also
installs `requirements.txt`. The images only install `requirements.txt`.

```
cd services/catalogue
pip install -r requirements-dev.txt
python -m pytest --cov=app --cov-report=term-missing
cd ../shows
pip install -r requirements-dev.txt
python -m pytest --cov=app --cov-report=term-missing
```

Result on 2026-11-10:

| Service | Tests | Coverage |
|---------|-------|----------|
| catalogue | 81 passed | 87% |
| shows | 74 passed | 88% |

The routes are still mostly untested on purpose: they hold no rules and
only call the services. See ADR-4 in `ADR.md`.

## Assignment 1 container contract check (§7)

This is the evidence for the single-container version of the app from
Assignment 1, before the split. Output of the provided `run.sh`, run on
2026-10-12:

```
=== SDD Assignment 1 contract check ===
Repository: /c/Users/Fernando/SoftwareandDevops/tribute-show-planner

==> Repository shape
  PASS  one Dockerfile, one manifest (requirements.txt)

==> Build from a clean context, no build args
  PASS  image built
  PASS  image size 220 MB

==> Start on PORT=8000 and reach it from the host
  PASS  HTTP 302 from http://localhost:8000/

==> SQLite file under DATA_DIR
  PASS  found in /data: tribute.db

==> Data persists, and a second boot does not re-seed
  PASS  volume at /data persists
  PASS  row counts unchanged across restart: outfits=7 setlist_items=0 shows=0 songs=20

==> PORT override is honoured (not hardcoded)
  PASS  HTTP 302 from http://localhost:9123/

=== ALL CHECKS PASSED ===
Paste this output into your README as the §7 evidence.
```

Notes:

- In the original output the row-counts line was garbled by Windows line
  endings. The line above shows the real counts: `outfits=7
  setlist_items=0 shows=0 songs=20`.
- I ran it in Git Bash on Windows. The script calls `mktemp -t sdd-check`,
  and GNU `mktemp` (the one in Git Bash) needs X's in the template to
  replace with random characters. So I defined a `mktemp` shell function
  that adds `XXXXXX` to the template, then ran the script unchanged.

## Project files

- `docker-compose.yml`: starts both services, one volume each.
- `.env.example`: the optional settings for compose.
- `services/<name>/Dockerfile`, `.dockerignore`, `requirements.txt`: how
  each image is built. Only `app/` is copied into the image.
- `services/<name>/requirements-dev.txt`: pytest and pytest-cov, for the
  tests only.
- `services/<name>/app/main.py`: builds the Flask app and starts waitress.
- `services/<name>/app/config.py`: reads that service's settings.
- `services/<name>/app/db.py` and `schema.sql`: SQLite connections and the
  tables that service owns.
- `services/catalogue/app/seed.py`: the demo catalogue.
- `services/catalogue/app/catalogue/`: `routes.py` (pages), `api.py` (JSON
  for the shows service), `service.py` (rules and validation),
  `repository.py` (SQL).
- `services/shows/app/shows/`: `routes.py`, `service.py`, `repository.py`,
  `rules.py` (the six setlist checks) and `catalogue_client.py` (the HTTP
  calls to the catalogue).
- `services/<name>/app/templates/`, `static/`: HTML templates, CSS and a
  little JavaScript.
- `docs/diagrams.md`: architecture and database diagrams (still show the
  single-app version).
- `ADR.md`: architecture decisions. `AI_USAGE.md`: AI usage log.
