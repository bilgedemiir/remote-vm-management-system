document.addEventListener("DOMContentLoaded", function () {

    const deleteGroupForms = document.querySelectorAll(
        ".delete-group-form"
    );

    deleteGroupForms.forEach(function (form) {

        form.addEventListener(
            "submit",
            function (event) {

                const confirmed = confirm(
                    "Bu grup silinsin mi?"
                );

                if (!confirmed) {
                    event.preventDefault();
                }
            }
        );

    });


    const removeMemberButtons = document.querySelectorAll(
        ".remove-group-member"
    );

    removeMemberButtons.forEach(function (button) {

        button.addEventListener(
            "click",
            function (event) {

                const hostname =
                    button.dataset.hostname || "İstemci";

                const confirmed = confirm(
                    `${hostname} bu gruptan çıkarılsın mı?`
                );

                if (!confirmed) {
                    event.preventDefault();
                }
            }
        );

    });

});