"""Settings for the shows service, read from environment variables with
defaults.

Nothing else in the service reads os.environ, so this file lists every
setting that can be changed without editing code.
"""
import os

# Port the web server listens on.
PORT = int(os.environ.get("PORT", "8000"))

# Folder that holds the SQLite database file.
DATA_DIR = os.environ.get("DATA_DIR", "data")

# Full path of the database file inside DATA_DIR.
DATABASE_PATH = os.path.join(DATA_DIR, "shows.db")

# Where this service calls the catalogue's JSON API. In docker compose it is
# http://catalogue:8000 (the service name on the compose network).
CATALOGUE_URL = os.environ.get("CATALOGUE_URL", "http://localhost:8001")

# Seconds to wait for the catalogue before giving up on a request.
CATALOGUE_TIMEOUT = float(os.environ.get("CATALOGUE_TIMEOUT", "5"))

# Address of the catalogue as the browser sees it, for the "Songs" and
# "Outfits" links. Not the same as CATALOGUE_URL inside docker compose.
CATALOGUE_PUBLIC_URL = os.environ.get("CATALOGUE_PUBLIC_URL", "http://localhost:8001")
