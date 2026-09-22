import threading
import time

from flask import (
    Flask,
    request
)

from backend.config import Config

from backend.extensions import (
    csrf
)

from backend.web.routes.auth_routes import (
    auth_bp
)

from backend.web.routes.dashboard_routes import (
    dashboard_bp
)

from backend.web.routes.client_routes import (
    client_bp
)

from backend.web.routes.log_routes import (
    log_bp
)

from backend.web.routes.script_execution_routes import (
    script_execution_bp
)

from backend.web.routes.download_routes import (
    download_bp
)

from backend.web.routes.group_routes import (
    group_bp
)

from backend.database.repositories.client_repository import (
    mark_stale_clients_offline
)

CLIENT_STATUS_TIMEOUT_SECONDS = 40
CLIENT_STATUS_SYNC_INTERVAL_SECONDS = 5


def create_app():
    app = Flask(
        __name__,
        static_folder="web/static",
        static_url_path="/static"
    )

    app.config.from_object(Config)

    app.config[
        "WTF_CSRF_CHECK_DEFAULT"
    ] = True

    csrf.init_app(
        app
    )

    status_sync_lock = threading.Lock()

    last_status_sync = {
        "time": 0.0
    }

    @app.before_request
    def synchronize_client_statuses():
        if request.endpoint == "static":
            return None

        current_time = time.monotonic()

        elapsed_time = (
            current_time
            - last_status_sync["time"]
        )

        if (
            elapsed_time
            < CLIENT_STATUS_SYNC_INTERVAL_SECONDS
        ):
            return None

        lock_acquired = (
            status_sync_lock.acquire(
                blocking=False
            )
        )

        if not lock_acquired:
            return None

        try:
            current_time = time.monotonic()

            elapsed_time = (
                current_time
                - last_status_sync["time"]
            )

            if (
                elapsed_time
                < CLIENT_STATUS_SYNC_INTERVAL_SECONDS
            ):
                return None

            mark_stale_clients_offline(
                timeout_seconds=(
                    CLIENT_STATUS_TIMEOUT_SECONDS
                )
            )

            last_status_sync["time"] = (
                current_time
            )

        except Exception:
            app.logger.exception(
                "Eski istemci durumları "
                "güncellenemedi."
            )

        finally:
            status_sync_lock.release()

        return None

    @app.after_request
    def add_security_headers(response):
        response.headers[
            "Cache-Control"
        ] = (
            "no-store, no-cache, "
            "must-revalidate, max-age=0"
        )

        response.headers[
            "Pragma"
        ] = "no-cache"

        response.headers[
            "Expires"
        ] = "0"

        response.headers[
            "X-Content-Type-Options"
        ] = "nosniff"

        response.headers[
            "X-Frame-Options"
        ] = "SAMEORIGIN"

        response.headers[
            "Referrer-Policy"
        ] = "strict-origin-when-cross-origin"

        response.headers[
            "Content-Security-Policy"
        ] = (
            "default-src 'self'; "
            "script-src 'self' "
            "https://challenges.cloudflare.com; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self' data:; "
            "connect-src 'self' "
            "https://challenges.cloudflare.com; "
            "frame-src "
            "https://challenges.cloudflare.com; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'self'"
        )

        return response

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(client_bp)
    app.register_blueprint(log_bp)
    app.register_blueprint(script_execution_bp)
    app.register_blueprint(download_bp)
    app.register_blueprint(group_bp)

    return app


if __name__ == "__main__":
    app = create_app()

    app.run(
        debug=False,
        host="0.0.0.0",
        port=5000
    )