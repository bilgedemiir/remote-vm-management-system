from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from backend.services.script_service import (
    list_scripts,
    get_script,
    list_versions,
    create_new_script,
    create_new_version,
    change_script_status
)

from backend.utils.decorators import (
    login_required,
    operator_required
)


script_bp = Blueprint(
    "script",
    __name__,
    template_folder="../templates"
)


@script_bp.route("/scripts")
@login_required
def scripts():
    script_list = list_scripts()

    return render_template(
        "scripts.html",
        scripts=script_list
    )


@script_bp.route(
    "/scripts/create",
    methods=["GET", "POST"]
)
@operator_required
def create_script():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "").strip()
        script_content = request.form.get(
            "script_content",
            ""
        ).strip()

        if not name:
            flash("Script adı boş bırakılamaz.", "danger")
            return render_template(
                "script_create.html",
                form_data=request.form
            )

        if not script_content:
            flash("Script içeriği boş bırakılamaz.", "danger")
            return render_template(
                "script_create.html",
                form_data=request.form
            )

        try:
            create_new_script(
                name=name,
                description=description,
                category=category,
                script_content=script_content,
                created_by=session["user_id"]
            )

            flash("Script başarıyla oluşturuldu.", "success")

            return redirect(
                url_for("script.scripts")
            )

        except ValueError as error:
            flash(str(error), "danger")

        except Exception:
            flash(
                "Script oluşturulurken bir hata oluştu.",
                "danger"
            )

    return render_template(
        "script_create.html",
        form_data={}
    )


@script_bp.route("/scripts/<int:script_id>")
@login_required
def script_detail(script_id):
    script_data = get_script(script_id)

    if script_data is None:
        return "Script bulunamadı.", 404

    versions = list_versions(script_id)

    return render_template(
        "script_detail.html",
        script=script_data,
        versions=versions
    )


@script_bp.route(
    "/scripts/<int:script_id>/version",
    methods=["POST"]
)
@operator_required
def new_version(script_id):
    script_data = get_script(script_id)

    if script_data is None:
        return "Script bulunamadı.", 404

    script_content = request.form.get(
        "script_content",
        ""
    ).strip()

    change_log = request.form.get(
        "change_log",
        ""
    ).strip()

    if not script_content:
        flash(
            "Yeni versiyonun script içeriği boş bırakılamaz.",
            "danger"
        )

        return redirect(
            url_for(
                "script.script_detail",
                script_id=script_id
            )
        )

    try:
        create_new_version(
            script_id=script_id,
            script_content=script_content,
            created_by=session["user_id"],
            change_log=change_log
        )

        flash(
            "Yeni script versiyonu oluşturuldu.",
            "success"
        )

    except ValueError as error:
        flash(str(error), "danger")

    except Exception:
        flash(
            "Yeni versiyon oluşturulurken hata oluştu.",
            "danger"
        )

    return redirect(
        url_for(
            "script.script_detail",
            script_id=script_id
        )
    )


@script_bp.route(
    "/scripts/<int:script_id>/toggle",
    methods=["POST"]
)
@operator_required
def toggle_script(script_id):
    script_data = get_script(script_id)

    if script_data is None:
        return "Script bulunamadı.", 404

    new_status = not bool(script_data["is_active"])

    try:
        change_script_status(
            script_id=script_id,
            is_active=new_status
        )

        if new_status:
            flash("Script aktif hale getirildi.", "success")
        else:
            flash("Script pasif hale getirildi.", "success")

    except ValueError as error:
        flash(str(error), "danger")

    except Exception:
        flash(
            "Script durumu değiştirilirken hata oluştu.",
            "danger"
        )

    return redirect(
        url_for("script.scripts")
    )