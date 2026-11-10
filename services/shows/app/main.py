"""Entry point of the shows service: builds the Flask app and serves it
with waitress.

Start it from services/shows with: python app/main.py
"""
from flask import Flask, redirect, url_for
from waitress import serve

import config
import db
from shows.routes import bp as shows_bp


def create_app():
    """Create missing tables, then build and return the Flask app."""
    db.init_db()
    app = Flask(__name__)
    app.register_blueprint(shows_bp)

    @app.context_processor
    def links_to_other_services():
        return {"catalogue_public_url": config.CATALOGUE_PUBLIC_URL}

    @app.route("/")
    def home():
        return redirect(url_for("shows.show_list"))

    @app.route("/health")
    def health():
        return {"status": "ok"}

    return app


if __name__ == "__main__":
    # 0.0.0.0 accepts connections from outside the machine or container,
    # not only from localhost.
    serve(create_app(), host="0.0.0.0", port=config.PORT)
