/**
 * Theme Toggle Functionality
 * Handles light/dark mode switches and saves preference in localStorage.
 */
document.addEventListener("DOMContentLoaded", () => {
  const themeToggle = document.getElementById("theme-toggle");
  const themeIcon = document.getElementById("theme-icon");
  const body = document.body;

  // 1. Check saved preference and update toggle icon state
  const savedTheme = localStorage.getItem("theme");
  if (savedTheme === "dark") {
    body.classList.add("dark-theme");
    if (themeIcon) {
      themeIcon.classList.replace("bi-moon", "bi-sun");
    }
  }

  // 2. Add click handler for the toggle button
  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      body.classList.toggle("dark-theme");
      const isDark = body.classList.contains("dark-theme");

      if (isDark) {
        localStorage.setItem("theme", "dark");
        if (themeIcon) {
          themeIcon.classList.replace("bi-moon", "bi-sun");
        }
      } else {
        localStorage.setItem("theme", "light");
        if (themeIcon) {
          themeIcon.classList.replace("bi-sun", "bi-moon");
        }
      }
    });
  }
});
