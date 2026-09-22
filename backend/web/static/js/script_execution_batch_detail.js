document.addEventListener(
    "DOMContentLoaded",
    function () {
        const refreshButton = document.getElementById(
            "refreshBatchButton"
        );

        const autoRefreshMarker = document.getElementById(
            "batchAutoRefresh"
        );

        const scrollStorageKey =
            "batchScrollPosition:"
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
                    .refreshInterval || 5000
            );

            const refreshInterval = Math.min(
                60000,
                Math.max(3000, rawInterval)
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