"""Catalogue web pages. Each route reads the request, calls the service or
repository, and renders a template. No rules live here."""
from flask import Blueprint, abort, redirect, render_template, request, url_for

from catalogue import repository, service

bp = Blueprint("catalogue", __name__, url_prefix="/catalogue")


@bp.route("/")
def song_list():
    return render_template(
        "catalogue/songs.html",
        songs=repository.list_songs(),
        format_duration=service.format_duration,
    )


def render_song_form(heading, form, errors):
    """Show the song form, used for both adding and editing."""
    return render_template(
        "catalogue/song_form.html",
        heading=heading,
        form=form,
        errors=errors,
        outfits=repository.list_outfits(),
    )


@bp.route("/songs/new", methods=["GET", "POST"])
def new_song():
    form = {}
    errors = []
    if request.method == "POST":
        form = request.form
        errors = service.add_song(form)
        if not errors:
            return redirect(url_for("catalogue.song_list"))
    return render_song_form("Add a song", form, errors)


@bp.route("/songs/<int:song_id>/edit", methods=["GET", "POST"])
def edit_song(song_id):
    song = repository.get_song(song_id)
    if song is None:
        abort(404)
    form = service.song_to_form(song)
    errors = []
    if request.method == "POST":
        form = request.form
        errors = service.edit_song(song_id, form)
        if not errors:
            return redirect(url_for("catalogue.song_list"))
    return render_song_form(f"Edit {song['title']}", form, errors)


@bp.route("/songs/<int:song_id>/retire", methods=["POST"])
def retire(song_id):
    service.retire_song(song_id)
    return redirect(url_for("catalogue.song_list"))


@bp.route("/songs/<int:song_id>/reactivate", methods=["POST"])
def reactivate(song_id):
    service.reactivate_song(song_id)
    return redirect(url_for("catalogue.song_list"))


@bp.route("/outfits", methods=["GET", "POST"])
def outfit_list():
    form = {}
    errors = []
    if request.method == "POST":
        form = request.form
        errors = service.add_outfit(form)
        if not errors:
            return redirect(url_for("catalogue.outfit_list"))
    return render_template(
        "catalogue/outfits.html",
        outfits=repository.list_outfits(),
        form=form,
        errors=errors,
    )
