"""Settings for the catalogue service, read from environment variables with
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
DATABASE_PATH = os.path.join(DATA_DIR, "catalogue.db")

# Address of the shows service as the browser sees it, for the "Shows" link
# in the page header. This is a browser link, not a service-to-service call.
SHOWS_PUBLIC_URL = os.environ.get("SHOWS_PUBLIC_URL", "http://localhost:8002")
