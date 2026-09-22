import requests

from flask import current_app


def verify_turnstile(
    token,
    remote_ip=None
):
    token = str(token or "").strip()

    if not token:
        return False

    verification_data = {
        "secret": current_app.config[
            "TURNSTILE_SECRET_KEY"
        ],
        "response": token
    }

    if remote_ip:
        verification_data["remoteip"] = (
            remote_ip
        )

    try:
        response = requests.post(
            current_app.config[
                "TURNSTILE_VERIFY_URL"
            ],
            data=verification_data,
            timeout=10
        )

        response.raise_for_status()

        result = response.json()

        return result.get(
            "success",
            False
        ) is True

    except (
        requests.RequestException,
        ValueError
    ):
        return False