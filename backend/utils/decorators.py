from functools import wraps

from flask import (
    session,
    redirect,
    url_for,
    abort
)


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            return redirect(
                url_for("auth.login")
            )

        return func(*args, **kwargs)

    return wrapper


def role_required(*allowed_roles):
    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):

            if "user_id" not in session:
                return redirect(
                    url_for("auth.login")
                )

            role = session.get("role_name")

            if role not in allowed_roles:
                abort(403)

            return func(*args, **kwargs)

        return wrapper

    return decorator


def admin_required(func):
    return role_required("admin")(func)


def operator_required(func):
    return role_required(
        "admin",
        "operator"
    )(func)


def viewer_required(func):
    return role_required(
        "admin",
        "viewer"
    )(func)