from flask import (
    Blueprint,
    current_app,
    render_template,
    request,
    redirect,
    url_for,
    session
)

from backend.services.auth_service import (
    authenticate_user
)

from backend.services.turnstile_service import (
    verify_turnstile
)

from backend.services.log_service import (
    log_info,
    log_warning
)


auth_bp = Blueprint(
    "auth",
    __name__,
    template_folder="../templates"
)


def render_login(
    error=None,
    username=""
):
    return render_template(
        "login.html",
        error=error,
        username=username,
        turnstile_site_key=current_app.config[
            "TURNSTILE_SITE_KEY"
        ]
    )


@auth_bp.route(
    "/login",
    methods=["GET", "POST"]
)
def login():
    if session.get("user_id"):
        if session.get("role_name") == "viewer":
            return redirect(
                url_for("logs.logs")
            )

        return redirect(
            url_for("dashboard.dashboard")
        )

    if request.method == "POST":
        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if not username or not password:
            return render_login(
                error=(
                    "Kullanıcı adı ve şifre "
                    "zorunludur."
                ),
                username=username
            )

        turnstile_token = request.form.get(
            "cf-turnstile-response",
            ""
        )

        turnstile_valid = verify_turnstile(
            token=turnstile_token,
            remote_ip=request.remote_addr
        )

        if not turnstile_valid:
            log_warning(
                event_type="TURNSTILE_FAILED",
                message=(
                    "Turnstile doğrulaması "
                    "başarısız oldu. "
                    f"Kullanıcı: "
                    f"{username or 'Belirtilmedi'}"
                ),
                ip_address=request.remote_addr
            )

            return render_login(
                error=(
                    "Güvenlik doğrulaması "
                    "başarısız oldu. "
                    "Lütfen tekrar deneyin."
                ),
                username=username
            )

        user = authenticate_user(
            username,
            password
        )

        if user is None:
            log_warning(
                event_type="LOGIN_FAILED",
                message=(
                    "Başarısız giriş denemesi. "
                    f"Kullanıcı: {username}"
                ),
                ip_address=request.remote_addr
            )

            return render_login(
                error=(
                    "Kullanıcı adı veya "
                    "şifre hatalı."
                ),
                username=username
            )

        session.clear()
        session.permanent = True

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role_id"] = user["role_id"]
        session["role_name"] = user["role_name"]

        log_info(
            event_type="LOGIN",
            message=(
                f"{user['username']} "
                "sisteme giriş yaptı."
            ),
            user_id=user["id"],
            ip_address=request.remote_addr
        )

        if user["role_name"] == "viewer":
            return redirect(
                url_for("logs.logs")
            )

        return redirect(
            url_for("dashboard.dashboard")
        )

    return render_login()


@auth_bp.route("/logout")
def logout():
    user_id = session.get("user_id")
    username = session.get("username")

    if user_id is not None:
        log_info(
            event_type="LOGOUT",
            message=(
                f"{username} sistemden "
                "çıkış yaptı."
            ),
            user_id=user_id,
            ip_address=request.remote_addr
        )

    session.clear()

    return redirect(
        url_for("auth.login")
    )