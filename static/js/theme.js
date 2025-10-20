(function () {
    const ready = (callback) => {
        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", callback);
        } else {
            callback();
        }
    };

    const THEME_KEY = "zetom-theme";
    const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;

    ready(() => {
        const buttons = Array.from(document.querySelectorAll("[data-theme-toggle]"));
        if (!buttons.length) {
            return;
        }

        const getStoredTheme = () => {
            try {
                return sessionStorage.getItem(THEME_KEY);
            } catch (error) {
                return null;
            }
        };

        const storeTheme = (theme) => {
            try {
                sessionStorage.setItem(THEME_KEY, theme);
            } catch (error) {
                // ignore write errors (e.g. storage disabled)
            }
        };

        const applyTheme = (theme) => {
            document.body.dataset.theme = theme;
            buttons.forEach((button) => {
                const isDark = theme === "dark";
                button.setAttribute("aria-pressed", isDark ? "true" : "false");
                button.classList.toggle("is-dark", isDark);
                const label = button.querySelector("[data-theme-toggle-label]");
                if (label) {
                    const light = label.getAttribute("data-light-label") || "Light";
                    const dark = label.getAttribute("data-dark-label") || "Dark";
                    label.textContent = isDark ? dark : light;
                }
            });
        };

        const initialTheme = (() => {
            const stored = getStoredTheme();
            if (stored === "dark" || stored === "light") {
                return stored;
            }
            const preset = document.body && document.body.dataset ? document.body.dataset.theme : null;
            if (preset === "dark" || preset === "light") {
                return preset;
            }
            return prefersDark ? "dark" : "light";
        })();

        applyTheme(initialTheme);

        buttons.forEach((button) => {
            button.addEventListener("click", () => {
                const nextTheme = document.body.dataset.theme === "dark" ? "light" : "dark";
                applyTheme(nextTheme);
                storeTheme(nextTheme);
            });
        });

        if (window.matchMedia) {
            const media = window.matchMedia("(prefers-color-scheme: dark)");
            const handleChange = (event) => {
                const stored = getStoredTheme();
                if (stored !== "dark" && stored !== "light") {
                    const theme = event.matches ? "dark" : "light";
                    applyTheme(theme);
                }
            };
            if (typeof media.addEventListener === "function") {
                media.addEventListener("change", handleChange);
            } else if (typeof media.addListener === "function") {
                media.addListener(handleChange);
            }
        }
    });
})();
