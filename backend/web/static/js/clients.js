document.addEventListener("DOMContentLoaded", function () {

    const form = document.getElementById("bulkGroupForm");

    if (!form) {
        return;
    }

    const clientCheckboxes = Array.from(
        document.querySelectorAll(".client-select")
    );

    const groupCheckboxes = Array.from(
        document.querySelectorAll(".bulk-group-checkbox")
    );

    const selectAll = document.getElementById(
        "selectAllClients"
    );

    const selectedCount = document.getElementById(
        "selectedClientCount"
    );

    const assignButton = document.getElementById(
        "bulkAssignButton"
    );

    const groupPanel = document.getElementById(
        "bulkGroupPanel"
    );

    const saveButton = document.getElementById(
        "saveBulkGroupsButton"
    );

    const cancelButton = document.getElementById(
        "cancelBulkGroupsButton"
    );


    function getSelectedClients() {
        return clientCheckboxes.filter(
            checkbox => checkbox.checked
        );
    }


    function getSelectedGroups() {
        return groupCheckboxes.filter(
            checkbox => checkbox.checked
        );
    }


    function updateState() {
        const selectedClients = getSelectedClients();
        const selectedGroups = getSelectedGroups();

        if (selectedCount) {
            selectedCount.textContent =
                `${selectedClients.length} istemci seçildi`;
        }

        if (assignButton) {
            assignButton.disabled =
                selectedClients.length === 0;
        }

        if (saveButton) {
            saveButton.disabled =
                selectedClients.length === 0 ||
                selectedGroups.length === 0;
        }

        if (selectAll) {
            selectAll.checked =
                clientCheckboxes.length > 0 &&
                selectedClients.length === clientCheckboxes.length;

            selectAll.indeterminate =
                selectedClients.length > 0 &&
                selectedClients.length < clientCheckboxes.length;
        }
    }


    if (selectAll) {
        selectAll.addEventListener(
            "change",
            function () {

                clientCheckboxes.forEach(
                    checkbox => {
                        checkbox.checked =
                            selectAll.checked;
                    }
                );

                updateState();
            }
        );
    }


    clientCheckboxes.forEach(
        checkbox => {
            checkbox.addEventListener(
                "change",
                updateState
            );
        }
    );


    groupCheckboxes.forEach(
        checkbox => {
            checkbox.addEventListener(
                "change",
                updateState
            );
        }
    );


    if (assignButton && groupPanel) {
        assignButton.addEventListener(
            "click",
            function () {
                groupPanel.classList.remove(
                    "d-none"
                );
            }
        );
    }


    if (cancelButton && groupPanel) {
        cancelButton.addEventListener(
            "click",
            function () {

                groupCheckboxes.forEach(
                    checkbox => {
                        checkbox.checked = false;
                    }
                );

                groupPanel.classList.add(
                    "d-none"
                );

                updateState();
            }
        );
    }


    form.addEventListener(
        "submit",
        function (event) {

            if (getSelectedClients().length === 0) {
                event.preventDefault();

                alert(
                    "En az bir istemci seçmelisiniz."
                );

                return;
            }

            if (getSelectedGroups().length === 0) {
                event.preventDefault();

                alert(
                    "En az bir grup seçmelisiniz."
                );
            }
        }
    );


    updateState();
});