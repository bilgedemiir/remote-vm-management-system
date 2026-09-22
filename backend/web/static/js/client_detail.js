document.addEventListener(
    "DOMContentLoaded",
    function () {
        const progressBars = document.querySelectorAll(
            ".progress-bar[data-width]"
        );

        const upgradeForms = document.querySelectorAll(
            ".software-upgrade-form"
        );

        progressBars.forEach(
            function (bar) {
                const rawWidth = Number(
                    bar.dataset.width || 0
                );

                const safeWidth = Math.min(
                    100,
                    Math.max(0, rawWidth)
                );

                bar.style.width = safeWidth + "%";
            }
        );

        upgradeForms.forEach(
            function (form) {
                form.addEventListener(
                    "submit",
                    function (event) {
                        const packageName =
                            form.dataset.packageName
                            || "Bu yazılım";

                        const confirmed = confirm(
                            packageName
                            + " güncellenecek. "
                            + "Devam etmek istiyor musunuz?"
                        );

                        if (!confirmed) {
                            event.preventDefault();
                        }
                    }
                );
            }
        );
    }
);