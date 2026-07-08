from flask import Flask

from config import Config
from web.routes.dashboard_routes import dashboard_bp
from web.routes.auth_routes import auth_bp
from web.routes.client_routes import client_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    @app.after_request
    def add_no_cache_headers(response):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(client_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )