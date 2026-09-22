document.addEventListener(
    "DOMContentLoaded",
    function () {
        const form = document.getElementById(
            "scriptForm"
        );

        if (!form) {
            return;
        }

        const scriptContent = document.getElementById(
            "script_content"
        );

        const characterCount = document.getElementById(
            "scriptCharacterCount"
        );

        const clientCheckboxes = Array.from(
            document.querySelectorAll(
                ".client-checkbox"
            )
        );

        const groupCheckboxes = Array.from(
            document.querySelectorAll(
                ".group-checkbox"
            )
        );

        const selectAllOnline = document.getElementById(
            "select_all_online"
        );

        const selectedClientCount = document.getElementById(
            "selectedClientCount"
        );

        const selectedGroupCount = document.getElementById(
            "selectedGroupCount"
        );

        const selectedTargetSummary = document.getElementById(
            "selectedTargetSummary"
        );

        const submitButton = form.querySelector(
            "button[type='submit']"
        );


        function getSelectedClients() {
            return clientCheckboxes.filter(
                function (checkbox) {
                    return (
                        checkbox.checked
                        && !checkbox.disabled
                    );
                }
            );
        }


        function getSelectedGroups() {
            return groupCheckboxes.filter(
                function (checkbox) {
                    return checkbox.checked;
                }
            );
        }


        function updateCharacterCount() {
            if (!scriptContent || !characterCount) {
                return;
            }

            const length = scriptContent.value.length;

            characterCount.textContent =
                length + " karakter";
        }


        function updateTargetState() {
            const clientTotal =
                getSelectedClients().length;

            const groupTotal =
                getSelectedGroups().length;

            const allOnlineSelected =
                selectAllOnline
                && selectAllOnline.checked;

            if (selectedClientCount) {
                selectedClientCount.textContent =
                    clientTotal
                    + " istemci seçildi";
            }

            if (selectedGroupCount) {
                selectedGroupCount.textContent =
                    groupTotal
                    + " grup seçildi";
            }

            if (!selectedTargetSummary) {
                return;
            }

            const summaryParts = [];

            if (clientTotal > 0) {
                summaryParts.push(
                    clientTotal + " istemci"
                );
            }

            if (groupTotal > 0) {
                summaryParts.push(
                    groupTotal + " grup"
                );
            }

            if (allOnlineSelected) {
                summaryParts.push(
                    "tüm çevrimiçi istemciler"
                );
            }

            if (summaryParts.length === 0) {
                selectedTargetSummary.textContent =
                    "Henüz hedef seçilmedi";

                selectedTargetSummary.classList.remove(
                    "has-target"
                );

                return;
            }

            selectedTargetSummary.textContent =
                summaryParts.join(", ");

            selectedTargetSummary.classList.add(
                "has-target"
            );
        }


        if (scriptContent) {
            scriptContent.addEventListener(
                "input",
                updateCharacterCount
            );
        }

        clientCheckboxes.forEach(
            function (checkbox) {
                checkbox.addEventListener(
                    "change",
                    updateTargetState
                );
            }
        );

        groupCheckboxes.forEach(
            function (checkbox) {
                checkbox.addEventListener(
                    "change",
                    updateTargetState
                );
            }
        );

        if (selectAllOnline) {
            selectAllOnline.addEventListener(
                "change",
                updateTargetState
            );
        }


        form.addEventListener(
            "submit",
            function (event) {
                const clientTotal =
                    getSelectedClients().length;

                const groupTotal =
                    getSelectedGroups().length;

                const allOnlineSelected =
                    selectAllOnline
                    && selectAllOnline.checked;

                if (
                    clientTotal === 0
                    && groupTotal === 0
                    && !allOnlineSelected
                ) {
                    event.preventDefault();

                    alert(
                        "En az bir istemci, grup veya "
                        + "tüm çevrimiçi istemciler "
                        + "seçeneğini seçmelisiniz."
                    );

                    return;
                }

                const confirmed = confirm(
                    "Script seçilen hedeflerde "
                    + "çalıştırılacak. "
                    + "Devam etmek istiyor musunuz?"
                );

                if (!confirmed) {
                    event.preventDefault();
                    return;
                }

                if (submitButton) {
                    submitButton.disabled = true;
                    submitButton.textContent =
                        "Kuyruğa Ekleniyor...";
                }
            }
        );


        updateCharacterCount();
        updateTargetState();
    }
);