document.addEventListener(
    "DOMContentLoaded",
    function () {
        const autoRefreshMarker =
            document.getElementById(
                "nmapScanAutoRefresh"
            );

        if (!autoRefreshMarker) {
            return;
        }

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
                    window.location.reload();
                }
            },
            refreshInterval
        );
    }
);