"""Show builder web pages. Each route reads the request, calls the service,
repository or rules, and renders a template. No rules live here."""
from flask import Blueprint, abort, redirect, render_template, request, url_for

from shows import repository, rules, service

bp = Blueprint("shows", __name__, url_prefix="/shows")


@bp.route("/", methods=["GET", "POST"])
def show_list():
    form = {}
    errors = []
    if request.method == "POST":
        form = request.form
        show_id, errors = service.create_show(form)
        if not errors:
            return redirect(url_for("shows.show_detail", show_id=show_id))
    return render_template(
        "shows/shows.html",
        shows=repository.list_shows(),
        form=form,
        errors=errors,
    )


def get_show_or_404(show_id):
    """The show with this id, or stop with a 404 page."""
    show = repository.get_show(show_id)
    if show is None:
        abort(404)
    return show


def render_show_page(show, errors=(), break_form=None):
    """Show one show with its setlist, the check results, and the forms to
    add to it."""
    items = service.get_setlist(show["id"])
    total_seconds = rules.setlist_seconds(items)
    return render_template(
        "shows/show_detail.html",
        show=show,
        items=items,
        total_seconds=total_seconds,
        over_limit=rules.is_over_limit(total_seconds, show["max_minutes"]),
        problems=rules.check_setlist(items, show["max_minutes"]),
        songs=service.songs_to_choose(),
        format_duration=service.format_duration,
        errors=errors,
        break_form=break_form or {},
    )


@bp.route("/<int:show_id>")
def show_detail(show_id):
    return render_show_page(get_show_or_404(show_id))


@bp.route("/<int:show_id>/songs", methods=["POST"])
def add_song(show_id):
    show = get_show_or_404(show_id)
    # type=int gives None instead of crashing if song_id is not a number.
    song_id = request.form.get("song_id", type=int)
    errors = service.add_song_to_setlist(show_id, song_id)
    if errors:
        return render_show_page(show, errors)
    return redirect(url_for("shows.show_detail", show_id=show_id))


@bp.route("/<int:show_id>/breaks", methods=["POST"])
def add_break(show_id):
    show = get_show_or_404(show_id)
    errors = service.add_break_to_setlist(show_id, request.form)
    if errors:
        return render_show_page(show, errors, request.form)
    return redirect(url_for("shows.show_detail", show_id=show_id))


@bp.route("/<int:show_id>/items/<int:item_id>/move", methods=["POST"])
def move_item(show_id, item_id):
    get_show_or_404(show_id)
    direction = request.form.get("direction", "")
    if direction not in service.DIRECTIONS:
        abort(400)
    service.move_item(show_id, item_id, direction)
    return redirect(url_for("shows.show_detail", show_id=show_id))


@bp.route("/<int:show_id>/items/<int:item_id>/remove", methods=["POST"])
def remove_item(show_id, item_id):
    get_show_or_404(show_id)
    service.remove_item(show_id, item_id)
    return redirect(url_for("shows.show_detail", show_id=show_id))
