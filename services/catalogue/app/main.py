"""Entry point of the catalogue service: builds the Flask app and serves it
with waitress.

Start it from services/catalogue with: python app/main.py
"""
from flask import Flask, redirect, url_for
from waitress import serve

import config
import db
import seed
from catalogue.api import bp as api_bp
from catalogue.routes import bp as catalogue_bp


def create_app():
    """Create missing tables, add the demo catalogue if it is empty, then
    build and return the Flask app."""
    db.init_db()
    seed.seed_demo_catalogue()
    app = Flask(__name__)
    app.register_blueprint(catalogue_bp)
    app.register_blueprint(api_bp)

    @app.context_processor
    def links_to_other_services():
        return {"shows_public_url": config.SHOWS_PUBLIC_URL}

    @app.route("/")
    def home():
        return redirect(url_for("catalogue.song_list"))

    @app.route("/health")
    def health():
        return {"status": "ok"}

    return app


if __name__ == "__main__":
    # 0.0.0.0 accepts connections from outside the machine or container,
    # not only from localhost.
    serve(create_app(), host="0.0.0.0", port=config.PORT)
