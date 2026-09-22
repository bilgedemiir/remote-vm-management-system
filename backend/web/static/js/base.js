document.addEventListener(
    "DOMContentLoaded",
    function () {
        const appLayout = document.querySelector(
            ".app-layout"
        );

        const toggleButton = document.getElementById(
            "sidebarToggleButton"
        );

        const closeButton = document.getElementById(
            "sidebarCloseButton"
        );

        const backdrop = document.getElementById(
            "sidebarBackdrop"
        );

        const sidebarLinks = document.querySelectorAll(
            ".sidebar-link"
        );

        if (!appLayout || !toggleButton) {
            return;
        }

        const mobileBreakpoint = window.matchMedia(
            "(max-width: 991.98px)"
        );

        function isMobileScreen() {
            return mobileBreakpoint.matches;
        }

        function openMobileSidebar() {
            appLayout.classList.add(
                "sidebar-open"
            );
        }

        function closeMobileSidebar() {
            appLayout.classList.remove(
                "sidebar-open"
            );
        }

        function toggleDesktopSidebar() {
            appLayout.classList.toggle(
                "sidebar-collapsed"
            );

            const collapsed = appLayout.classList.contains(
                "sidebar-collapsed"
            );

            localStorage.setItem(
                "sidebarCollapsed",
                collapsed ? "true" : "false"
            );
        }

        function restoreSidebarState() {
            if (isMobileScreen()) {
                appLayout.classList.remove(
                    "sidebar-collapsed"
                );

                return;
            }

            const collapsed = localStorage.getItem(
                "sidebarCollapsed"
            );

            appLayout.classList.toggle(
                "sidebar-collapsed",
                collapsed === "true"
            );
        }

        toggleButton.addEventListener(
            "click",
            function () {
                if (isMobileScreen()) {
                    openMobileSidebar();
                    return;
                }

                toggleDesktopSidebar();
            }
        );

        if (closeButton) {
            closeButton.addEventListener(
                "click",
                closeMobileSidebar
            );
        }

        if (backdrop) {
            backdrop.addEventListener(
                "click",
                closeMobileSidebar
            );
        }

        sidebarLinks.forEach(
            function (link) {
                link.addEventListener(
                    "click",
                    function () {
                        if (isMobileScreen()) {
                            closeMobileSidebar();
                        }
                    }
                );
            }
        );

        document.addEventListener(
            "keydown",
            function (event) {
                if (
                    event.key === "Escape"
                    && isMobileScreen()
                ) {
                    closeMobileSidebar();
                }
            }
        );

        mobileBreakpoint.addEventListener(
            "change",
            function () {
                closeMobileSidebar();
                restoreSidebarState();
            }
        );

        restoreSidebarState();
    }
);