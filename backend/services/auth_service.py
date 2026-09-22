import bcrypt

from backend.database.repositories.user_repository import (
    get_user_by_username,
    update_last_login
)


def authenticate_user(username, password):
    user = get_user_by_username(username)

    if user is None:
        return None

    if not user["is_active"]:
        return None

    if not bcrypt.checkpw(
        password.encode("utf-8"),
        user["password_hash"].encode("utf-8")
    ):
        return None

    update_last_login(user["id"])

    return user