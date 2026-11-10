"""JSON endpoints for other services. They replace the two in-process seam
functions the show builder used to import (ADR-3, ADR-6). Both are
read-only and only call catalogue.service."""
from flask import Blueprint, abort, request

from catalogue import service

bp = Blueprint("catalogue_api", __name__, url_prefix="/api")


@bp.route("/songs")
def songs_by_ids():
    """GET /api/songs?ids=3,7,12 -> the songs with these ids, as a list.

    Ids that do not exist are simply missing from the list. No ids gives
    an empty list.
    """
    text = request.args.get("ids", "").strip()
    try:
        song_ids = [int(part) for part in text.split(",")] if text else []
    except ValueError:
        abort(400, "ids must be whole numbers separated by commas.")
    return list(service.get_songs_by_ids(song_ids).values())


@bp.route("/songs/active")
def active_songs():
    """GET /api/songs/active -> the songs that can be added to a setlist."""
    return service.list_active_songs()
