document.addEventListener(
    "DOMContentLoaded",
    function () {
        const refreshButton = document.getElementById(
            "refreshExecutionButton"
        );

        const autoRefreshMarker = document.getElementById(
            "executionAutoRefresh"
        );

        const scrollStorageKey =
            "executionScrollPosition:"
            + window.location.pathname;


        function restoreScrollPosition() {
            const savedPosition = sessionStorage.getItem(
                scrollStorageKey
            );

            if (savedPosition === null) {
                return;
            }

            sessionStorage.removeItem(
                scrollStorageKey
            );

            window.scrollTo(
                0,
                Number(savedPosition) || 0
            );
        }


        function refreshPage() {
            sessionStorage.setItem(
                scrollStorageKey,
                String(window.scrollY)
            );

            window.location.reload();
        }


        if (refreshButton) {
            refreshButton.addEventListener(
                "click",
                function () {
                    refreshButton.disabled = true;
                    refreshButton.textContent =
                        "Yenileniyor...";

                    refreshPage();
                }
            );
        }


        if (autoRefreshMarker) {
            const rawInterval = Number(
                autoRefreshMarker.dataset
                    .refreshInterval || 3000
            );

            const refreshInterval = Math.min(
                60000,
                Math.max(2000, rawInterval)
            );

            window.setInterval(
                function () {
                    if (
                        document.visibilityState
                        === "visible"
                    ) {
                        refreshPage();
                    }
                },
                refreshInterval
            );
        }


        restoreScrollPosition();
    }
);