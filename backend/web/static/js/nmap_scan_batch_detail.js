document.addEventListener(
    "DOMContentLoaded",
    function () {
        const refreshButton = document.getElementById(
            "refreshNmapBatchButton"
        );

        const autoRefreshElement = document.getElementById(
            "nmapBatchAutoRefresh"
        );

        if (refreshButton) {
            refreshButton.addEventListener(
                "click",
                function () {
                    window.location.reload();
                }
            );
        }

        if (!autoRefreshElement) {
            return;
        }

        const refreshInterval = Number(
            autoRefreshElement.dataset.refreshInterval
        );

        if (
            !Number.isFinite(refreshInterval)
            || refreshInterval < 1000
        ) {
            return;
        }

        function scheduleRefresh() {
            window.setTimeout(
                function () {
                    if (
                        document.visibilityState
                        === "visible"
                    ) {
                        window.location.reload();
                        return;
                    }

                    scheduleRefresh();
                },
                refreshInterval
            );
        }

        scheduleRefresh();
    }
);