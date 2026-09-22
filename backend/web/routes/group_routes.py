from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from backend.services.group_service import (
    list_groups,
    add_group,
    edit_group,
    remove_group,
    get_group,
    list_group_members,
    remove_client_from_group
)

from backend.utils.decorators import (
    admin_required
)


group_bp = Blueprint(
    "groups",
    __name__,
    template_folder="../templates"
)


@group_bp.route("/groups")
@admin_required
def groups():

    groups = list_groups()

    group_members = {
        group["id"]: list_group_members(
            group["id"]
        )
        for group in groups
    }

    return render_template(
        "groups.html",
        groups=groups,
        group_members=group_members
    )


@group_bp.route(
    "/groups/create",
    methods=["POST"]
)
@admin_required
def create_group():

    try:

        add_group(
            name=request.form.get("name", ""),
            description=request.form.get(
                "description",
                ""
            ),
            created_by=session["user_id"]
        )

        flash(
            "Grup oluşturuldu.",
            "success"
        )

    except Exception as error:

        flash(
            str(error),
            "danger"
        )

    return redirect(
        url_for("groups.groups")
    )


@group_bp.route(
    "/groups/<int:group_id>/edit",
    methods=["POST"]
)
@admin_required
def update_group(group_id):

    try:

        edit_group(
            group_id=group_id,
            name=request.form.get("name", ""),
            description=request.form.get(
                "description",
                ""
            )
        )

        flash(
            "Grup güncellendi.",
            "success"
        )

    except Exception as error:

        flash(
            str(error),
            "danger"
        )

    return redirect(
        url_for("groups.groups")
    )


@group_bp.route(
    "/groups/<int:group_id>/delete",
    methods=["POST"]
)
@admin_required
def delete_group(group_id):

    remove_group(group_id)

    flash(
        "Grup silindi.",
        "success"
    )

    return redirect(
        url_for("groups.groups")
    )


@group_bp.route(
    "/groups/<int:group_id>/members/<int:client_id>/remove",
    methods=["POST"]
)
@admin_required
def remove_member(
    group_id,
    client_id
):

    try:

        remove_client_from_group(
            group_id=group_id,
            client_id=client_id
        )

        flash(
            "İstemci gruptan çıkarıldı.",
            "success"
        )

    except ValueError as error:

        flash(
            str(error),
            "warning"
        )

    except Exception:

        flash(
            "İstemci gruptan çıkarılırken bir hata oluştu.",
            "danger"
        )

    return redirect(
        url_for("groups.groups")
    )