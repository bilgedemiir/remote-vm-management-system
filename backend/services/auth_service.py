from database.repositories.user_repository import find_user_by_username


def authenticate_user(username, password):
    user = find_user_by_username(username)

    if not user:
        return None

    if user["password_hash"] != password:
        return None

    return user