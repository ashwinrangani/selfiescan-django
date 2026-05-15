document.addEventListener("DOMContentLoaded", () => {
    const themeToggle = document.getElementById("theme-toggle");
    const htmlElement = document.documentElement;

    // SVG Icons
    const lightIcon = themeToggle.querySelector(".block");
    const darkIcon = themeToggle.querySelector(".hidden");

    const currentTheme = localStorage.getItem("theme") || "gourmet";

    // Apply the saved theme on page load
    htmlElement.setAttribute("data-theme", currentTheme);
    toggleIcons(currentTheme);

    // Toggle the theme on button click
    themeToggle.addEventListener("click", () => {
        const isDark = htmlElement.getAttribute("data-theme") === "luxury";
        const newTheme = isDark ? "gourmet" : "luxury";

        htmlElement.setAttribute("data-theme", newTheme);
        localStorage.setItem("theme", newTheme);
        toggleIcons(newTheme, true);;
    });

    function toggleIcons(theme, animate = false) {
        const incoming = theme === "luxury" ? darkIcon : lightIcon;
        const outgoing = theme === "luxury" ? lightIcon : darkIcon;

        outgoing.classList.add("hidden");
        outgoing.classList.remove("icon-animate");

        incoming.classList.remove("hidden");

        if (animate) {
            incoming.classList.remove("icon-animate");
            // Force reflow so the animation restarts cleanly every click
            void incoming.offsetWidth;
            incoming.classList.add("icon-animate");
        }
    }
});
