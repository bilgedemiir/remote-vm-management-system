
from flask import Blueprint, render_template, request, redirect, url_for, session

from services.auth_service import authenticate_user

auth_bp = Blueprint(
    "auth",
    __name__,
    template_folder="../templates"
)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        user = authenticate_user(username, password)

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            return redirect(url_for("dashboard.dashboard"))

        return render_template(
            "login.html",
            error="Kullanıcı adı veya şifre hatalı."
        )

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))